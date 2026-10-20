#!/usr/bin/env python3
"""检查接入 iOS 发端 SDK 所需的本机环境与目标工程，只读，不安装任何东西。

用法：python3 -I check_env.py --project-dir <工程目录>
退出码：0 全部通过；1 有缺失项（按提示让开发者自行安装）。
"""
import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path


def _run(cmd):
    """执行命令，返回 (退出码, 标准输出)；命令不存在返回 (127, "")"""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return p.returncode, p.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 127, ""


def _list_targets(xcodeproj):
    """用 xcodeproj 列出工程里的 iOS App target 及 Bundle ID"""
    script = (
        'require "xcodeproj"; require "json"; p = Xcodeproj::Project.open(ARGV[0]); '
        'puts JSON.generate(p.native_targets.select { |t| t.product_type == "com.apple.product-type.application" }'
        '.map { |t| { name: t.name, bundle_id: t.build_configurations.map { |c| c.build_settings["PRODUCT_BUNDLE_IDENTIFIER"] }.compact.uniq } })'
    )
    code, out = _run(["ruby", "-e", script, str(xcodeproj)])
    return json.loads(out) if code == 0 and out else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", required=True)
    args = parser.parse_args()
    problems = []

    if platform.system() != "Darwin":
        problems.append("需要在 macOS 上运行")

    code, out = _run(["xcodebuild", "-version"])
    if code != 0:
        problems.append("未找到完整 Xcode：请从 App Store 安装 Xcode，并执行 sudo xcode-select -s /Applications/Xcode.app")
    else:
        print("Xcode: " + out.splitlines()[0])

    code, _ = _run(["ruby", "-e", 'require "xcodeproj"'])
    if code != 0:
        problems.append("缺少 xcodeproj（Ruby 库）：执行 sudo gem install xcodeproj，或安装 CocoaPods（sudo gem install cocoapods）")
    else:
        print("xcodeproj: OK")

    project_dir = Path(args.project_dir).expanduser().resolve()
    projects = [p for p in project_dir.glob("*.xcodeproj") if p.name != "Pods.xcodeproj"]
    if not projects:
        problems.append("在 " + str(project_dir) + " 下没有找到 .xcodeproj：本 Skill 只支持接入已有工程")
    for xcodeproj in projects:
        targets = _list_targets(xcodeproj)
        if targets is None:
            print("工程 " + xcodeproj.name + "：无法读取 target")
            continue
        print("工程 " + xcodeproj.name + " 的 App target：")
        for t in targets:
            print("  - " + t["name"] + "  Bundle ID: " + ", ".join(t["bundle_id"] or ["(未设置)"]))
        if not targets:
            problems.append(xcodeproj.name + " 里没有 iOS App target")

    if problems:
        print("\n缺失项：")
        for p in problems:
            print("  - " + p)
        return 1
    print("\n环境检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
