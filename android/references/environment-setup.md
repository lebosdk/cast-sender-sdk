# Android build environment

Prepare the build environment before changing SDK integration code. The host project does not need to have JDK, Android SDK, `adb`, or a global Gradle installation in advance.

This workflow requires an Android project directory. If no project exists yet, follow [Android project selection and creation](project-setup.md) first.

## Detect

Run the read-only check from the Skill directory:

```bash
python3 scripts/prepare_android_env.py \
  --project-dir /path/to/android-project \
  --check
```

The script inspects the project's Android Gradle Plugin, Gradle Wrapper, `compileSdk`, and `buildToolsVersion`. It then checks for a compatible JDK, required Android SDK packages, platform tools, and the Gradle Wrapper. If a value is indirect or cannot be detected, inspect the project and pass the known value with `--compile-sdk`, `--build-tools`, or `--gradle-version`.

## Prepare

If the check reports missing components, first complete the confirmation phase described in `SKILL.md`. Only after the tester answers `y` to any required license prompt should you run the same command without `--check`. The script:

- reuses a compatible installed JDK or Android Studio runtime when possible;
- downloads a matching Temurin JDK into the user's cache when needed, and may use a separate JDK 17 runtime for current Android command-line tools without changing the project's JDK;
- reuses an existing Android SDK or installs verified Google command-line tools and missing SDK packages into the user's cache;
- uses the project's Gradle Wrapper, or creates a compatible wrapper when the project does not contain one; before downloading, it searches the Skill cache, `GRADLE_USER_HOME/wrapper/dists`, `~/.gradle/wrapper/dists`, and an exact-version `gradle` on `PATH`;
- writes `sdk.dir` to untracked `local.properties` without replacing other properties;
- creates or checks the wrapper, verifies the selected Gradle runtime, and records the local paths under the user's platform state directory.

It does not require administrator access and does not install a global Gradle distribution. JDK, Android command-line tools, and Gradle archives are checksum-verified before use.

If an exact Gradle distribution exists locally, the script creates Wrapper files without Gradle's otherwise automatic `services.gradle.org` URL-validation request; the generated portable Wrapper still points to the official distribution URL for other machines. If no exact distribution exists locally, Python downloads it from `services.gradle.org`. On a restricted network, configure `HTTP_PROXY`/`HTTPS_PROXY` for the preparation command or pre-populate the normal Gradle wrapper cache. A 60-second download timeout is not evidence that the version is unavailable; do not delete a valid local cache or repeatedly retry the same blocked URL.

The generated project's repository blocks accept optional organization-approved mirrors without changing tracked files:

```bash
ANDROID_GRADLE_PLUGIN_MIRROR=https://maven.aliyun.com/repository/gradle-plugin \
ANDROID_GOOGLE_MAVEN_MIRROR=https://maven.aliyun.com/repository/google \
ANDROID_CENTRAL_MAVEN_MIRROR=https://maven.aliyun.com/repository/central \
./gradlew assembleDebug
```

Official repositories remain as fallbacks. Prefer an organization's authenticated artifact proxy when available. For a direct Gradle proxy, put `systemProp.http.proxyHost`, `systemProp.http.proxyPort`, `systemProp.https.proxyHost`, and `systemProp.https.proxyPort` in the user's `~/.gradle/gradle.properties`, not the tracked project file; keep proxy credentials out of chat and source control. If an existing host uses dependency repository policy, preserve it and add only an approved equivalent source.

Android SDK licenses are legal terms and must be accepted by the tester, not by the coding agent. During the upfront confirmation phase, let the tester review them and ask `是否接受以上 Android SDK 许可证？[y/n]`. Accept only `y` or `n`, case-insensitively, and reprompt after empty or any other input. Run the following command only after `y`; after `n`, leave the licenses pending and stop environment preparation. Do not defer this approval until after SDK integration starts:

```bash
python3 scripts/prepare_android_env.py \
  --project-dir /path/to/android-project \
  --accept-licenses
```

Do not pass `--accept-licenses` merely to suppress a failed installation.

## Build

Use the `JAVA_HOME` and `ANDROID_SDK_ROOT` printed by the script for all subsequent Gradle commands in the current task. Do not put an absolute JDK path in a tracked `gradle.properties` file. Use the project wrapper rather than a globally installed `gradle` executable.

After preparation, run an appropriate project build such as:

```bash
JAVA_HOME=/selected/jdk \
ANDROID_SDK_ROOT=/selected/android-sdk \
ANDROID_HOME=/selected/android-sdk \
./gradlew assembleDebug
```

If the build reveals an SDK platform or Build Tools version that could not be inferred initially, rerun the preparation script with the corresponding override and retry the build. Report any remaining failures caused by private repositories, unavailable artifacts, proxy policy, or unsupported project configuration; do not silently change dependency versions to make the environment check pass.
