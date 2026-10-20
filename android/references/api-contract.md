# API contract

This is the short checklist. For the complete public API, read [api-reference.md](api-reference.md). Verify signatures against the SDK version being integrated. The names below describe the public `LelinkSourceSDK` API expected by this Skill version.

## Core flow

An explicit request for media push, real-time screen mirroring, or adding either capability to an existing integration determines the scope; do not ask the user to select it again. Only when a new/full integration remains ambiguous, show a numbered terminal menu ordered as `1. 仅媒体推送（默认）`, `2. 仅手机屏幕实时镜像`, `3. 媒体推送 + 手机屏幕实时镜像`. Accept only `1`, `2`, or `3` and reprompt after other input. Wait up to 30 seconds. A timeout selects option `1`; state that result and do not add mirroring-specific permissions or lifecycle code in push-only mode. This is a value selection, not a `[y/n]` approval confirmation.

1. Add explicit AndroidX Core, a valid host application icon, and `android:usesCleartextTraffic="true"`; verify all three through dependency/runtime checks and the final merged Manifest. Override the AAR's USB Host feature to `android:required="false"` unless USB is a product requirement, and remove/review unused sensitive merged permissions and the accessibility service.
2. `LelinkSourceSDK.getInstance()`.
3. Create one long-lived, application-scoped device coordinator. Register `IBindSdkListener`, `IBrowseListener`, `IConnectListener`, and `ILelinkPlayerListener` or `INewPlayerListener` there before binding; UI pages attach observers instead of replacing SDK listeners.
4. Reuse an existing non-placeholder credential source and `setSdkInitInfo(...).bindSdk()` call. For Skill-managed credentials, run `scripts/onboard.py --project-dir <project> --app-name "<application name>" --check` first and require the invariant mapping `APP_ID = appId`, `APP_SECRET = md5Key`. Never pass platform `secret` to SDK initialization. Queue a browse request while binding and call `startBrowse()` only after `onBindCallback(true)`.
5. Copy every `IBrowseListener.onBrowse` list and replace the latest internal objects. Coalesce identical logs/UI updates by stable content fingerprint and report a repeat count. Treat unsolicited `BROWSE_STOP(2)` after roughly 30 seconds as normal SDK browse-window completion. Preserve the exact current `LelinkServiceInfo` selected from the newest snapshot and pass it to `connect(info)`.
6. Treat only `IConnectListener.onConnect` as connection success. Store its device and `connectType`, then start only the selected mode: use `startPlayMedia(url, mediaType, false)` or a populated `LelinkPlayerInfo` for media push. For real-time screen mirroring in an ordinary application, leave `useSystemMirrorCapture` unset/default `false` (or explicitly set `false`) and use the SDK mirror entrypoint plus the MediaProjection consent flow. Never generate `useSystemMirrorCapture(true)` for an ordinary application; it skips that authorization path and is reserved for a confirmed system-app system-capture integration.
7. Do not stop browse, disconnect, or unbind from UI `onPause()` or `onStop()`. Use `stopBrowse()` for explicit stop, serialized refresh, or final coordinator teardown; use `stopPlay()` and `disconnect(info)` according to actual feature ownership.

Read [discovery and connection](discovery-connection.md) before implementing this flow. `addQRCodeToLelinkServiceInfo(qrUrl, listener)` and `addPinCodeToLelinkServiceInfo(pinCode, listener)` parse other connection inputs. Declare `listener` as `IServiceInfoParseListener` before either call because their deprecated overload makes a bare Java lambda ambiguous. Camera decoding is a separate preceding stage; connect only after `PARSE_SUCCESS` with a non-null object returned by that callback.

## Lists and controls

For image lists, populate `ImageListInfo[]` with `ImageItem.id` and URL, set `LelinkPlayerInfo.setType(MEDIA_TYPE_IMAGE)`, `setLelinkServiceInfo(info)`, the initial URL or local path, then `setImageList(list, initialImageId, period)` and `startPlayMedia(playerInfo)`. Check `isSupportImageList(info)` before showing list controls. `appendImageList`, `clearImageList`, `playImageWithKey`, `playNextImage`, and `playPreImage` operate on the active list. The `period` field is documented by the API as list validity in seconds; confirm receiver behavior before promising an automatic per-image display interval.

After starting a cast, `queryCastCapability()` provides current available controls, or `null` when no device is connected. `canPause`, `canSeek`, `canVolume`, `canRate`, `canSwitchItem`, `canDefinition`, and `canPlayLocalMedia` are UI inputs. `rates` is a default list; `queryRate()` reports actual receiver rates asynchronously.

Make player callbacks idempotent. `onStart` may repeat about every 30 seconds during one video and may be the only post-seek state callback. Confirm seek through `onPositionUpdate` with tolerance and timeout; use `onSeekComplete` when delivered but do not require it.

`getSinkInstallGuide()` gives `h5Url`, `title`, and fallback `steps`. `diagnose()` gives local SDK state for troubleshooting and includes app and device information.

## Implementation note

`ILelinkPlayerListener` has multiple callback methods. Use the complete interface from the installed SDK artifact or the platform-neutral examples in this Skill; do not create a listener with only the error callback unless the host language provides a separate adapter.
