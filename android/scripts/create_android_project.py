#!/usr/bin/env python3
"""Create a minimal Android application for sender SDK integration testing."""

import argparse
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Dict
from xml.sax.saxutils import escape as xml_escape


DEFAULT_AGP_VERSION = "8.7.3"
DEFAULT_COMPILE_SDK = 35
DEFAULT_MIN_SDK = 21
DEFAULT_ANDROIDX_CORE_VERSION = "1.13.1"
JAVA_KEYWORDS = {
    "abstract", "assert", "boolean", "break", "byte", "case", "catch", "char",
    "class", "const", "continue", "default", "do", "double", "else", "enum",
    "extends", "final", "finally", "float", "for", "goto", "if", "implements",
    "import", "instanceof", "int", "interface", "long", "native", "new", "package",
    "private", "protected", "public", "return", "short", "static", "strictfp",
    "super", "switch", "synchronized", "this", "throw", "throws", "transient",
    "try", "void", "volatile", "while",
}


class ProjectError(Exception):
    pass


def validate_package_name(value: str) -> str:
    pattern = r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+$"
    if not re.fullmatch(pattern, value):
        raise ProjectError("Invalid Android application ID: " + value)
    if any(segment in JAVA_KEYWORDS for segment in value.split(".")):
        raise ProjectError("Android application ID contains a Java keyword: " + value)
    return value


def groovy_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("$", "\\$")


def java_string(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )


def project_files(
    app_name: str,
    package_name: str,
    agp_version: str,
    compile_sdk: int,
    min_sdk: int,
) -> Dict[str, str]:
    package_path = package_name.replace(".", "/")
    return {
        ".gitignore": """.gradle/
.idea/
*.iml
build/
**/build/
local.properties
app/libs/*.aar
""",
        "settings.gradle": """pluginManagement {
    repositories {
        def pluginMirror = providers.environmentVariable("ANDROID_GRADLE_PLUGIN_MIRROR").orNull
        if (pluginMirror) {
            maven { url = uri(pluginMirror) }
        }
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        def googleMirror = providers.environmentVariable("ANDROID_GOOGLE_MAVEN_MIRROR").orNull
        def centralMirror = providers.environmentVariable("ANDROID_CENTRAL_MAVEN_MIRROR").orNull
        if (googleMirror) {
            maven { url = uri(googleMirror) }
        }
        if (centralMirror) {
            maven { url = uri(centralMirror) }
        }
        google()
        mavenCentral()
    }
}

rootProject.name = "%s"
include ":app"
""" % groovy_string(app_name),
        "build.gradle": """plugins {
    id "com.android.application" version "%s" apply false
}
""" % agp_version,
        "gradle.properties": """org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
""",
        "app/build.gradle": """plugins {
    id "com.android.application"
}

android {
    namespace "%(package_name)s"
    compileSdk %(compile_sdk)d

    defaultConfig {
        applicationId "%(package_name)s"
        minSdk %(min_sdk)d
        targetSdk %(compile_sdk)d
        versionCode 1
        versionName "1.0"
    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro"
        }
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }
}

dependencies {
    implementation fileTree(dir: "libs", include: ["*.jar", "*.aar"])
    // The sender AAR references ContextCompat and NotificationCompat but cannot
    // publish transitive dependencies when installed as a local file.
    implementation "androidx.core:core:%(androidx_core_version)s"
}
""" % {
            "package_name": package_name,
            "compile_sdk": compile_sdk,
            "min_sdk": min_sdk,
            "androidx_core_version": DEFAULT_ANDROIDX_CORE_VERSION,
        },
        "app/proguard-rules.pro": "# Add app-specific R8 rules here.\n",
        "app/src/main/AndroidManifest.xml": """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">
    <!-- The SDK AAR declares USB Host as required. Keep ordinary sender apps installable
         on devices without USB Host unless the product explicitly requires USB casting. -->
    <uses-feature
        android:name="android.hardware.usb.host"
        android:required="false"
        tools:replace="android:required" />

    <!-- Optional SDK capabilities must be opted into deliberately after privacy review. -->
    <uses-permission
        android:name="android.permission.SYSTEM_ALERT_WINDOW"
        tools:node="remove" />
    <uses-permission
        android:name="android.permission.READ_EXTERNAL_STORAGE"
        tools:node="remove" />
    <uses-permission
        android:name="android.permission.WRITE_EXTERNAL_STORAGE"
        tools:node="remove" />

    <application
        android:allowBackup="false"
        android:icon="@drawable/ic_launcher"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:usesCleartextTraffic="true">
        <activity
            android:name=".MainActivity"
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
        <service
            android:name="com.hpplay.sdk.source.api.LelinkAccessibilityService"
            tools:node="remove" />
    </application>
</manifest>
""",
        "app/src/main/res/drawable/ic_launcher.xml": """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="48dp"
    android:height="48dp"
    android:viewportWidth="48"
    android:viewportHeight="48">
    <path
        android:fillColor="#1976D2"
        android:pathData="M6,6h36v36h-36z" />
    <path
        android:fillColor="#FFFFFFFF"
        android:pathData="M12,13h24v17h-9l-6,6v-6h-9z" />
</vector>
""",
        "app/src/main/res/values/strings.xml": """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">{}</string>
</resources>
""".format(xml_escape(app_name)),
        "app/src/main/java/{}/MainActivity.java".format(package_path): """package {package_name};

import android.app.Activity;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.TextView;

public final class MainActivity extends Activity {{
    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        TextView status = new TextView(this);
        status.setGravity(Gravity.CENTER);
        status.setText("{app_name} is ready for Sender SDK integration");
        setContentView(status);
    }}
}}
""".format(package_name=package_name, app_name=java_string(app_name)),
    }


