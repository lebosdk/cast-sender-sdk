#!/usr/bin/env python3
"""获取乐播 iOS 发端 SDK，放到 <工程目录>/LeboSenderSDK/：
  LBLelinkKit.xcframework（推送）；包里有 Extension/ 时另装 Mirror/App、Mirror/Extension（镜像）。

用法：
  python3 -I obtain_sdk.py --project-dir <工程目录> --check      只读：报告已装版本
  python3 -I obtain_sdk.py --project-dir <工程目录>              从官方 CDN 下载安装
  python3 -I obtain_sdk.py --project-dir <工程目录> --local <zip 或 xcframework>   用指定的本地包安装
内容与已装的一致就不动，不一致整体替换。
注意：只校验 zip 完整、xcframework 分片齐全（CDN 另校验 HTTPS），并打印 SHA-256 留档。
"""
import argparse
import hashlib
import plistlib
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

CDN_URL = "https://lebotob.hpplay.cn/sdk/iOS/Release/ios-sender-sdk.zip"
FRAMEWORK = "LBLelinkKit.xcframework"
INSTALL_DIR = "LeboSenderSDK"
# 必须同时有真机和模拟器分片
REQUIRED_SLICES = {("ios", None), ("ios", "simulator")}
# 镜像需要的 framework，按 target 分放；录屏扩展另外链接 LBLelinkKit.xcframework
MIRROR_DIR = "Mirror"
MIRROR_FRAMEWORKS = {
    "App": ["LBReplayAppKit", "NERtcSDK", "TXLiteAVSDK_TRTC", "TXFFmpeg", "TXSoundTouch"],
    "Extension": ["LBReplayKitExtension", "LBReplayKit", "LBSREncoder", "NERtcReplayKit", "TXLiteAVSDK_ReplayKitExt"],
}


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_tree(root):
    """目录内容指纹：按相对路径排序后对路径和内容一起取哈希"""
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(_sha256_file(p).encode())
    return h.hexdigest()


def _check_xcframework(path):
    """校验 xcframework 结构，返回 SDK 版本号；不合格抛 ValueError"""
    info_path = path / "Info.plist"
    if not info_path.is_file():
        raise ValueError(FRAMEWORK + " 缺少 Info.plist")
    with open(info_path, "rb") as f:
        info = plistlib.load(f)
    slices = {(lib.get("SupportedPlatform"), lib.get("SupportedPlatformVariant")) for lib in info.get("AvailableLibraries", [])}
    if not REQUIRED_SLICES <= slices:
        raise ValueError(FRAMEWORK + " 缺少真机或模拟器分片")
    version = None
    for lib in info["AvailableLibraries"]:
        fw = path / lib["LibraryIdentifier"] / lib["LibraryPath"]
        if not (fw / "LBLelinkKit").is_file() or not (fw / "Headers" / "LBLelinkKit.h").is_file():
            raise ValueError(lib["LibraryIdentifier"] + " 分片缺少二进制或头文件")
        with open(fw / "Info.plist", "rb") as f:
            version = plistlib.load(f).get("CFBundleShortVersionString", version)
    return version


def _stage_mirror(root, dest):
    """包里有 Extension/ 时校验镜像 framework 并拷到 dest/Mirror；没有返回 False"""
    if root is None or not (root / "Extension").is_dir():
        return False
    for part, names in MIRROR_FRAMEWORKS.items():
        for name in names:
            src = root / part / (name + ".framework")
            if not (src / name).is_file():
                raise ValueError("镜像包缺少 " + part + "/" + name + ".framework")
            shutil.copytree(src, dest / MIRROR_DIR / part / src.name, symlinks=True)
    return True


def _tree_hash(base, names):
    """多个子路径合在一起的内容指纹；不存在的子路径记为空"""
    return "".join((_sha256_tree(base / n) if (base / n).exists() else "-") for n in names)


def _installed_version(target):
    try:
        return _check_xcframework(target)
    except (ValueError, OSError):
        return None


def _download(url, dest):
    if not url.startswith("https://"):
        raise ValueError("只允许 HTTPS 地址")
    with urllib.request.urlopen(url, timeout=30) as resp:
        if not resp.geturl().startswith("https://"):
            raise ValueError("重定向到了非 HTTPS 地址")
        with open(dest, "wb") as f:
            shutil.copyfileobj(resp, f)


def _extract(zip_path, workdir):
    """解压并找到 xcframework（兼容 App/ 子目录与根目录两种布局）"""
    with zipfile.ZipFile(zip_path) as z:
        bad = z.testzip()
        if bad:
            raise ValueError("zip 损坏：" + bad)
        for name in z.namelist():
            if name.startswith("/") or ".." in Path(name).parts:
                raise ValueError("zip 内含非法路径：" + name)
        z.extractall(workdir)
    found = [p for p in workdir.rglob(FRAMEWORK) if p.is_dir() and "__MACOSX" not in p.parts]
    if not found:
        raise ValueError("zip 里没有 " + FRAMEWORK)
    # 包根目录：xcframework 在 App/ 下时取它的上两级
    root = found[0].parent.parent if found[0].parent.name == "App" else found[0].parent
    return found[0], root


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", required=True)
    parser.add_argument("--check", action="store_true", help="只读检查")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--local", help="指定本地 zip 或 xcframework，代替 CDN 下载")
    source.add_argument("--cdn", action="store_true", help="从官方 CDN 下载（默认即如此，保留兼容旧用法）")
    parser.add_argument("--url", default=CDN_URL, help="下载地址，默认官方 CDN")
    args = parser.parse_args()

    install_dir = Path(args.project_dir).expanduser().resolve() / INSTALL_DIR
    target = install_dir / FRAMEWORK
    if args.check:
        version = _installed_version(target)
        print("已安装 SDK：" + (version + "  " + str(target) if version else "无"))
        print("镜像 framework：" + ("已安装" if (install_dir / MIRROR_DIR / "Extension").is_dir() else "无"))
        return 0

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        try:
            root = None
            if args.local:
                src = Path(args.local).expanduser().resolve()
                if src.is_dir():
                    candidate = src
                    print("本地包：" + str(src))
                else:
                    print("本地包：" + str(src) + "  SHA-256: " + _sha256_file(src))
                    candidate, root = _extract(src, tmp / "x")
            else:
                zip_path = tmp / "sdk.zip"
                print("下载：" + args.url)
                _download(args.url, zip_path)
                print("SHA-256: " + _sha256_file(zip_path))
                candidate, root = _extract(zip_path, tmp / "x")
            version = _check_xcframework(candidate)
            # 按安装后的目录结构先在临时目录摆好，整体比较、整体替换
            stage = tmp / "stage"
            shutil.copytree(candidate, stage / FRAMEWORK, symlinks=True)
            has_mirror = _stage_mirror(root, stage)
        except Exception as e:  # 网络、zip、结构错误统一报给开发者
            print("获取 SDK 失败：" + str(e))
            return 1

        managed = [FRAMEWORK, MIRROR_DIR]
        if _tree_hash(install_dir, managed) == _tree_hash(stage, managed):
            print("已是同一版本，未改动：" + str(version))
            return 0
        install_dir.mkdir(parents=True, exist_ok=True)
        for name in managed:
            if (install_dir / name).exists():
                shutil.rmtree(install_dir / name)
            if (stage / name).exists():
                shutil.copytree(stage / name, install_dir / name, symlinks=True)
        print("已安装 SDK " + str(version) + " 到 " + str(install_dir) + ("（含镜像）" if has_mirror else "（仅推送）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
