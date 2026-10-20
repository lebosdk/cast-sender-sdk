#!/usr/bin/env python3
"""Download, validate, and place the latest Android sender SDK AAR."""

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
from typing import Iterable, Optional
from urllib import request
import zipfile


SDK_CDN_URL = "https://lebotob.hpplay.cn/sdk/android/release/source-leboapk-release.aar"
SDK_FILENAME = "android-sender-sdk.aar"
SKIP_DIRS = {".git", ".gradle", ".idea", "build", "out", "node_modules"}


class ArtifactError(Exception):
    pass


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def validate_aar(path: Path) -> str:
    if not path.is_file():
        raise ArtifactError("SDK AAR does not exist: " + str(path))
    if not zipfile.is_zipfile(str(path)):
        raise ArtifactError("SDK artifact is not a valid AAR/ZIP file: " + str(path))
    with zipfile.ZipFile(str(path)) as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise ArtifactError("SDK AAR contains a corrupt entry: " + corrupt)
        names = set(archive.namelist())
        if "AndroidManifest.xml" not in names or "classes.jar" not in names:
            raise ArtifactError("SDK AAR must contain AndroidManifest.xml and classes.jar")
    actual = sha256(path)
    return actual


def gradle_files(project_dir: Path) -> Iterable[Path]:
    for root, directories, files in os.walk(str(project_dir)):
        directories[:] = [item for item in directories if item not in SKIP_DIRS]
        for name in files:
            if name in ("build.gradle", "build.gradle.kts"):
                yield Path(root) / name


def applies_android_application_plugin(text: str) -> bool:
    if re.search(
        r"apply\s+plugin\s*:\s*[\"']com\.android\.application[\"']",
        text,
    ):
        return True
    for line in text.splitlines():
        if not re.search(
            r"\bid\s*(?:\(\s*)?[\"']com\.android\.application[\"']",
            line,
        ):
            continue
        if not re.search(r"\bapply\s+false\b", line):
            return True
    return False


def find_app_module(project_dir: Path, module_dir: Optional[str]) -> Path:
    if module_dir:
        candidate = Path(module_dir).expanduser()
        if not candidate.is_absolute():
            candidate = project_dir / candidate
        candidate = candidate.resolve()
        try:
            candidate.relative_to(project_dir)
        except ValueError as exc:
            raise ArtifactError("Application module must be inside the project") from exc
        if not candidate.is_dir():
            raise ArtifactError("Application module does not exist: " + str(candidate))
        return candidate

    candidates = []
    for build_file in gradle_files(project_dir):
        try:
            text = build_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if applies_android_application_plugin(text):
            candidates.append(build_file.parent.resolve())
    unique = sorted(set(candidates), key=str)
    if len(unique) == 1:
        return unique[0]
    if not unique:
        raise ArtifactError(
            "No Android application module was detected. Pass --module-dir explicitly."
        )
    raise ArtifactError(
        "Multiple Android application modules were detected. Pass --module-dir explicitly: "
        + ", ".join(str(item.relative_to(project_dir)) for item in unique)
    )


def configured_cdn() -> str:
    url = SDK_CDN_URL.strip()
    if not url:
        raise ArtifactError("The Skill SDK CDN URL is not configured")
    if not url.lower().startswith("https://"):
        raise ArtifactError("The configured SDK CDN URL must use HTTPS")
    return url


def download_aar(url: str, destination: Path) -> None:
    print("Downloading latest SDK AAR: " + url, file=sys.stderr)
    http_request = request.Request(
        url,
        headers={
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "User-Agent": "cast-sender-sdk-skill",
        },
    )
    with request.urlopen(http_request, timeout=60) as response, destination.open("wb") as output:
        if not response.geturl().lower().startswith("https://"):
            raise ArtifactError("The SDK CDN redirected to a non-HTTPS URL")
        shutil.copyfileobj(response, output)


def copy_atomically(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=destination.name + ".",
        dir=str(destination.parent),
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        shutil.copy2(str(source), str(temporary))
        os.replace(str(temporary), str(destination))
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Download and place the latest Android sender SDK AAR."
    )
    result.add_argument("--project-dir", required=True, help="Android project root")
    result.add_argument("--module-dir", help="Application module, relative to the project root")
    result.add_argument(
        "--check",
        action="store_true",
        help="Download and validate the latest AAR without changing the project",
    )
    return result


def main() -> int:
    arguments = parser().parse_args()
    project_dir = Path(arguments.project_dir).expanduser().resolve()
    try:
        if not project_dir.is_dir():
            raise ArtifactError("Android project does not exist: " + str(project_dir))
        module_dir = find_app_module(project_dir, arguments.module_dir)
        destination = module_dir / "libs" / SDK_FILENAME
        url = configured_cdn()
        with tempfile.TemporaryDirectory(prefix="android-sender-aar-") as temporary:
            source = Path(temporary) / SDK_FILENAME
            download_aar(url, source)
            actual_sha256 = validate_aar(source)

            print("Application module: " + str(module_dir))
            print("SDK source: " + url)
            print("Destination: " + str(destination))
            print("SHA-256: " + actual_sha256)

            if arguments.check:
                print("Latest SDK AAR is valid; no project files were changed.")
                return 0

            if destination.is_file() and sha256(destination) == actual_sha256:
                print("Latest SDK AAR is already installed.")
                return 0
            if destination.exists() and not destination.is_file():
                raise ArtifactError("SDK AAR destination is not a file: " + str(destination))
            copy_atomically(source, destination)

        print("Latest SDK AAR installed: " + str(destination))
        return 0
    except (OSError, ArtifactError, zipfile.BadZipFile) as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