def validate_destination(destination: Path) -> None:
    if destination.exists() and not destination.is_dir():
        raise ProjectError("Project destination is not a directory: " + str(destination))
    if destination.exists() and any(destination.iterdir()):
        raise ProjectError("Refusing to overwrite a non-empty directory: " + str(destination))


def initialize_git_repository(project_dir: Path) -> None:
    git = shutil.which("git")
    if not git:
        raise ProjectError(
            "Git is required because onboarding stores credentials only in ignored files"
        )
    result = subprocess.run(
        [git, "init", "--quiet", str(project_dir)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise ProjectError("Git repository initialization failed: " + result.stdout.strip())


def create_project(destination: Path, files: Dict[str, str]) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="android-sender-project-", dir=str(destination.parent)) as temp:
        staged = Path(temp) / destination.name
        staged.mkdir()
        for relative, content in files.items():
            target = staged / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
        initialize_git_repository(staged)
        if destination.exists():
            destination.rmdir()
        os.replace(str(staged), str(destination))


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Create a minimal Android app for Sender SDK integration."
    )
    result.add_argument("--project-dir", required=True, help="New Android project directory")
    result.add_argument("--app-name", required=True, help="Application display name")
    result.add_argument("--package-name", required=True, help="Android application ID")
    result.add_argument("--agp-version", default=DEFAULT_AGP_VERSION)
    result.add_argument("--compile-sdk", type=int, default=DEFAULT_COMPILE_SDK)
    result.add_argument("--min-sdk", type=int, default=DEFAULT_MIN_SDK)
    mode = result.add_mutually_exclusive_group()
    mode.add_argument(
        "--check",
        action="store_true",
        help="Validate and display inputs without creating files",
    )
    mode.add_argument(
        "--confirm",
        action="store_true",
        help="Create only after the user confirmed the exact app name and application ID",
    )
    return result


def main() -> int:
    arguments = parser().parse_args()
    destination = Path(arguments.project_dir).expanduser().resolve()
    try:
        app_name = arguments.app_name.strip()
        if not app_name or len(app_name) > 50:
            raise ProjectError("Application name must contain 1 to 50 characters")
        if any(ord(character) < 32 for character in app_name):
            raise ProjectError("Application name must not contain control characters")
        package_name = validate_package_name(arguments.package_name.strip())
        if arguments.min_sdk < 21:
            raise ProjectError("minSdk must be at least 21")
        if arguments.compile_sdk < arguments.min_sdk:
            raise ProjectError("compileSdk must not be lower than minSdk")
        if not re.fullmatch(r"\d+(?:\.\d+){1,3}(?:[-+._A-Za-z0-9]*)?", arguments.agp_version):
            raise ProjectError("Invalid Android Gradle Plugin version")
        validate_destination(destination)
        files = project_files(
            app_name,
            package_name,
            arguments.agp_version,
            arguments.compile_sdk,
            arguments.min_sdk,
        )
        print("Project: " + str(destination))
        print("Application: " + app_name)
        print("applicationId: " + package_name)
        print("AGP: " + arguments.agp_version)
        print("compileSdk: " + str(arguments.compile_sdk))
        if arguments.check:
            print("Project inputs are valid; no files were created.")
            print(
                "Before rerunning with --confirm, let the user choose a displayed candidate "
                "or type each identity value and press Enter, then confirm the exact pair [y/n]."
            )
            return 0
        if not arguments.confirm:
            raise ProjectError(
                "User confirmation is required. Ask the user to confirm the exact application "
                "name and applicationId with y or n, then rerun with --confirm only after y."
            )
        create_project(destination, files)
    except (OSError, ProjectError) as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2
    print("Android project created and initialized as a Git repository.")
    print("Run prepare_android_env.py next.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
