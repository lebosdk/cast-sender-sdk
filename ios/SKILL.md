---
name: ios-sender-sdk
description: Integrate the HPPlay (Lebo) iOS sender SDK free edition into an existing Xcode app for discovering, connecting to, pushing media to, and mirroring the screen to the official Lebo TV receiver app. Use when implementing, testing, or reviewing iOS sender SDK media push or screen mirroring; not for receiver-side development or Android.
---

# iOS Sender SDK Integration (media push and screen mirroring)

Resolve every reference relative to this file. Treat the headers inside the installed `LBLelinkKit.xcframework` as the source of truth; if a name here differs from the installed headers, follow the headers.

Media push covers search, connect, push online or local media, playback control, capability query, and diagnostics; it also runs in the simulator. Screen mirroring adds a Broadcast Upload Extension, runs on a real device only, and needs a signing team that can register an App Group. The user picks which of the two to integrate (step 2). Both share the SDK wiring, credentials, and coordinator, so mirroring-only still goes through steps 3 to 7.

## Workflow

1. **Select the project.** Work only on an existing Xcode project; never create one. Run `python3 -I scripts/check_env.py --project-dir <dir>`. If it lists several App targets, ask the user to pick one with a numbered menu. Do not continue on missing items; show the printed install hints and stop.
2. **Classify the request.** If the target already links `LBLelinkKit` or calls `authWithAppid:`, this is an incremental change: read [incremental integration](references/incremental-integration.md) and reuse its SDK copy, credentials, and coordinator.
   **Scope.** For a new integration whose request does not already say push, mirroring, or both, show this numbered menu and wait for the answer (no timeout, no default); accept only `1`, `2`, or `3` and reprompt on anything else:
   `1. 仅媒体推送`, `2. 仅手机屏幕镜像`, `3. 媒体推送 + 手机屏幕镜像`.
   Tell the user under the menu: media push also runs in the simulator; mirroring runs on a real device only, adds a Broadcast Upload Extension target, and needs a signing team that can register an App Group. For an incremental change, the request decides the scope; do not show the menu.
3. **Read-only preflight** for a new integration, all before changing anything:
   - `python3 -I scripts/obtain_sdk.py --project-dir <dir> --check`
   - `ruby scripts/integrate_sdk.rb --project <X.xcodeproj> --target <target> --check`
   - `python3 -I scripts/onboard.py --project-dir <dir> --app-name "<application name>" --check` (skip when the project already passes a non-placeholder App ID and secret to `authWithAppid:secretKey:error:`)
   - Scope 2 or 3: `xcodebuild -project <X.xcodeproj> -target <target> -showBuildSettings | grep DEVELOPMENT_TEAM`; if it is empty, ask the user for a signing team now; that answer is the approval step 10 needs for setting it, so do not ask again (`integrate_mirror.rb --check` needs the SDK installed and wired, so it runs in step 10).
