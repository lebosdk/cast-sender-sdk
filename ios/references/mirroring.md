# Screen mirroring

Mirroring sends the phone screen to the TV through a Broadcast Upload Extension. It works on a real device only (the system broadcast extension does not run in the simulator) and needs a signing team that can register an App Group.

Integrate media push first (`integrate_sdk.rb`, coordinator, credentials). Mirroring reuses its `LBLelinkConnection`.

## Wiring the project

`ruby scripts/integrate_mirror.rb --project <X.xcodeproj> --target <App target> [--team <ID>] [--app-group <group.xxx>] [--extension <name>]`

| Default | Value |
|---|---|
| Extension target | `LeboBroadcast`, bundle ID `<App bundle ID>.LeboBroadcast` |
| App Group | `group.<App bundle ID>`; pass `--app-group` when the bundle ID contains `$(...)` |
| Signing team | The App's `DEVELOPMENT_TEAM`; pass `--team` when it is empty |

It creates the extension (`SampleHandler`, `Info.plist` with `com.apple.broadcast-services-upload`, entitlements), links and embeds the mirror frameworks in both targets, adds the App Group to both entitlements, and writes `<App dir>/LeboMirrorConfig.h` with `LeboMirrorAppGroupId` and `LeboMirrorExtensionBundleId`. `--check` lists what is missing; rerunning must print `镜像已接入，无需改动`.

Embedded dynamic frameworks (Embed & Sign in the App): `NERtcSDK`, `NERtcReplayKit`, `TXFFmpeg`, `TXSoundTouch`. The extension loads `NERtcReplayKit` from the App's `Frameworks` directory. Do not embed frameworks inside the extension.

If automatic signing cannot register the App Group, ask the user to add it to the team in the Apple Developer portal (Identifiers > App Groups) and to enable it on both App IDs; do not change signing to manual.

## App code

Start from `examples/Mirror/LBMirrorController.h/.m`:

1. After authentication, call `[[LBMirrorController shared] setup]` once. It sets the App Group on `LBLelinkKit` and `LBLelinkMirrorEngine` and becomes the engine delegate.
2. When the user taps Mirror and the push coordinator is connected, call `startWithConnection:` with the coordinator's connected `LBLelinkConnection`.
3. On `mirrorAddMirrorDeviceSucceedConnection:` the controller shows the system broadcast picker limited to `LeboMirrorExtensionBundleId`. The user taps "Start Broadcast"; the extension then starts mirroring.
4. `mirrorStateMirroring:` reports the mirroring state; `stop` ends the broadcast.
5. Stopping a cross-network (cloud) mirror must send `[player cloudMirrorExitMode:LBLelinkCloudMirrorExitModeActive]` first, on the player already bound to the mirroring connection (`connection.lelinkService.lelinkPlayer`); otherwise the TV keeps showing the mirror. `stopExtensionApp` alone only sends a plain stop. The controller does this in `stop` and when the user stops the broadcast from Control Center (`mirrorDidBroadcastExtensionStopedMirrorStype:`), then calls `cleanMirrorDevice`. Do not create a new `LBLelinkPlayer` for it: setting `lelinkConnection` rebinds the connection to that player.

`LBLelinkMirrorEngineDelegate` has no `@optional` section: all 14 methods are required. Objective-C only warns when one is missing; Swift does not compile.

## Extension code

`integrate_mirror.rb` generates `SampleHandler.m` from `examples/Mirror/SampleHandler.m` with the App Group filled in. Do not add other work to the extension: iOS limits a broadcast extension to about 50 MB of memory.

## Free-edition behaviour

- Mirroring is allowed only to the official Lebo TV receiver app. A connection to anything else is rejected before mirroring with -2800 (`LBLelinkConnectionErrorDomain`) and the install guide in `userInfo`.
- Cross-network mirroring uses NetEase or Tencent, chosen by the server. If the server ever assigns Zego, the extension ends the broadcast with error `errorInfo` "Skill free edition unsupported Zego".
- Only one connection at a time: connecting from another `LBLelinkConnection` disconnects the mirroring connection.

## Troubleshooting

| Symptom | Check |
|---|---|
| Picker does not list the extension | The extension is embedded in the App (`PlugIns/<name>.appex`) and signed with the same team; reinstall the App |
| Broadcast starts and stops at once | Both targets carry the same App Group, and `LeboMirrorConfig.h` matches the extension's `kLeboAppGroupId` |
| `dyld: Library not loaded: @rpath/NERtcReplayKit.framework` in the extension | `NERtcReplayKit` is embedded in the App and the extension's `LD_RUNPATH_SEARCH_PATHS` contains `@executable_path/../../Frameworks` |
| Cross-network mirror stops on the phone but the TV does not exit | The App's ATS allows `NSAllowsArbitraryLoads` with no `NSAllowsLocalNetworking` beside it (the stop goes over `http://<IP>:7172/1/push`; a blocked request logs `-1022`); `cloudMirrorExitMode:` is sent; a player is bound to the connection (bind it in `didConnectToService`) |
| Mirroring fails for a non-official receiver | Expected in the free edition; show the install guide |
