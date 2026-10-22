# Error handling

Keep the domain and numeric code of every `NSError`; do not merge different failures into one empty state.

| Code | Domain / callback | Meaning | What the app shows |
|---|---|---|---|
| -1700 | `LBLelinkBrowserErrorDomain`, `lelinkBrowser:onError:` | Devices answered, none is the official Lebo TV app | Install guide |
| -1701 | `LBLelinkBrowserErrorDomain`, `lelinkBrowser:onError:` | No device answered within 10 s | Check Wi-Fi, local network permission, AP isolation |
| -1702 | `LBLelinkBrowserErrorDomain`, `lelinkBrowser:onError:` | QR / cast code points to a non-official receiver | Install guide; no device is delivered |
| -1300 | `LBLelinkBrowserErrorDomain` | No network | Network hint (no -1701 in this case) |
| -1009 and other `NSURLErrorDomain` codes | `authWithAppid:secretKey:error:` | Auth could not reach the server (no network, or "使用无线数据" not yet allowed on a China-region iPhone). No SDK feature works until auth succeeds | Network hint; authenticate again when the network becomes available or the App returns to the foreground |
| -1500 | `LBLelinkBrowserErrorDomain` | `NSBonjourServices` / `NSLocalNetworkUsageDescription` missing | Fix Info.plist (rerun `integrate_sdk.rb`) |
| -2800 | `LBLelinkConnectionErrorDomain`, `lelinkConnection:onError:` | Receiver is not the official app; no connection was attempted | Install guide |
| -3900 | `LBLelinkPlayerErrorDomain`, `lelinkPlayer:onError:` | Local media over a cross-network connection; nothing was sent | Ask for a URL the TV can reach |

Searching continues after -1700 / -1701 / -1702.

## Mirroring

| Callback | Meaning | What the app shows |
|---|---|---|
| `mirrorAddMirrorDeviceFailureConnection:error:` with -2800 | Receiver is not the official app | Install guide (same `userInfo` keys as below) |
| `mirrorAddMirrorDeviceFailureConnection:error:` other codes | The connection is not connected, or the receiver does not support mirroring | Reconnect, then retry |
| Broadcast ends with `errorInfo` "Skill free edition unsupported Zego" | Server assigned Zego, which the free edition does not ship | Report to Lebo; not fixable in the app |

## Install guide

-1700, -1702, and -2800 carry the guide in `error.userInfo`:

| Key | Value |
|---|---|
| `LBSkillInstallGuideURLKey` | H5 page with installation steps |
| `LBSkillInstallGuideTitleKey` | Title, e.g. "请先在电视上安装并打开乐播投屏 TV 版" |
| `LBSkillInstallGuideStepsKey` | `NSArray<NSString *>`, three steps; show them when the page cannot load |
| `LBSkillUserTipKey` | "仅支持连接乐播投屏 TV 端应用" |

The SDK never shows UI. Present the page in a web view or `SFSafariViewController`, falling back to the steps.