4. **Get the SDK** per [SDK artifact](references/sdk-artifact.md): `python3 -I scripts/obtain_sdk.py --project-dir <dir>` downloads and installs the SDK from the official CDN. Use `--local <zip or xcframework>` only when the user supplies another package. Never ask the user to download the SDK by hand.
5. **Wire the project** per [SDK installation](references/sdk-installation.md): `ruby scripts/integrate_sdk.rb --project <X.xcodeproj> --target <target>`. Rerun it; it must print `已接入，无需改动`.
6. **Credentials** per [onboarding](references/onboarding.md). Only when no reusable credential pair exists, run `python3 -I scripts/onboard.py --project-dir <dir> --app-name "<application name>" --confirm`. The SDK secret is the platform `md5Key`, never the platform `secret`.
7. **Write the code** per [API reference](references/api-reference.md) and [discovery and connection](references/discovery-connection.md): one long-lived coordinator owns auth, browser, connection, and player; authenticate before searching; connect only to a device from the latest browse or parse callback; start pushing only after `lelinkConnection:didConnectToService:`. Start from [examples](examples/README.md). For scope 2 copy the coordinator as is and use it for auth, search, and connect; just do not call its push or control methods from the UI.
8. **Connection methods, playback controls, and logs.** After the coordinator code is written and before the first build (do not wait for a TV), show the menus below so the user knows what the SDK supports, and build only what they pick. Skip a menu when the request already names those items (then build exactly those). Each menu accepts comma-separated numbers, `全部`, or `0` for none; reprompt on anything else.
   Always build, outside the menus: the LAN device list; for scope 1 or 3 also an online-video push entry and a stop button. Connection methods (every scope): `1. 投屏码输入`, `2. 扫码连接`. Tell the user that Bluetooth discovery is always on and not a menu item, but it only finds nearby TVs; to reach a TV outside the phone's Wi-Fi (cloud push and cloud mirroring) reliably, pick at least one of these two. Use `connectWithCastCode:` / `connectWithQRCode:`; for `2` also copy `examples/ObjC/LBQRScanViewController` and rerun `integrate_sdk.rb` with `--camera`, and pass `--camera` to every later `integrate_sdk.rb` run, including `--check`.
   Playback controls (scope 1 or 3 only):
   `1. 暂停/继续`, `2. 进度拖动`, `3. 音量`, `4. 倍速`, `5. 视频列表选集`, `6. 清晰度（在电视上切换，手机端只显示提示）`.
   Always add a stop button; it is not in the menu. Build UI only for the picked items, each shown only while its `capability` flag is YES (see the control table in [API reference](references/api-reference.md)). Items 5 and 6 only turn on after a video list is pushed, so they also need a list entry point in the App; say so when the user picks them. The stop button stops media push only; mirroring keeps its own stop sequence (step 10).
   Logs (every scope, for troubleshooting with Lebo): `1. 控制台打印`, `2. 保存日志文件`. Call `[cast enableLogConsole:file:]` before `startWithAppId:secretKey:` with the picked items (unpicked ones pass `NO`; the SDK prints to the console by default, so not picking `1` turns it off). Files go to the App sandbox `Library/Caches/LBLelinkKit` (max 10 MB); tell the user that is where to fetch them when reporting a problem.
9. **Handle errors** per [error handling](references/error-handling.md). Show the SDK's install guide for -1700 / -1702 / -2800; give network hints for -1701; never collapse them into an empty list.
10. **Mirroring (scope 2 or 3)** per [screen mirroring](references/mirroring.md): `ruby scripts/integrate_mirror.rb --project <X.xcodeproj> --target <target>` (add `--team` when the App has no signing team), then wire `examples/Mirror/LBMirrorController` to the coordinator's connection. Keep its stop sequence: for a cross-network mirror, call `cloudMirrorExitMode:LBLelinkCloudMirrorExitModeActive` on the player bound to the connection before `stopExtensionApp`, or the TV never exits. Ask the user before changing the signing team or App Group.
11. **Verify** per [acceptance](references/acceptance.md). Rerun the onboarding `--check` before every build when credentials are Skill-managed. Scope 1: build and run on the simulator at least. Scope 2 or 3: the mirror frameworks are device-only (arm64), so the simulator build fails by design; use the device build without signing instead. State what remains unverified without a receiver.

## Free-edition rules the code must respect

- Only the official Lebo TV receiver app ("乐播投屏 TV 版") is eligible. Other receivers are removed from search results and rejected on connect; this is expected, not a bug.
- Only one connection at a time: connecting a second `LBLelinkConnection` disconnects the previous one.
- Over a cross-network (non-LAN) connection, local media cannot be pushed; push a URL the TV can reach.
- Bluetooth discovery can surface nearby official receivers outside the LAN, so "only non-official receivers on the LAN" may still show devices.
- Mirroring to a non-official receiver is rejected with -2800 before the broadcast starts.
- ATS must be `NSAllowsArbitraryLoads = true` without `NSAllowsLocalNetworking`: cross-network control (including the mirror stop) is sent over plain HTTP to an IP address; `integrate_sdk.rb` sets this.
- `stopExtensionApp` alone does not end a cross-network mirror on the TV; `cloudMirrorExitMode:` must be sent first (also when the user stops the broadcast from Control Center).

## Boundaries

- Every binary confirmation uses `[y/n]` and accepts only `y` or `n`; reprompt on anything else and never treat silence as `y`.
- Never print, log, or put on a command line: passwords, verification codes, tokens, platform `secret`, or `md5Key`. The generated `SkillSdkConfig` and `LeboSenderSDK/skill-credentials.properties` must stay Git-ignored.
- Never overwrite a non-Skill `SkillSdkConfig`, an existing credential source, or an unrelated `Info.plist` key. The scripts only add what is missing.
- `+[LBLelinkKit diagnose]` contains the app ID and device names; review before sharing.
