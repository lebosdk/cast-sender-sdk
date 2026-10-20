#!/usr/bin/env python3
"""Detect and prepare the Android build environment for a host project."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
from typing import Dict, Iterable, List, NamedTuple, Optional, Sequence, Tuple
from urllib import error as urlerror
from urllib import request
import xml.etree.ElementTree as ET
import zipfile


ANDROID_REPOSITORY = "https://dl.google.com/android/repository/repository2-1.xml"
ANDROID_DOWNLOAD_ROOT = "https://dl.google.com/android/repository/"
ADOPTIUM_API = "https://api.adoptium.net/v3/assets/latest/{major}/hotspot"
GRADLE_DOWNLOAD_ROOT = "https://services.gradle.org/distributions/"
SKIP_DIRS = {".git", ".gradle", ".idea", "build", "out", "node_modules"}


class SetupError(Exception):
    pass


class Requirements(NamedTuple):
    agp_version: Optional[str]
    gradle_version: Optional[str]
    java_major: int
    compile_sdk: Optional[int]
    build_tools: Optional[str]


class JavaRuntime(NamedTuple):
    home: Path
    major: int


def state_directory() -> Path:
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "hpplay-skill"
    root = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return root / "hpplay-skill"


def cache_directory() -> Path:
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        return Path(os.environ["LOCALAPPDATA"]) / "hpplay-skill" / "cache"
    root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return root / "hpplay-skill"


def version_tuple(value: Optional[str]) -> Tuple[int, ...]:
    if not value:
        return ()
    match = re.search(r"\d+(?:\.\d+)*", value)
    return tuple(int(part) for part in match.group(0).split(".")) if match else ()


def iter_project_files(project_dir: Path) -> Iterable[Path]:
    names = {
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle",
        "settings.gradle.kts",
        "gradle.properties",
        "libs.versions.toml",
        "gradle-wrapper.properties",
    }
    for root, directories, files in os.walk(str(project_dir)):
        directories[:] = [item for item in directories if item not in SKIP_DIRS]
        for name in files:
            if name in names:
                yield Path(root) / name


def read_project_text(project_dir: Path) -> str:
    chunks = []
    for path in iter_project_files(project_dir):
        try:
            if path.stat().st_size <= 2 * 1024 * 1024:
                chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n".join(chunks)


def first_match(patterns: Sequence[str], text: str) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, re.MULTILINE)
        if match:
            return match.group(1)
    return None


def required_java_major(agp_version: Optional[str], gradle_version: Optional[str]) -> int:
    agp = version_tuple(agp_version)
    if agp and agp[0] >= 8:
        return 17
    if agp and agp[0] >= 7:
        return 11
    gradle = version_tuple(gradle_version)
    if gradle and gradle[0] >= 9:
        return 17
    if gradle and gradle >= (6, 7):
        return 11
    return 8


def inspect_project(
    project_dir: Path,
    compile_sdk_override: Optional[int],
    build_tools_override: Optional[str],
    gradle_override: Optional[str],
) -> Requirements:
    text = read_project_text(project_dir)
    wrapper = project_dir / "gradle" / "wrapper" / "gradle-wrapper.properties"
    wrapper_text = ""
    if wrapper.exists():
        wrapper_text = wrapper.read_text(encoding="utf-8", errors="replace")

    agp_version = first_match(
        (
            r"com\.android\.tools\.build:gradle:([0-9][0-9A-Za-z.+_-]*)",
            r"(?:id\s*\(?\s*[\"']com\.android\.(?:application|library)[\"']\s*\)?|com\.android\.(?:application|library))\s+version\s+[\"']([0-9][0-9A-Za-z.+_-]*)[\"']",
            r"(?m)^\s*agp\s*=\s*[\"']([0-9][0-9A-Za-z.+_-]*)[\"']",
        ),
        text,
    )
    detected_gradle_version = first_match(
        (r"distributionUrl=.*gradle-([0-9][0-9A-Za-z.+_-]*)-(?:bin|all)\.zip",),
        wrapper_text,
    )
    gradle_version = detected_gradle_version or gradle_override
    compile_sdk_text = first_match(
        (
            r"\bcompileSdk(?:Version)?\s*(?:=|\s)\s*[\"']?(\d+)",
            r"\bcompileVersion\s*:\s*[\"']?(\d+)",
            r"(?m)^\s*compileSdk\s*=\s*[\"'](\d+)[\"']",
        ),
        text,
    )
    build_tools = build_tools_override or first_match(
        (
            r"\bbuildToolsVersion\s*(?:=|\s|:)\s*[\"']([0-9]+(?:\.[0-9]+){1,2})[\"']",
            r"(?m)^\s*buildTools\s*=\s*[\"']([0-9]+(?:\.[0-9]+){1,2})[\"']",
        ),
        text,
    )
    compile_sdk = compile_sdk_override or (int(compile_sdk_text) if compile_sdk_text else None)
    return Requirements(
        agp_version=agp_version,
        gradle_version=gradle_version,
        java_major=required_java_major(agp_version, gradle_version),
        compile_sdk=compile_sdk,
        build_tools=build_tools,
    )


def run(
    command: Sequence[str],
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[Path] = None,
    input_text: Optional[str] = None,
    check: bool = False,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(command),
        cwd=str(cwd) if cwd else None,
        env=env,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=check,
    )


def java_major(java_binary: Path) -> Optional[int]:
    try:
        result = run([str(java_binary), "-version"])
    except OSError:
        return None
    match = re.search(r'version\s+"(?:1\.)?(\d+)', result.stdout)
    return int(match.group(1)) if result.returncode == 0 and match else None


def java_home_from_binary(java_binary: Path) -> Optional[Path]:
    try:
        result = run([str(java_binary), "-XshowSettings:properties", "-version"])
    except OSError:
        return None
    match = re.search(r"^\s*java\.home\s*=\s*(.+?)\s*$", result.stdout, re.MULTILINE)
    if not match:
        return None
    home = Path(match.group(1)).expanduser().resolve()
    return home if (home / "bin" / ("java.exe" if os.name == "nt" else "java")).exists() else None


def java_candidates(required_major: int) -> List[Path]:
    values = []
    if os.environ.get("JAVA_HOME"):
        values.append(Path(os.environ["JAVA_HOME"]))
    current = shutil.which("java")
    if current:
        resolved = java_home_from_binary(Path(current))
        if resolved:
            values.append(resolved)
    if sys.platform == "darwin":
        helper = Path("/usr/libexec/java_home")
        if helper.exists():
            requested_version = "1.8" if required_major == 8 else str(required_major)
            result = run([str(helper), "-v", requested_version])
            if result.returncode == 0 and result.stdout.strip():
                values.append(Path(result.stdout.strip()))
        values.extend(Path("/Library/Java/JavaVirtualMachines").glob("*/Contents/Home"))
        values.append(Path("/Applications/Android Studio.app/Contents/jbr/Contents/Home"))
    elif os.name == "nt":
        for variable in ("ProgramFiles", "LOCALAPPDATA"):
            if os.environ.get(variable):
                values.append(Path(os.environ[variable]) / "Android" / "Android Studio" / "jbr")
    else:
        values.extend(Path("/usr/lib/jvm").glob("*"))
        values.extend(
            (
                Path("/opt/android-studio/jbr"),
                Path.home() / "android-studio" / "jbr",
            )
        )
    managed = cache_directory() / "jdks" / ("temurin-" + str(required_major))
    values.append(managed)
    unique = []
    seen = set()
    for value in values:
        key = str(value.expanduser())
        if key not in seen:
            seen.add(key)
            unique.append(value.expanduser())
    return unique


def max_java_major(gradle_version: Optional[str]) -> Optional[int]:
    version = version_tuple(gradle_version)
    if not version:
        return None
    if version < (5, 0):
        return 8
    if version < (6, 7):
        return 11
    if version < (7, 3):
        return 16
    if version < (8, 0):
        return 18
    if version < (8, 5):
        return 20
    return None


def find_java(requirements: Requirements) -> Optional[JavaRuntime]:
    maximum = max_java_major(requirements.gradle_version)
    runtimes = []
    java_name = "java.exe" if os.name == "nt" else "java"
    for home in java_candidates(requirements.java_major):
        binary = home / "bin" / java_name
        compiler = home / "bin" / ("javac.exe" if os.name == "nt" else "javac")
        if not compiler.exists():
            continue
        major = java_major(binary)
        if major is None or major < requirements.java_major:
            continue
        if maximum is not None and major > maximum:
            continue
        runtimes.append(JavaRuntime(home.resolve(), major))
    if not runtimes:
        return None
    return sorted(runtimes, key=lambda item: (item.major != requirements.java_major, item.major))[0]


def platform_values() -> Tuple[str, str]:
    system = platform.system().lower()
    machine = platform.machine().lower()
    os_name = {"darwin": "mac", "linux": "linux", "windows": "windows"}.get(system)
    architecture = {
        "x86_64": "x64",
        "amd64": "x64",
        "aarch64": "aarch64",
        "arm64": "aarch64",
    }.get(machine)
    if not os_name or not architecture:
        raise SetupError("Unsupported host platform: " + system + "/" + machine)
    return os_name, architecture


def download(url: str, destination: Path) -> None:
    print("Downloading " + url, file=sys.stderr)
    http_request = request.Request(url, headers={"User-Agent": "cast-sender-sdk-skill"})
    try:
        with request.urlopen(http_request, timeout=60) as response, destination.open("wb") as output:
            shutil.copyfileobj(response, output)
    except (OSError, TimeoutError, urlerror.URLError) as exc:
        raise SetupError(
            "Download failed for "
            + url
            + ". Check HTTP_PROXY/HTTPS_PROXY or use an existing local cache. Cause: "
            + str(exc)
        ) from exc


def digest(path: Path, algorithm: str) -> str:
    value = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def safe_extract_zip(archive: Path, destination: Path) -> None:
    root = destination.resolve()
    with zipfile.ZipFile(str(archive)) as handle:
        for member in handle.infolist():
            target = (destination / member.filename).resolve()
            if root != target and root not in target.parents:
                raise SetupError("Archive contains an unsafe path: " + member.filename)
        handle.extractall(str(destination))


def safe_extract_tar(archive: Path, destination: Path) -> None:
    root = destination.resolve()
    with tarfile.open(str(archive), "r:gz") as handle:
        for member in handle.getmembers():
            target = (destination / member.name).resolve()
            if root != target and root not in target.parents:
                raise SetupError("Archive contains an unsafe path: " + member.name)
            if member.issym() or member.islnk():
                link_target = (target.parent / member.linkname).resolve()
                if root != link_target and root not in link_target.parents:
                    raise SetupError("Archive contains an unsafe link: " + member.name)
        handle.extractall(str(destination))


def install_jdk(required_major: int) -> JavaRuntime:
    os_name, architecture = platform_values()
    api_os = "mac" if os_name == "mac" else os_name
    url = ADOPTIUM_API.format(major=required_major)
    url += "?architecture={}&image_type=jdk&os={}&vendor=eclipse".format(architecture, api_os)
    print("Resolving Temurin JDK " + str(required_major), file=sys.stderr)
    http_request = request.Request(url, headers={"User-Agent": "cast-sender-sdk-skill"})
    with request.urlopen(http_request, timeout=30) as response:
        assets = json.loads(response.read().decode("utf-8"))
    if not isinstance(assets, list) or not assets:
        raise SetupError("No Temurin JDK download was found for this platform")
    package = assets[0].get("binary", {}).get("package", {})
    link = package.get("link")
    checksum = package.get("checksum")
    if not link or not checksum:
        raise SetupError("The Temurin API response did not include a verified package")

    target = cache_directory() / "jdks" / ("temurin-" + str(required_major))
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hpplay-jdk-") as temporary:
        temporary_dir = Path(temporary)
        suffix = ".zip" if str(link).lower().endswith(".zip") else ".tar.gz"
        archive = temporary_dir / ("jdk" + suffix)
        extracted = temporary_dir / "extracted"
        extracted.mkdir()
        download(str(link), archive)
        if digest(archive, "sha256").lower() != str(checksum).lower():
            raise SetupError("Temurin JDK checksum verification failed")
        if suffix == ".zip":
            safe_extract_zip(archive, extracted)
        else:
            safe_extract_tar(archive, extracted)
        java_name = "java.exe" if os.name == "nt" else "java"
        binaries = list(extracted.rglob("bin/" + java_name))
        if not binaries:
            raise SetupError("The downloaded JDK does not contain bin/java")
        source_home = binaries[0].parent.parent
        staged = target.parent / (target.name + ".tmp")
        if staged.exists():
            shutil.rmtree(str(staged))
        shutil.copytree(str(source_home), str(staged), symlinks=True)
        if target.exists():
            shutil.rmtree(str(target))
        staged.replace(target)
    runtime = JavaRuntime(target, required_major)
    actual = java_major(runtime.home / "bin" / ("java.exe" if os.name == "nt" else "java"))
    if actual != required_major:
        raise SetupError("Installed JDK could not be verified")
    return runtime


def properties(path: Path) -> Dict[str, str]:
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "=" not in line or line.lstrip().startswith(("#", "!")):
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().replace("\\:", ":").replace("\\\\", "\\")
    return values


def android_sdk_candidates(project_dir: Path) -> List[Path]:
    values = []
    local_sdk = properties(project_dir / "local.properties").get("sdk.dir")
    if local_sdk:
        values.append(Path(local_sdk))
    for variable in ("ANDROID_SDK_ROOT", "ANDROID_HOME"):
        if os.environ.get(variable):
            values.append(Path(os.environ[variable]))
    if sys.platform == "darwin":
        values.append(Path.home() / "Library" / "Android" / "sdk")
    elif os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        values.append(Path(os.environ["LOCALAPPDATA"]) / "Android" / "Sdk")
    else:
        values.extend((Path.home() / "Android" / "Sdk", Path.home() / "Android" / "sdk"))
    values.append(cache_directory() / "android-sdk")
    unique = []
    seen = set()
    for value in values:
        key = str(value.expanduser())
        if key not in seen:
            seen.add(key)
            unique.append(value.expanduser())
    return unique


def sdk_has_required_packages(sdk_root: Path, requirements: Requirements) -> bool:
    adb_name = "adb.exe" if os.name == "nt" else "adb"
    if not (sdk_root / "platform-tools" / adb_name).exists():
        return False
    if requirements.compile_sdk and not (
        sdk_root / "platforms" / ("android-" + str(requirements.compile_sdk))
    ).is_dir():
        return False
    if requirements.build_tools and not (sdk_root / "build-tools" / requirements.build_tools).is_dir():
        return False
    return True


def find_android_sdk(project_dir: Path, requirements: Requirements) -> Optional[Path]:
    for candidate in android_sdk_candidates(project_dir):
        if candidate.is_dir() and sdk_has_required_packages(candidate, requirements):
            return candidate.resolve()
    return None


def find_sdkmanager(sdk_root: Path) -> Optional[Path]:
    executable = "sdkmanager.bat" if os.name == "nt" else "sdkmanager"
    candidates = list((sdk_root / "cmdline-tools").glob("*/bin/" + executable))
    candidates.append(sdk_root / "tools" / "bin" / executable)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def resolve_command_line_tools() -> Tuple[str, str]:
    host_os = {"darwin": "macosx", "linux": "linux", "win32": "windows"}.get(sys.platform)
    if not host_os:
        raise SetupError("Android command-line tools are unsupported on " + sys.platform)
    http_request = request.Request(
        ANDROID_REPOSITORY,
        headers={"User-Agent": "cast-sender-sdk-skill"},
    )
    with request.urlopen(http_request, timeout=30) as response:
        root = ET.fromstring(response.read())
    for package in root.iter():
        if local_name(package.tag) != "remotePackage":
            continue
        if package.attrib.get("path") != "cmdline-tools;latest":
            continue
        for archive in package.iter():
            if local_name(archive.tag) != "archive":
                continue
            archive_os = next(
                (item.text for item in archive if local_name(item.tag) == "host-os"),
                None,
            )
            if archive_os != host_os:
                continue
            url = next((item.text for item in archive.iter() if local_name(item.tag) == "url"), None)
            checksum = next(
                (item.text for item in archive.iter() if local_name(item.tag) == "checksum"),
                None,
            )
            if url and checksum:
                return ANDROID_DOWNLOAD_ROOT + url, checksum
    raise SetupError("Could not resolve Android SDK command-line tools")


def install_command_line_tools(sdk_root: Path) -> Path:
    url, checksum = resolve_command_line_tools()
    target = sdk_root / "cmdline-tools" / "hpplay-skill"
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="hpplay-android-tools-") as temporary:
        temporary_dir = Path(temporary)
        archive = temporary_dir / "command-line-tools.zip"
        extracted = temporary_dir / "extracted"
        extracted.mkdir()
        download(url, archive)
        algorithm = "sha1" if len(checksum) == 40 else "sha256"
        if digest(archive, algorithm).lower() != checksum.lower():
            raise SetupError("Android command-line tools checksum verification failed")
        safe_extract_zip(archive, extracted)
        source = extracted / "cmdline-tools"
        if not source.is_dir():
            raise SetupError("Unexpected Android command-line tools archive layout")
        staged = target.parent / (target.name + ".tmp")
        if staged.exists():
            shutil.rmtree(str(staged))
        shutil.copytree(str(source), str(staged), symlinks=True)
        if target.exists():
            shutil.rmtree(str(target))
        staged.replace(target)
    if os.name != "nt":
        for executable in (target / "bin").iterdir():
            if executable.is_file():
                executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    manager = find_sdkmanager(sdk_root)
    if manager is None:
        raise SetupError("Installed Android command-line tools could not be verified")
    return manager


def build_environment(java: JavaRuntime, sdk_root: Path) -> Dict[str, str]:
    environment = os.environ.copy()
    environment["JAVA_HOME"] = str(java.home)
    environment["ANDROID_SDK_ROOT"] = str(sdk_root)
    environment["ANDROID_HOME"] = str(sdk_root)
    path_entries = [str(java.home / "bin"), str(sdk_root / "platform-tools")]
    environment["PATH"] = os.pathsep.join(path_entries + [environment.get("PATH", "")])
    return environment


def ensure_android_sdk(
    project_dir: Path,
    requirements: Requirements,
    java: JavaRuntime,
    accept_licenses: bool,
) -> Path:
    for candidate in android_sdk_candidates(project_dir):
        if candidate.is_dir():
            sdk_root = candidate.resolve()
            break
    else:
        sdk_root = (cache_directory() / "android-sdk").resolve()
        sdk_root.mkdir(parents=True, exist_ok=True)
    if sdk_has_required_packages(sdk_root, requirements):
        return sdk_root

    manager = find_sdkmanager(sdk_root) or install_command_line_tools(sdk_root)
    sdk_java = java
    if sdk_java.major < 17:
        sdk_requirements = Requirements(None, None, 17, None, None)
        sdk_java = find_java(sdk_requirements) or install_jdk(17)
    environment = build_environment(sdk_java, sdk_root)
    if accept_licenses:
        print("Accepting Android SDK licenses after the user answered y", file=sys.stderr)
        result = run(
            [str(manager), "--sdk_root=" + str(sdk_root), "--licenses"],
            env=environment,
            input_text="y\n" * 100,
        )
        if result.returncode != 0:
            raise SetupError("Android SDK license acceptance failed:\n" + result.stdout[-4000:])

    packages = []
    adb_name = "adb.exe" if os.name == "nt" else "adb"
    if not (sdk_root / "platform-tools" / adb_name).exists():
        packages.append("platform-tools")
    if requirements.compile_sdk and not (
        sdk_root / "platforms" / ("android-" + str(requirements.compile_sdk))
    ).is_dir():
        packages.append("platforms;android-" + str(requirements.compile_sdk))
    if requirements.build_tools and not (sdk_root / "build-tools" / requirements.build_tools).is_dir():
        packages.append("build-tools;" + requirements.build_tools)
    if not packages:
        return sdk_root
    print("Installing Android SDK packages: " + ", ".join(packages), file=sys.stderr)
    result = run(
        [str(manager), "--sdk_root=" + str(sdk_root)] + packages,
        env=environment,
        input_text="",
    )
    if result.returncode != 0:
        hint = ""
        if not accept_licenses:
            hint = (
                "\nAndroid licenses may be pending. After the tester reviews them and answers "
                "y to the [y/n] confirmation, rerun with --accept-licenses."
            )
        raise SetupError("Android SDK package installation failed:\n" + result.stdout[-4000:] + hint)
    if not sdk_has_required_packages(sdk_root, requirements):
        raise SetupError("Android SDK packages were installed but verification still failed")
    return sdk_root


GRADLE_FOR_AGP = {
    (4, 2): "6.7.1",
    (7, 0): "7.0.2",
    (7, 1): "7.2",
    (7, 2): "7.3.3",
    (7, 3): "7.4",
    (7, 4): "7.5",
    (8, 0): "8.0",
    (8, 1): "8.0",
    (8, 2): "8.2",
    (8, 3): "8.4",
    (8, 4): "8.6",
    (8, 5): "8.7",
    (8, 6): "8.7",
    (8, 7): "8.9",
    (8, 8): "8.10.2",
    (8, 9): "8.11.1",
    (8, 10): "8.11.1",
    (8, 11): "8.13",
    (8, 12): "8.13",
    (8, 13): "8.13",
}


def gradle_wrapper_command(project_dir: Path) -> Optional[List[str]]:
    properties_file = project_dir / "gradle" / "wrapper" / "gradle-wrapper.properties"
    wrapper_jar = project_dir / "gradle" / "wrapper" / "gradle-wrapper.jar"
    if not properties_file.exists() or not wrapper_jar.exists():
        return None
    if os.name == "nt":
        wrapper = project_dir / "gradlew.bat"
        return [str(wrapper)] if wrapper.exists() else None
    wrapper = project_dir / "gradlew"
    return ["sh", str(wrapper)] if wrapper.exists() else None


def recommended_gradle(requirements: Requirements) -> Optional[str]:
    if requirements.gradle_version:
        return requirements.gradle_version
    agp = version_tuple(requirements.agp_version)
    if len(agp) >= 2:
        return GRADLE_FOR_AGP.get((agp[0], agp[1]))
    return None


def managed_gradle(version: str) -> Path:
    return (
        cache_directory()
        / "gradle"
        / ("gradle-" + version)
        / "bin"
        / ("gradle.bat" if os.name == "nt" else "gradle")
    )


def gradle_runtime_version(executable: Path) -> Optional[str]:
    try:
        result = run([str(executable), "--version"])
    except OSError:
        return None
    match = re.search(r"^Gradle\s+([^\s]+)\s*$", result.stdout, re.MULTILINE)
    return match.group(1) if result.returncode == 0 and match else None


def local_gradle_candidates(version: str) -> List[Path]:
    executable_name = "gradle.bat" if os.name == "nt" else "gradle"
    values = [managed_gradle(version)]
    gradle_homes = []
    if os.environ.get("GRADLE_USER_HOME"):
        gradle_homes.append(Path(os.environ["GRADLE_USER_HOME"]).expanduser())
    gradle_homes.append(Path.home() / ".gradle")
    for gradle_home in gradle_homes:
        distribution_root = gradle_home / "wrapper" / "dists"
        if distribution_root.is_dir():
            values.extend(
                distribution_root.glob(
                    "gradle-{}-*/**/gradle-{}/bin/{}".format(
                        version,
                        version,
                        executable_name,
                    )
                )
            )
    system_gradle = shutil.which("gradle")
    if system_gradle:
        values.append(Path(system_gradle))
    unique = []
    seen = set()
    for value in values:
        try:
            key = str(value.resolve())
        except OSError:
            key = str(value)
        if key not in seen:
            seen.add(key)
            unique.append(value)
    return unique


def find_local_gradle(version: str) -> Optional[Path]:
    for candidate in local_gradle_candidates(version):
        if candidate.is_file() and gradle_runtime_version(candidate) == version:
            return candidate.resolve()
    return None


def install_gradle(version: str) -> Path:
    cached = find_local_gradle(version)
    if cached is not None:
        print("Reusing local Gradle " + version + ": " + str(cached), file=sys.stderr)
        return cached
    executable = managed_gradle(version)
    target = executable.parent.parent
    if executable.exists():
        return executable
    target.parent.mkdir(parents=True, exist_ok=True)
    base_name = "gradle-" + version + "-bin.zip"
    url = GRADLE_DOWNLOAD_ROOT + base_name
    checksum_url = url + ".sha256"
    with tempfile.TemporaryDirectory(prefix="hpplay-gradle-") as temporary:
        temporary_dir = Path(temporary)
        archive = temporary_dir / base_name
        checksum_file = temporary_dir / (base_name + ".sha256")
        extracted = temporary_dir / "extracted"
        extracted.mkdir()
        try:
            download(checksum_url, checksum_file)
            checksum = checksum_file.read_text(encoding="ascii").strip().split()[0]
            download(url, archive)
        except SetupError as exc:
            raise SetupError(
                "No Gradle "
                + version
                + " distribution was found in the Skill cache, GRADLE_USER_HOME, ~/.gradle, "
                "or PATH, and the "
                "official download failed. Configure HTTP_PROXY/HTTPS_PROXY, populate the "
                "Gradle wrapper cache, or install the exact version locally. "
                + str(exc)
            ) from exc
        if digest(archive, "sha256").lower() != checksum.lower():
            raise SetupError("Gradle distribution checksum verification failed")
        safe_extract_zip(archive, extracted)
        source = extracted / ("gradle-" + version)
        if not source.is_dir():
            raise SetupError("Unexpected Gradle archive layout")
        staged = target.parent / (target.name + ".tmp")
        if staged.exists():
            shutil.rmtree(str(staged))
        shutil.copytree(str(source), str(staged), symlinks=True)
        if target.exists():
            shutil.rmtree(str(target))
        staged.replace(target)
    if os.name != "nt":
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
    return executable


def ensure_gradle_wrapper(
    project_dir: Path,
    requirements: Requirements,
    environment: Dict[str, str],
) -> Tuple[List[str], bool]:
    command = gradle_wrapper_command(project_dir)
    if command:
        return command, False
    version = recommended_gradle(requirements)
    if not version:
        raise SetupError(
            "The project has no Gradle Wrapper and its compatible Gradle version could not "
            "be inferred. Rerun with --gradle-version <version>."
        )
    gradle = install_gradle(version)
    print("Creating Gradle Wrapper " + version, file=sys.stderr)
    with tempfile.TemporaryDirectory(prefix="hpplay-gradle-wrapper-") as temporary:
        temporary_dir = Path(temporary)
        (temporary_dir / "settings.gradle").write_text("\n", encoding="utf-8")
        wrapper_arguments = [
            str(gradle),
            "wrapper",
            "--gradle-version",
            version,
            "--distribution-type",
            "bin",
        ]
        wrapper_help = run(
            [str(gradle), "help", "--task", "wrapper"],
            cwd=temporary_dir,
            env=environment,
        )
        if wrapper_help.returncode == 0 and "--no-validate-url" in wrapper_help.stdout:
            # Gradle 8+ may contact services.gradle.org just to validate the URL.
            # The locally executed distribution already matches the requested version.
            wrapper_arguments.append("--no-validate-url")
        result = run(
            wrapper_arguments,
            cwd=temporary_dir,
            env=environment,
        )
        if result.returncode != 0:
            raise SetupError("Gradle Wrapper creation failed:\n" + result.stdout[-4000:])
        generated_properties = temporary_dir / "gradle" / "wrapper" / "gradle-wrapper.properties"
        wrapper_properties = generated_properties.read_text(encoding="utf-8").splitlines()
        generated_properties.write_text(
            "\n".join(
                line
                for line in wrapper_properties
                if not line.startswith("validateDistributionUrl=")
            )
            + "\n",
            encoding="utf-8",
        )
        (project_dir / "gradle" / "wrapper").mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(temporary_dir / "gradlew"), str(project_dir / "gradlew"))
        shutil.copy2(str(temporary_dir / "gradlew.bat"), str(project_dir / "gradlew.bat"))
        for name in ("gradle-wrapper.jar", "gradle-wrapper.properties"):
            shutil.copy2(
                str(temporary_dir / "gradle" / "wrapper" / name),
                str(project_dir / "gradle" / "wrapper" / name),
            )
    if os.name != "nt":
        wrapper = project_dir / "gradlew"
        wrapper.chmod(wrapper.stat().st_mode | stat.S_IXUSR)
    command = gradle_wrapper_command(project_dir)
    if not command:
        raise SetupError("Gradle Wrapper was created but could not be verified")
    return command, True


def git_output(project_dir: Path, arguments: Sequence[str]) -> Optional[str]:
    try:
        result = run(["git", "-C", str(project_dir)] + list(arguments))
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def ensure_local_properties(project_dir: Path, sdk_root: Path) -> Optional[Path]:
    destination = project_dir / "local.properties"
    tracked = git_output(project_dir, ["ls-files", "--error-unmatch", "--", "local.properties"])
    if tracked is not None:
        print(
            "Warning: local.properties is Git-tracked; leaving it unchanged and using environment variables.",
            file=sys.stderr,
        )
        return None
    git_root = git_output(project_dir, ["rev-parse", "--show-toplevel"])
    ignored = git_output(project_dir, ["check-ignore", "local.properties"])
    if git_root and ignored is None:
        exclude = Path(git_root) / ".git" / "info" / "exclude"
        try:
            relative = destination.resolve().relative_to(Path(git_root).resolve()).as_posix()
            exclude.parent.mkdir(parents=True, exist_ok=True)
            existing = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
            if relative not in existing.splitlines():
                with exclude.open("a", encoding="utf-8") as handle:
                    if existing and not existing.endswith("\n"):
                        handle.write("\n")
                    handle.write(relative + "\n")
        except (OSError, ValueError):
            pass

    lines = destination.read_text(encoding="utf-8").splitlines() if destination.exists() else []
    escaped = str(sdk_root).replace("\\", "\\\\").replace(":", "\\:")
    replacement = "sdk.dir=" + escaped
    updated = []
    found = False
    for line in lines:
        if re.match(r"^\s*sdk\.dir\s*=", line):
            if not found:
                updated.append(replacement)
                found = True
        else:
            updated.append(line)
    if not found:
        updated.append(replacement)
    destination.write_text("\n".join(updated) + "\n", encoding="utf-8")
    try:
        destination.chmod(0o600)
    except OSError:
        pass
    return destination


def write_state(
    project_dir: Path,
    requirements: Requirements,
    java: JavaRuntime,
    sdk_root: Path,
) -> Path:
    destination = state_directory() / "android-environment.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "projectDir": str(project_dir),
        "javaHome": str(java.home),
        "javaMajor": java.major,
        "androidSdkRoot": str(sdk_root),
        "compileSdk": requirements.compile_sdk,
        "buildTools": requirements.build_tools,
        "gradleVersion": requirements.gradle_version or recommended_gradle(requirements),
        "agpVersion": requirements.agp_version,
    }
    destination.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    try:
        destination.chmod(0o600)
    except OSError:
        pass
    return destination


def missing_items(
    project_dir: Path,
    requirements: Requirements,
    java: Optional[JavaRuntime],
    sdk_root: Optional[Path],
) -> List[str]:
    missing = []
    if java is None:
        missing.append("compatible JDK " + str(requirements.java_major))
    if sdk_root is None:
        missing.append("Android SDK packages")
    if gradle_wrapper_command(project_dir) is None:
        missing.append("Gradle Wrapper")
    return missing


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Detect and prepare JDK, Android SDK, and Gradle for an Android project."
    )
    result.add_argument("--project-dir", required=True, help="Android project root")
    result.add_argument("--compile-sdk", type=int, help="Override an undetectable compileSdk")
    result.add_argument("--build-tools", help="Override an undetectable buildToolsVersion")
    result.add_argument("--gradle-version", help="Gradle version to use if the wrapper is missing")
    result.add_argument(
        "--check",
        action="store_true",
        help="Report missing tools without downloading or changing files",
    )
    result.add_argument(
        "--accept-licenses",
        action="store_true",
        help="Accept Android SDK licenses only after the tester reviewed them and answered y",
    )
    return result


def main() -> int:
    arguments = parser().parse_args()
    project_dir = Path(arguments.project_dir).expanduser().resolve()
    if not project_dir.is_dir():
        print("error: Android project directory does not exist: " + str(project_dir), file=sys.stderr)
        return 2
    requirements = inspect_project(
        project_dir,
        arguments.compile_sdk,
        arguments.build_tools,
        arguments.gradle_version,
    )
    java = find_java(requirements)
    sdk_root = find_android_sdk(project_dir, requirements)

    print("Project: " + str(project_dir))
    print("AGP: " + (requirements.agp_version or "not detected"))
    print("Gradle: " + (requirements.gradle_version or "not detected"))
    print("Required JDK: " + str(requirements.java_major))
    print("compileSdk: " + (str(requirements.compile_sdk) if requirements.compile_sdk else "not detected"))
    print("buildTools: " + (requirements.build_tools or "project/AGP default"))
    missing = missing_items(project_dir, requirements, java, sdk_root)
    if arguments.check:
        if java:
            print("JAVA_HOME: " + str(java.home))
        if sdk_root:
            print("ANDROID_SDK_ROOT: " + str(sdk_root))
        local_gradle_version = recommended_gradle(requirements)
        if local_gradle_version:
            local_gradle = find_local_gradle(local_gradle_version)
            if local_gradle:
                print("Local Gradle distribution: " + str(local_gradle))
        if missing:
            print("Missing: " + ", ".join(missing))
            return 1
        print("Android build environment is ready.")
        return 0

    try:
        if java is None:
            java = install_jdk(requirements.java_major)
        sdk_root = ensure_android_sdk(
            project_dir,
            requirements,
            java,
            arguments.accept_licenses,
        )
        environment = build_environment(java, sdk_root)
        wrapper, wrapper_created = ensure_gradle_wrapper(project_dir, requirements, environment)
        ensure_local_properties(project_dir, sdk_root)
        verification_command = wrapper
        gradle_version = recommended_gradle(requirements)
        if wrapper_created and gradle_version:
            local_gradle = find_local_gradle(gradle_version)
            if local_gradle is not None:
                verification_command = [str(local_gradle)]
        print("Verifying Gradle environment", file=sys.stderr)
        verification = run(
            verification_command + ["--version"],
            cwd=project_dir,
            env=environment,
        )
        if verification.returncode != 0:
            raise SetupError("Gradle Wrapper verification failed:\n" + verification.stdout[-4000:])
        state = write_state(project_dir, requirements, java, sdk_root)
    except (OSError, ValueError, json.JSONDecodeError, ET.ParseError, SetupError) as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2

    print("JAVA_HOME=" + str(java.home))
    print("ANDROID_SDK_ROOT=" + str(sdk_root))
    print("Environment state: " + str(state))
    print("Android build environment is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
