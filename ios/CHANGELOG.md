# Changelog

## 0.2.4

- Playback controls: after push works, the Skill lists every control the SDK supports (pause/resume, seek, volume, rate, video-list episodes, definition) in a numbered menu and builds the ones the user picks; stop is always added. Each control follows its `LBCastCapability` flag.
- `LBCastCoordinator` wraps `pause`, `resumePlay`, `seekTo:`, `setVolume:`, `setPlaySpeed:`, `playVideoList:startMediaId:`, `playMediaId:`, `playNext`, `playPrevious`, `stop`, and adds `onProgress` / `onCurrentMediaId`.
- `api-reference.md` maps each capability to its API; acceptance now checks that picked controls exist.
- The control menu is shown once the push code is written, without waiting for a TV; item 6 says definition is switched on the TV.
- `api-reference.md` spells out the definition list: `clarityType` goes on each sub-source, and the outer `mediaURLString` is not sent when sub-sources exist.
- `LBCastCoordinator capability` logs the `queryCastCapability` result required by acceptance.
- Connection methods: the same step shows a menu for cast-code input and QR scan (needed to reach a TV outside the Wi-Fi for cloud push and cloud mirroring). `LBCastCoordinator connectWithQRCode:` and the `LBQRScanViewController` example are added; `integrate_sdk.rb --camera` adds `NSCameraUsageDescription`.
- Fix: `LBMirrorController` also calls `cleanMirrorDevice` when the broadcast is stopped from Control Center, as `mirroring.md` already described.
- `SampleHandler` template implements `hostAppReceiveHeartBeat` and `lelinkMirrorExtensionMirroringProvider:` (empty; the SDK rejects Zego itself), removing the missing-protocol-method warnings.
- Fix: `integrate_mirror.rb --app-group` replaces the old App Group in both entitlements and in the extension's `SampleHandler.m` instead of appending; without `--app-group` it keeps the last value from `LeboMirrorConfig.h`.
- `onboard.py` records the Bundle ID in the credentials file and `--check` / reuse stop when the target's Bundle ID differs (otherwise auth fails with 402).
- Scope 2 or 3 verifies with the device build without signing; the mirror frameworks are device-only, so the simulator build fails by design.
- Scope menu: a new integration asks for `1. 仅媒体推送`, `2. 仅手机屏幕镜像`, or `3. 媒体推送 + 手机屏幕镜像` (no timeout) instead of integrating push only unless mirroring was asked for. Mirroring-only keeps the SDK wiring and coordinator but skips push UI and the playback menu.
- Logs: the same step shows a menu for console printing and saving log files; `LBCastCoordinator enableLogConsole:file:` wraps `enableLog:` / `enableLogFileSave:`. The free-edition SDK masks `secretKey` in the auth-failure log (first 4 characters only), since logs can now be saved to files.
- `LBCastCoordinator` auto-connects only devices whose `sourceStyle` is cast code or QR scan; it does not implement `didFindLelinkServiceFromQRCode:`, which fires again for every scan.

## 0.2.3

- The SDK is no longer shipped inside the Skill: `obtain_sdk.py` downloads `https://lebotob.hpplay.cn/sdk/iOS/Release/ios-sender-sdk.zip` by default; `--local` still installs a supplied package. `--cdn` is kept as a no-op for older instructions.

## 0.2.2

- Switch to production: `onboard.py` registers on `https://openplat.hpplay.cn`; `sdk/ios-sender-sdk.zip` is the production package (92717).
- Fix: `integrate_sdk.rb` and `integrate_mirror.rb` read files as UTF-8, so an Info.plist with Chinese text no longer fails when the terminal locale is not UTF-8.

## 0.2.1

- Fix: `integrate_sdk.rb` now sets `NSAllowsArbitraryLoads` and removes `NSAllowsLocalNetworking` (which makes iOS ignore it). Cross-network control, including the cloud-mirror stop, is pushed to `http://<IP>:7172` and was blocked by ATS (`-1022`).
- Fix: stopping a cross-network mirror now makes the TV exit. `LBMirrorController` sends `cloudMirrorExitMode:LBLelinkCloudMirrorExitModeActive` on the bound player before `stopExtensionApp` (also when the broadcast is stopped from Control Center), then calls `cleanMirrorDevice`; `SampleHandler` calls `stopMirror` in `broadcastFinished`.

## 0.2.0

- Screen mirroring: bundled SDK now carries the mirror frameworks and slimmed NetEase / Tencent SDKs; `integrate_mirror.rb` creates the broadcast extension, App Group, linking, and embedding; `LBMirrorController` and `SampleHandler` examples; `references/mirroring.md`.
- The free-edition SDK no longer ships QUIC.
- Discovery of official receivers outside the Wi-Fi: `integrate_sdk.rb` adds `NSBluetoothAlwaysUsageDescription`; the examples enable Bluetooth discovery (off by default in the SDK) and search LAN + cross-network types.
- `LBCastCoordinator` connects by cast code (`connectWithCastCode:`).

## 0.1.1

- Ship the SDK inside the Skill (`sdk/ios-sender-sdk.zip`, free edition 92717, media push only); `obtain_sdk.py` installs it by default. The CDN is now opt-in with `--cdn` because the iOS package is not published there.

## 0.1.0

- First version, media push only: environment check, SDK download (CDN or local package), project wiring with xcodeproj, SMS onboarding ported from the Android Skill (`platformType = 2`), API and error-handling references, Objective-C coordinator and Swift sketch.
- Screen mirroring is not covered.
