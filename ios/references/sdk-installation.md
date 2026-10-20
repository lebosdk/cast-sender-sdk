# SDK installation

`ruby scripts/integrate_sdk.rb --project <X.xcodeproj> --target <App target>` makes these changes and nothing else. `--check` lists what is missing and exits 1. Rerunning is a no-op.

| Change | Why |
|---|---|
| Link `LeboSenderSDK/LBLelinkKit.xcframework` (Do Not Embed) | The SDK is a static library. |
| Link `MediaPlayer.framework` | The only system framework the static library does not auto-link. |
| `OTHER_LDFLAGS += -ObjC` | Categories and runtime-looked-up classes in the static library must be linked. |
| `NSLocalNetworkUsageDescription` | iOS 14+ local network permission prompt. |
| `NSBluetoothAlwaysUsageDescription` | Bluetooth discovers nearby official receivers that are not on the same Wi-Fi; they connect across networks. Without it iOS blocks Bluetooth scanning. |
| `NSBonjourServices += _leboremote._tcp` | Without it LAN search finds nothing and the SDK reports -1500. |
| `NSAppTransportSecurity.NSAllowsArbitraryLoads = true` | The SDK talks plain HTTP to LAN receivers and to the cross-network push server (`http://<IP>:7172/1/push`). Cross-network playback control and the cloud-mirror stop go through that push; without it they fail with `NSURLErrorDomain -1022` and the TV never stops. Remove `NSAllowsLocalNetworking`, `NSAllowsArbitraryLoadsInWebContent` and `NSAllowsArbitraryLoadsForMedia`: when any of them is present, iOS ignores `NSAllowsArbitraryLoads`. Tell the user App Store review may ask for a justification. |

If the target has no `INFOPLIST_FILE` (Xcode-generated Info.plist), the script creates `<target>/Info.plist` with only these keys and sets `INFOPLIST_FILE`; Xcode merges it with the generated keys.

Simulator and device both work for media push. Do not add OpenSSL (`libcrypto`) or AirPlay-related libraries; the free edition does not need them.

Import in Objective-C: `#import <LBLelinkKit/LBLelinkKit.h>`. In Swift: `import LBLelinkKit`.

Screen mirroring is wired separately by `integrate_mirror.rb`; see [screen mirroring](mirroring.md).
