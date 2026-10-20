---
name: ios-sender-sdk
description: Integrate the HPPlay (Lebo) iOS sender SDK free edition into an existing Xcode app for discovering, connecting to, pushing media to, and mirroring the screen to the official Lebo TV receiver app. Use when implementing, testing, or reviewing iOS sender SDK media push or screen mirroring; not for receiver-side development or Android.
---

# iOS Sender SDK Integration (media push and screen mirroring)

Resolve every reference relative to this file. Treat the headers inside the installed `LBLelinkKit.xcframework` as the source of truth; if a name here differs from the installed headers, follow the headers.

Media push covers search, connect, push online or local media, playback control, capability query, and diagnostics; it also runs in the simulator. Screen mirroring adds a Broadcast Upload Extension, runs on a real device only, and needs a signing team that can register an App Group. Integrate mirroring only when the user asks for it, and always on top of a working media-push integration.

## Workflow

1. **Select the project.** Work only on an existing Xcode project; never create one. Run `python3 -I scripts/check_env.py --project-dir <dir>`. If it lists several App targets, ask the user to pick one with a numbered menu. Do not continue on missing items; show the printed install hints and stop.
2. **Classify the request.** If the target already links `LBLelinkKit` or calls `authWithAppid:`, this is an incremental change: read [incremental integration](references/incremental-integration.md) and reuse its SDK copy, credentials, and coordinator.
3. **Read-only preflight** for a new integration, all before changing anything:
   - `python3 -I scripts/obtain_sdk.py --project-dir <dir> --check`
   - `ruby scripts/integrate_sdk.rb --project <X.xcodeproj> --target <target> --check`
   - `python3 -I scripts/onboard.py --project-dir <dir> --app-name "<application name>" --check` (skip when the project already passes a non-placeholder App ID and secret to `authWithAppid:secretKey:error:`)
4. **Get the SDK** per [SDK artifact](references/sdk-artifact.md): `python3 -I scripts/obtain_sdk.py --project-dir <dir>` downloads and installs the SDK from the official CDN. Use `--local <zip or xcframework>` only when the user supplies another package. Never ask the user to download the SDK by hand.
5. **Wire the project** per [SDK installation](references/sdk-installation.md): `ruby scripts/integrate_sdk.rb --project <X.xcodeproj> --target <target>`. Rerun it; it must print `已接入，无需改动`.
6. **Credentials** per [onboarding](references/onboarding.md). Only when no reusable credential pair exists, run `python3 -I scripts/onboard.py --project-dir <dir> --app-name "<application name>" --confirm`. The SDK secret is the platform `md5Key`, never the platform `secret`.
7. **Write the code** per [API reference](references/api-reference.md) and [discovery and connection](references/discovery-connection.md): one long-lived coordinator owns auth, browser, connection, and player; authenticate before searching; connect only to a device from the latest browse or parse callback; start pushing only after `lelinkConnection:didConnectToService:`. Start from [examples](examples/README.md).
8. **Handle errors** per [error handling](references/error-handling.md). Show the SDK's install guide for -1700 / -1702 / -2800; give network hints for -1701; never collapse them into an empty list.
9. **Mirroring (only when requested)** per [screen mirroring](references/mirroring.md): `ruby scripts/integrate_mirror.rb --project <X.xcodeproj> --target <target>` (add `--team` when the App has no signing team), then wire `examples/Mirror/LBMirrorController` to the push coordinator's connection. Keep its stop sequence: for a cross-network mirror, call `cloudMirrorExitMode:LBLelinkCloudMirrorExitModeActive` on the player bound to the connection before `stopExtensionApp`, or the TV never exits. Ask the user before changing the signing team or App Group.
10. **Verify** per [acceptance](references/acceptance.md). Rerun the onboarding `--check` before every build when credentials are Skill-managed. Build and run on the simulator at least; state what remains unverified without a receiver.

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
