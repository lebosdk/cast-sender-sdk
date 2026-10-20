# SDK installation and host-app requirements

## Build environment

Before editing the integration, follow [Android build environment](environment-setup.md). Detect and, when necessary, prepare the compatible JDK, Android SDK packages, platform tools, and Gradle Wrapper. Use the environment selected by that workflow for every Gradle invocation.

## Dependency

For a new/full integration or an explicitly requested SDK update, follow [SDK AAR acquisition](sdk-artifact.md) and use the Skill script to download, validate, and install the AAR from its fixed official HTTPS CDN URL. Do not ask the developer to provide an SDK file. For an incremental capability change, preserve the existing artifact unless the requested API is absent. When acquiring an artifact, inspect it and its release metadata to determine whether transitive dependencies are embedded before adding it to the host app; this is an automated compatibility check, not a user approval prompt.

The SDK AAR is installed as a local file, so Gradle cannot discover Maven transitive dependencies from it. Add AndroidX Core explicitly to every host application. The generated project uses:

```groovy
dependencies {
    implementation fileTree(dir: "libs", include: ["*.jar", "*.aar"])
    implementation "androidx.core:core:1.13.1"
}
```

An existing host may retain a compatible newer AndroidX Core version already selected by its dependency management. Do not remove this dependency after compilation: the SDK capture permission activity loads `androidx.core.content.ContextCompat`, and mirror notification creation loads `androidx.core.app.NotificationCompat` only at runtime. A build that omits Core can compile successfully and then fail with `NoClassDefFoundError` when the user starts mirroring.

Record the SDK version, SHA-256, and release notes. Before onboarding, inspect an existing integration as described in [incremental integration](incremental-integration.md) and reuse its non-placeholder App ID and SDK App Secret in place. If no reusable credentials are available, use [credential onboarding](onboarding.md). The Skill keeps the platform `secret` and `md5Key` as separate ignored local properties, then generates an ignored `SkillSdkConfig` source file where `APP_SECRET` is populated from `md5Key`. Never commit credentials.

Before every Debug or Release build using Skill-managed credentials, run `scripts/onboard.py --project-dir <project> --app-name "<application name>" --check`. Proceed only when it reports that `APP_SECRET` uses platform `md5Key`. The check must block a missing config, an `APP_ID` mismatch, an `APP_SECRET` mismatch, or the specific error where `APP_SECRET` contains platform `secret`. For a pre-existing host-managed pair, preserve its source and verify both initialization arguments remain wired without printing or migrating them; do not run mutating onboarding.

## Initialization

Register bind, browse, connect, and player listeners before calling `setSdkInitInfo(context, SkillSdkConfig.APP_ID, SkillSdkConfig.APP_SECRET).bindSdk()`. The only valid mapping is `APP_ID = appId` and `APP_SECRET = md5Key`; platform `secret` must never be passed to this API. Call `startBrowse()` only from a successful bind callback. Call `connect(info)` with a selected device and start the selected media-push or mirroring flow only after the connection callback.

Implement [discovery and connection](discovery-connection.md) rather than placing SDK state directly in an Activity. Keep singleton listener ownership, the current browse snapshot, selected device, and connected device in one application-level coordinator. Remove or replace listeners only when that coordinator is finally destroyed; do not leave an Activity captured by a long-lived callback.

UI lifecycle callbacks manage UI observation only. Do not stop browse or disconnect in Activity/Fragment `onPause()` or `onStop()`: opening a QR scanner, permission page, MediaProjection consent, settings, or another Activity triggers those callbacks. An explicit browse stop/refresh or final coordinator teardown owns `stopBrowse()`.

## Android configuration

The SDK reads receiver metadata, including the App ID used for APK-channel eligibility, from a runtime LAN endpoint such as `http://<receiver-ip>:<port>/www.hpplay.com.cn/tv/app/DnsTxtInfo`. Android 9 and later block this request by default for modern target SDK versions. Every integrated host application must therefore declare cleartext traffic support on its own `<application>` element:

```xml
<application
    android:usesCleartextTraffic="true"
    ...>
```

