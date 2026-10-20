# Discovery and connection implementation

Use this contract whenever the generated application browses, parses, or connects to a receiver. It captures the working ownership model from the repository demo's `DeviceManager`, browse UI, and API-cast screen while removing demo-only USB, license, history, BLE, and test controls.

## Required ownership model

Create one long-lived device coordinator for the process or feature. It owns:

- the single `LelinkSourceSDK` instance;
- bind, browse, connect, and player listeners;
- bind/browse/connect state and any pending browse restart;
- an immutable snapshot of the latest callback device list;
- the exact selected and connected `LelinkServiceInfo` objects;
- lightweight UI observers that can attach and detach without replacing SDK listeners.

An Activity or Fragment renders coordinator state. It must not own the SDK listener lifetime. Register SDK listeners once before `bindSdk()` and do not register a new set every time a page resumes.

## State and call sequence

1. Initialize the coordinator with `applicationContext` and register all SDK listeners.
2. Call `setSdkInitInfo(applicationContext, APP_ID, APP_SECRET).bindSdk()` once. `APP_SECRET` contains platform `md5Key`.
3. A browse button or a one-shot feature initialization calls `requestBrowse()`. If binding is still pending, remember that request. Never call `startBrowse()` before `onBindCallback(true)`.
4. Start ordinary LAN discovery with `startBrowse()` or `startBrowse(true, true)`. Use `BrowserConfigBean` only for a requested advanced mode; do not copy demo-only BLE, history, sonic, Wi-Fi P2P, or permission-mode settings into a basic integration.
5. Handle each `IBrowseListener.onBrowse(resultCode, list)` independently. Copy `list` immediately and replace the internal latest snapshot even when its visible contents match the preceding callback, because the SDK may return newer object instances. Keep browsing active after incremental `BROWSE_SUCCESS` callbacks; terminal codes end the current browse state. Coalesce only logging and UI rendering, never callback processing or snapshot replacement.
6. Let the UI select an item from the current snapshot. Pass that exact object to `connect(info)`. Do not construct a new `LelinkServiceInfo`, connect by name/IP, or continue with a stale object after a refresh replaces the list.
7. Set connected state only from `IConnectListener.onConnect(info, connectType)`. Store the callback's `info` as the current connected device.
8. Start media or mirroring only after `onConnect`. Put that connected object in `LelinkPlayerInfo`; do not treat the synchronous return from `connect()` as success.
9. Clear matching connection state only for an actual disconnect or connection failure. `WHAT_HARASS_WAITING` and `WHAT_HARASS_VERIFY` are intermediate connection states and require UI handling rather than clearing the attempt.

## Browse result handling

Record redacted browse state transitions containing the callback name, numeric `resultCode`, copied device count, and current state. The SDK may emit the same `BROWSE_SUCCESS` result and unchanged two-device snapshot more than 100 times during one roughly 30-second browse window. Build a stable content fingerprint from the result code and ordered device UI keys/fields. Log and re-render the first callback and every fingerprint change; count identical repeats and emit one suppressed-repeat summary when the fingerprint changes or the browse ends. Do not write one log line or submit one UI list for every identical callback. Still replace the internal snapshot with the copied latest objects on every callback.

Do not log App Secret, `md5Key`, QR content, PIN, token, or the raw output of `diagnose()`.

| Result | Required behavior |
| --- | --- |
| `BROWSE_SUCCESS` (`1`) | Replace the internal snapshot with the copied latest list and keep browsing active. Publish/log only when its stable content fingerprint changes. |
| `BROWSE_STOP` (`2`) | Mark browsing false. This can be the response to `stopBrowse()` or the SDK's normal automatic end of its roughly 30-second browse window. If no explicit stop was pending, treat it as normal completion, not cancellation or error. Preserve the last visible list and start a queued refresh only when the host requested one. |
| `BROWSE_TIMEOUT` (`3`) | Mark browsing false and show timeout. Preserve any non-empty final list. |
| `BROWSE_NETWORK_DISCONNECTED` (`4`) | Mark browsing false and show a network-change state. Do not relabel it as timeout. |
| `BROWSE_NO_LEBO_DEVICE` (`5`) | The network returned devices but none passed the Skill-free APK receiver channel check. Show `getSinkInstallGuide()`. |
| `BROWSE_MULTICAST_BLOCKED` (`6`) | No device response was received. Show network, multicast, subnet, and AP-isolation guidance. |
| `BROWSE_ERROR_AUTH` / `BROWSE_ERROR_AUTH_TIME` | Show authentication failure and verify `appId` plus platform `md5Key`; do not present an empty device list as the root cause. |

