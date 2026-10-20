# Troubleshooting

## No device appears

First confirm the generated diagnostic sequence contains bind success, browse requested, browse started, and `onBrowse(resultCode, count)`. If one event is absent, fix that stage before investigating the network. Check that the phone and TV are on the same reachable network, multicast is not blocked, AP isolation is disabled, and the merged Manifest has the required network permissions. Distinguish `BROWSE_NO_LEBO_DEVICE` (other responses were seen) from `BROWSE_MULTICAST_BLOCKED` (no response was seen).

In a Skill-free build, internal logs may show discovered devices that never reach the public callback. The SDK accepts devices whose reported App ID maps to a server channel with `type == 1`; other channel types, DLNA-only entries, and missing App ID metadata are intentionally filtered. Do not diagnose this as multicast failure.

Check lifecycle logs around the browse. A generated Activity or Fragment must not call `stopBrowse()` from `onPause()` or `onStop()`. Opening QR scanning, permissions, MediaProjection consent, settings, or another Activity can otherwise stop a valid search before it produces a stable result.

## Device is rejected

For `PARSE_NOT_OFFICIAL_SINK` or `EXTRA_CONNECT_NOT_OFFICIAL_SINK`, first inspect the preceding SDK logs. If they contain `Cleartext HTTP traffic to <private-ip> not permitted`, `requestLelinkTxtInfo failed`, or `checkSink reject ... appId:0`, the host configuration is incomplete rather than proof that the receiver is unsupported. Add `android:usesCleartextTraffic="true"` to the host `<application>`, verify it in the final merged Manifest, reinstall the APK, and retest. The blocked `DnsTxtInfo` request prevents the SDK from obtaining the receiver App ID and can produce `WHAT_CONNECT_FAILED`/`EXTRA_CONNECT_NOT_OFFICIAL_SINK` (`212010/212101`) as a false rejection.

Only after LAN HTTP metadata loading succeeds should `PARSE_NOT_OFFICIAL_SINK` or `EXTRA_CONNECT_NOT_OFFICIAL_SINK` be treated as an unsupported receiver. Then do not retry the connection; show `getSinkInstallGuide()` and ask the user to install and open the official TV app.

## QR camera returns but parsing never starts

Treat camera decoding and SDK parsing as two stages. Confirm the camera result is `RESULT_OK` and contains non-empty text, then confirm `addQRCodeToLelinkServiceInfo()` is invoked and `onParseResult` reports a numeric code. Do not log the QR text. If the SDK parse call is absent, fix Activity-result delivery rather than SDK discovery.

## Public cast rejects a local file

`WHAT_ERROR_PUSH_INIT` with `EXTRA_ERROR_PUSH_LOCAL_MEDIA_ON_IM` means the target is reached through the public-network path and cannot fetch a sender-local path or URI. Replace it with a receiver-accessible HTTP(S) URL, or select a supported local-network receiver.

## Mirroring skips consent or never captures

For an ordinary application, first inspect how its `LelinkPlayerInfo` is built. Remove `useSystemMirrorCapture(true)` and leave the value unset/default `false` or explicitly pass `false`, then retest from a clean process. `true` tells the SDK to skip the normal MediaProjection authorization path and is valid only for a confirmed system application using the SDK-supported system capture path. If logs report `startMirror skipPerm=true` for an ordinary app, trace and remove the option that enabled permission skipping. Verify that starting mirror shows MediaProjection consent, denial is handled without starting capture, and approval reaches the SDK permission callback before diagnosing codec, transport, or receiver issues.

If mirror start throws `NoClassDefFoundError` for `androidx.core.content.ContextCompat`, `androidx.core.app.NotificationCompat`, or another `androidx.core` class, add an explicit compatible `androidx.core:core` dependency to the host. A local AAR has no POM and cannot bring this dependency transitively.

If MediaProjection authorization succeeds but `startForeground()` fails with `Bad notification for startForeground`, inspect the built variant's merged `<application android:icon>` and confirm the resource resolves and `ApplicationInfo.icon` is non-zero. The SDK uses that value as the mirror notification small icon.

## Gradle or dependencies cannot download

Before downloading Gradle, inspect the exact-version distributions under `GRADLE_USER_HOME/wrapper/dists` or `~/.gradle/wrapper/dists`; the environment script reuses their extracted `bin/gradle`. If none exists and `services.gradle.org` times out, configure `HTTP_PROXY`/`HTTPS_PROXY` or populate the wrapper cache instead of repeatedly waiting for the same 60-second timeout.

For AGP or AndroidX repository failures, use the generated project's `ANDROID_GRADLE_PLUGIN_MIRROR`, `ANDROID_GOOGLE_MAVEN_MIRROR`, and `ANDROID_CENTRAL_MAVEN_MIRROR` environment variables, or configure the user's Gradle proxy. Keep official repositories as fallback and keep credentials out of tracked project files.

## Browse or player callbacks repeat

Repeated identical `BROWSE_SUCCESS` callbacks are expected during an active browse. Always replace internal SDK objects, but fingerprint stable visible content and aggregate identical log/UI emissions. An unsolicited `BROWSE_STOP(2)` at about 30 seconds is normal browse-window completion.

Repeated player `onStart` is also a state notification, not a new session. Make its handling idempotent. If `seekTo` produces `onStart` but no `onSeekComplete`, confirm the new position through `onPositionUpdate` with tolerance and a timeout before treating it as a failure.

## QR or PIN lambda is ambiguous

The current API contains both `IServiceInfoParseListener` and deprecated `IParceResultListener` overloads. Assign the lambda to an `IServiceInfoParseListener` variable, then pass that variable to `addQRCodeToLelinkServiceInfo` or `addPinCodeToLelinkServiceInfo`.

## Binding or playback fails

For Skill-managed credentials, run `scripts/onboard.py --project-dir <project> --app-name "<application name>" --check` first. SDK error `402` commonly means the initialization credential is wrong: `SkillSdkConfig.APP_SECRET` must equal platform `md5Key`, never platform `secret`. Let the local check verify Skill-managed values and rerun onboarding if it fails. For a pre-existing host-managed pair, trace both non-placeholder `setSdkInitInfo` arguments without printing them and do not trigger registration or login. Then confirm SDK artifact integrity, network access, and that operations occur in order: bind, browse, connect callback, start media. Verify `connect()` receives the exact current callback object and casting waits for `onConnect`. Capture callback domain and codes separately. `diagnose()` is local-only diagnostic text; redact app credentials before sending it to support.