Do not assume the AAR can supply or override this application policy. The receiver IP and port are dynamic, so a fixed domain allowlist is not a substitute. If the host already declares `android:networkSecurityConfig`, inspect that XML too and ensure its effective base policy permits cleartext traffic; on supported Android versions a restrictive network security configuration can still block the request. Merge the SDK Manifest and inspect the final Debug and Release merged Manifests; both must contain `android:usesCleartextTraffic="true"` on `<application>` and must not reference a conflicting cleartext-denying policy.

The host `<application>` must also declare a valid icon resource in every built variant:

```xml
<application
    android:icon="@drawable/ic_launcher"
    ... />
```

The mirror foreground notification uses the host application's icon as its small icon. If `ApplicationInfo.icon` is `0`, or the referenced resource is absent from a variant, MediaProjection consent can succeed and `startForeground()` can then throw `Bad notification for startForeground`. Do not consider mirroring validated until the notification is posted successfully on a physical device.

The exact permission set depends on enabled features:

- Discovery and URL casting require network and Wi-Fi state access; multicast discovery must be allowed by the network.
- Local media requires the host app's media/file access flow. A public URL is preferable for cross-network casting.
- Add mirroring or audio-capture runtime permissions, MediaProjection consent, notifications, and foreground-service declarations when the explicit request or casting-scope selection includes mirroring. A new/full integration that times out to option `1` remains push-only.
- Keep SDK-declared services and bridge activities that are used by the selected features.

Request runtime permissions at the point where the feature is used. Test the host app's target Android version and the oldest supported Android version.

For an ordinary application, keep `LelinkPlayerInfo.useSystemMirrorCapture` unset/default `false` or explicitly call `useSystemMirrorCapture(false)`. Starting mirror then follows the SDK's normal MediaProjection consent path. `useSystemMirrorCapture(true)` skips that path; do not use it to bypass the consent UI, and do not generate it unless the host is a confirmed system application with the SDK-supported system capture path and that mode was explicitly requested.

## Manifest merge and store review

The current AAR declares `android.hardware.usb.host` without `android:required="false"`. Android therefore treats USB Host as required and application stores can filter out otherwise supported devices. Unless USB casting is an explicit product requirement, override it in the host manifest:

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">
    <uses-feature
        android:name="android.hardware.usb.host"
        android:required="false"
        tools:replace="android:required" />
</manifest>
```

The AAR also merges optional or review-sensitive declarations, including `SYSTEM_ALERT_WINDOW`, legacy `READ_EXTERNAL_STORAGE`/`WRITE_EXTERNAL_STORAGE`, audio and foreground-service permissions, USB components, and `com.hpplay.sdk.source.api.LelinkAccessibilityService`. Inventory the final merged Manifest for every variant and map each declaration to an enabled product capability, runtime request, store form, and privacy disclosure. Do not request a merged permission merely because the AAR declares it.

For a basic URL-push/ordinary MediaProjection host that does not offer overlay, direct legacy storage, USB casting, or accessibility-based reverse control, use higher-priority host entries to remove the unused sensitive declarations:

```xml
<uses-permission
    android:name="android.permission.SYSTEM_ALERT_WINDOW"
    tools:node="remove" />
<uses-permission
    android:name="android.permission.READ_EXTERNAL_STORAGE"
    tools:node="remove" />
<uses-permission
    android:name="android.permission.WRITE_EXTERNAL_STORAGE"
    tools:node="remove" />

<application ...>
    <service
        android:name="com.hpplay.sdk.source.api.LelinkAccessibilityService"
        tools:node="remove" />
</application>
```

The generated project includes these least-privilege overrides. If the user explicitly enables a capability that needs one of them, remove only the corresponding `tools:node="remove"`, add the modern target-SDK-specific permission flow, and update the product's user disclosure and store declarations. Never remove the MediaProjection foreground service or its required foreground-service permissions when mirroring is selected.

## R8 and release build

Use the consumer rules shipped with the official artifact. Run a minified Release smoke test covering bind, browse, connect, each selected casting-mode start, callbacks, stop, and disconnect. Record the final SDK version, host version, mapping policy, and any additional keep rules.
