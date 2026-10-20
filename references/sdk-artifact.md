# SDK AAR acquisition

Do not ask the developer to supply an SDK file. Before adding or updating integration code, download the latest release AAR from the fixed official CDN URL configured in `scripts/obtain_sdk_aar.py`: `https://lebotob.hpplay.cn/sdk/android/release/source-leboapk-release.aar`.

Validate the remote artifact and target module without modifying the project:

```bash
python3 scripts/obtain_sdk_aar.py \
  --project-dir /path/to/android-project \
  --check
```

`--check` still downloads the current CDN artifact. It requires HTTPS after redirects, verifies the ZIP is not corrupt, requires `AndroidManifest.xml` and `classes.jar`, and prints the computed SHA-256 for traceability. It does not write under the project.

Install it by removing `--check`:

```bash
python3 scripts/obtain_sdk_aar.py \
  --project-dir /path/to/android-project
```

For a project with multiple application modules, pass `--module-dir <relative-module-path>`. The script installs the artifact as `libs/android-sender-sdk.aar`. It leaves an identical installed file untouched and atomically replaces it when the CDN publishes a different version.

The production CDN path represents a mutable latest release, so the Skill cannot pin one SHA-256 without blocking future releases. Integrity therefore relies on HTTPS transport and AAR structure validation; record the SHA-256 printed on each run in the integration evidence.

## Gradle dependency

The generated project already includes all AARs under `app/libs/`. For an existing project, add the copied artifact using its established Groovy or Kotlin dependency style, for example:

```groovy
dependencies {
    implementation files("libs/android-sender-sdk.aar")
    implementation "androidx.core:core:1.13.1"
}
```

The local AAR has no POM, and its current contents do not embed AndroidX Core even though the capture permission page uses `ContextCompat` and mirror notifications use `NotificationCompat`. Keep an explicit compatible `androidx.core:core` dependency; an existing project may use its already selected compatible newer version. Inspect other embedded and external dependencies, then inspect the installed AAR's public interfaces before generating SDK calls. Do not introduce an additional user approval prompt for this compatibility check.