For a refresh while browsing, set `restartAfterStop` and a separate `stoppingForRefresh` guard, call `stopBrowse()` once, and wait for `BROWSE_STOP` before clearing the old selection/list and starting again. Further refresh taps while that callback is pending must not call `stopBrowse()` again. If `BROWSE_STOP` arrives with neither an explicit-stop flag nor `restartAfterStop`, record `sdk_window_complete` and remain idle. Do not issue overlapping stop/start calls.

## Lifecycle rules

Match the demo's separation between the long-lived device manager and short-lived UI:

- `onStart()` / `onResume()`: attach the UI observer and render the coordinator's current snapshot. A feature may make one explicit initial browse request, guarded so recreation does not repeatedly restart it.
- `onPause()` / `onStop()`: detach UI references if needed. Do not call `stopBrowse()`, `disconnect()`, or `unBindSdk()` merely because the UI is temporarily covered.
- QR camera pages, runtime permission screens, MediaProjection consent, settings, dialogs, and configuration changes must not tear down browsing or connection state.
- Explicit Stop/Refresh: stop or restart browse through the coordinator state machine.
- Final feature/process teardown: call `stopBrowse()`, stop active playback when owned by the feature, disconnect as required by product behavior, remove listeners, and call `unBindSdk()` only when the whole application no longer uses the SDK.

Do not keep a strong Activity reference in the coordinator. UI callbacks must be removable and posted to the main thread. Copy SDK lists before asynchronous diffing or adapter updates because the SDK may mutate its internal list while discovery continues.

## Selection and connection behavior

Preserve selection across harmless list updates with a stable UI key, preferably UID and otherwise IP plus port. The key is only for finding the corresponding object in the newest snapshot; always replace the selected reference with that newest object before `connect()`.

Expose these states separately: `unbound`, `binding`, `bound`, `browsing`, `connecting`, `connected`, and `casting`. Disable duplicate connect actions while connecting. Display `connectType` on success and both `what` and `extra` on disconnect/failure.

For Skill-free builds, receiver filtering is expected. The SDK loads the public receiver channel list and accepts a receiver when its reported App ID belongs to a channel whose `type` is `1`, which denotes an APK receiver channel. Channels with other types, DLNA-only devices, and entries without App ID metadata may be discovered internally but are filtered from the public list. Test with a known `type == 1` receiver when validating successful discovery, and use result `5` for the filtered-only case.

## QR and PIN paths

Camera decoding and SDK parsing are separate stages:

1. Confirm the final merged Manifest has `<application android:usesCleartextTraffic="true">`. QR and PIN parsing may fetch receiver metadata from a dynamic private-IP HTTP endpoint.
2. The camera Activity must return `RESULT_OK` and non-empty decoded text.
3. Pass QR text to `addQRCodeToLelinkServiceInfo(text, listener)` or PIN text to `addPinCodeToLelinkServiceInfo(text, listener)`. Both methods also retain a deprecated listener overload with the same lambda shape, so declare the variable as `IServiceInfoParseListener` or cast the lambda explicitly; a bare lambda is ambiguous in Java.
4. Log only stage names and numeric parse results, never the decoded text.
5. Connect only when `resultCode == PARSE_SUCCESS` and `serviceInfo != null`, using that exact returned object.
6. For `PARSE_NOT_OFFICIAL_SINK`, show the installation guide. Keep other parse errors in the parse callback domain. If logs also contain `Cleartext HTTP traffic ... not permitted` or the receiver App ID is missing, fix the Manifest first because the APK-channel decision lacks required metadata.

Opening or closing the camera Activity must not implicitly stop LAN discovery. If no SDK parse log appears, diagnose the camera result handoff before investigating SDK parsing.

## Minimum observable diagnostics

A generated integration must make the following events visible in debug logs or a diagnostic UI:

```text
bind result success=<true|false>
browse requested state=<...>
browse started modes=<...>
browse result code=<number> count=<number> repeated=<suppressed identical callbacks>
connect requested device=<redacted stable label>
connect result type=<number>
disconnect result what=<number> extra=<number>
qr decode result=<ok|cancel|empty>
qr/pin parse result code=<number> hasDevice=<true|false>
playback result callback=<name> what=<number> extra=<number>
```

These events distinguish a missing call, a filtered receiver, a network problem, a parse failure, a connection failure, and a playback failure. An empty UI without the corresponding callback code is not an acceptable implementation.
