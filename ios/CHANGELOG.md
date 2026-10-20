# Changelog

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
