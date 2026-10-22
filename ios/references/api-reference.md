# API 参考（媒体推送）

本文档对应当前 Skill 版本的公开发送端 API。已安装 `LBLelinkKit.xcframework` 里的头文件优先级最高；名称不一致时以头文件为准。

所有类都来自 `#import <LBLelinkKit/LBLelinkKit.h>`（Swift 为 `import LBLelinkKit`）。回调不保证在主线程，操作界面前先切回主线程。

## 1. 初始化

| 接口 | 说明 |
|---|---|
| `+ (BOOL)authWithAppid:secretKey:error:` | 同步网络请求，放在后台线程调用；返回 YES 后才能搜索。 |
| `+ enableLog:` | Xcode 控制台打印，**SDK 默认打开**。 |
| `+ enableLogFileSave:` | 保存日志到沙盒 `Library/Caches/LBLelinkKit`（最多 10 MB），同时打开云镜像日志（`Documents/dailyLogFile`）。和控制台打印互不影响。 |
| `+ enableLogToTarget:outputSEL:` | 日志回调给 App 自己处理，和 `enableLogFileSave:YES` 二选一，Skill 不使用。 |
| `+ (NSString *)diagnose` | 只读本地状态：版本、是否免费版、鉴权、appId、环境、渠道清单来源、最近一次搜索、当前连接。内容含 appId 和设备名。 |

## 2. 搜索：`LBLelinkBrowser`

| 接口 | 说明 |
|---|---|
| `delegate` | `LBLelinkBrowserDelegate` |
| `- searchForLelinkServiceOfType:` | 传 `LBLelinkServiceTypeLelink \| LBLelinkServiceTypeDlnaDMC \| LBLelinkServiceTypePublickNetwork`（局域网 + 跨网），调用 `stop` 前一直搜索。注意：第三方 App 传什么 SDK 都按全部类型搜索。 |
| `- enableSearchLelinkService:sourceStyle:onError:` | 传 `YES`、`LBLelinkServiceSourceStyleSearchBluetooth` 打开蓝牙搜索，在 `searchForLelinkServiceOfType:` 之前调用。**蓝牙搜索默认关闭**，不打开就发现不了不在同一 Wi-Fi 的官方收端。需要 Info.plist 有 `NSBluetoothAlwaysUsageDescription`。 |
| `- stop` | 只在用户主动停止或销毁时调用，页面消失时不要调。 |
| `- searchForLelinkServiceFormQRCode:onError:` | 解析扫到的电视二维码，**必须在子线程调用**（会阻塞）。结果从 `didFindLelinkService:fromSourceStyle:` 回调，`sourceStyle` 为 `LBLelinkServiceSourceStyleScanQRCode`。 |
| `- searchForLelinkServiceFormCastCode:callBlock:` | 解析电视上显示的投屏码，结果从 `didFindLelinkService:fromSourceStyle:` 回调，`sourceStyle` 为 `LBLelinkServiceSourceStyleInputCastCode`。 |
| `lelinkServices` | SDK 内部未过滤的列表，**不要读**，以代理回调为准。 |

代理方法（`lelinkBrowser:permissionsPolicyDenied:` **必须实现**，Swift 不实现编译不过）：

- `lelinkBrowser:permissionsPolicyDenied:`：系统权限（如本地网络）被拒，引导用户去设置里打开。
- `lelinkBrowser:didFindLelinkServices:`：当前可投的设备列表，会反复回调，每次整体替换界面列表。
- `lelinkBrowser:onError:`：搜索错误，回调后搜索继续。
- `lelinkBrowser:didFindLelinkService:fromSourceStyle:`：扫码 / 投屏码解析出的设备，只在 `sourceStyle` 是 `ScanQRCode` 或 `InputCastCode` 时自动连接；云端匹配等其他来源也会走这里，不要自动连。
- `lelinkBrowser:didFindLelinkServiceFromQRCode:`：**不要实现**。扫码时它和上一个回调都会触发，而且会重复回调，导致重复连接。

## 3. 连接：`LBLelinkConnection`

| 接口 | 说明 |
|---|---|
| `lelinkService`、`delegate` | 在 `connect` 前设置。 |
| `- connect` / `- connectToLelinkService:` | 传最近一次回调给出的那个 `LBLelinkService` 对象。 |
| `- disConnect` | 断开连接。 |
| `isConnected` | 是否已连接。 |

代理方法：`lelinkConnectionDidStartRetryConnect:`（**必须实现**，开始自动重连）、`lelinkConnection:didConnectToService:`（唯一的连接成功信号）、`lelinkConnection:disConnectToService:`、`lelinkConnection:onError:`。

## 4. 播放：`LBLelinkPlayer`

| 接口 | 说明 |
|---|---|
| `lelinkConnection`、`delegate` | **在 `lelinkConnection:didConnectToService:` 里、每次连接成功后**（包括重连）给 `lelinkConnection` 赋值。播放器在赋值时读取连接的内部通道；连接成功前赋值，`playWithItem:` 会报 -3003。 |
| `- playWithItem:` | 传 `LBLelinkPlayerItem`，设置 `mediaType` 和 `mediaURLString`（本地图片用 `mediaData`）。 |
| `- pause` / `- resumePlay` / `- seekTo:` / `- setVolume:` / `- stop` | 播控。 |
| `- setPlaySpeedWithRate:` | 仅在 `isSupportChangePlaySpeed` 为 YES 时调用。 |
| `- pushVideoList:validPeriod:startMediaId:` | 仅在 `canPushVideoList` 为 YES 时调用。 |
| `- canPlayMedia:` | 调 `playWithItem:` 前先判断。 |
| `- queryCastCapability` | 返回 `LBCastCapability`，未连接时为 nil。 |

`LBCastCapability`（只读）：`canPause`、`canSeek`、`canVolume`、`canRate`、`rates`、`canSwitchItem`、`canDefinition`、`canPlayLocalMedia`。开始推送后查询，只显示它允许的按钮。它已经按「收端能力」和「当前内容形态」（镜像 / 图片 / 音频 / 视频 / 视频列表）取过交集。

能力与接口对照（`LBCastCoordinator` 已封装同名方法）：

| 能力 | 显示条件 | 接口 |
|---|---|---|
| 暂停 / 继续 | `canPause` | `pause` / `resumePlay` |
| 进度拖动 | `canSeek`（音频、视频为 YES） | `seekTo:`（秒）；进度来自 `lelinkPlayer:progressInfo:` 的 `currentTime` / `duration` |
| 音量 | `canVolume` | `setVolume:`（0 ~ 100），或 `addVolume` / `reduceVolume` |
| 倍速 | `canRate`，档位取 `rates` | `setPlaySpeedWithRate:[player playSpeedRateTypeWithRate:rate]` |
| 视频列表选集 | `canSwitchItem`（推视频列表后才可能为 YES） | 先 `pushVideoList:validPeriod:startMediaId:`，再 `playVideoListToMediaId:` / `playNextMediaInVideoList` / `playPrevMediaInVideoList`；当前集来自 `lelinkPlayer:currentMediaId:` |
| 清晰度 | `canDefinition`（推视频列表后才可能为 YES） | 没有单独接口，在电视上切换，手机端只显示提示。推列表时外层 item 设 `mediaName`；`itemClarityArray` 里每个子片源各设 `mediaId`、`mediaURLString`、`clarityType`（`Std` / `High` / `Super`），可选 `pixelWidth` / `pixelHeight`。有子片源时外层 `mediaURLString` 不会发给电视；没有子片源时外层 item 就是唯一片源 |
| 停止 | 始终显示 | `stop`，只停推送 |
| 投本机文件 | `canPlayLocalMedia`（跨网为 NO） | 不是播控按钮；为 NO 时隐藏本机文件入口 |

代理方法：`lelinkPlayer:playStatus:`（`Loading`、`Playing`、`Pause`、`Stopped`、`Commpleted`、`Error`，可能重复回调）、`lelinkPlayer:progressInfo:`、`lelinkPlayer:onError:`。

媒体类型：`LBLelinkMediaTypeVideoOnline`、`AudioOnline`、`PhotoOnline`、`PhotoLocal`、`VideoLocal`、`AudioLocal`。本地视频和音频需要 App 自己起本地 HTTP 服务提供文件地址。

## 5. 镜像：`LBLelinkMirrorEngine`（`#import <LBReplayAppKit/LBReplayAppKit.h>`）

| 接口 | 说明 |
|---|---|
| `+ shareInstance` | 单例。 |
| `delegate` | `LBLelinkMirrorEngineDelegate`，**14 个方法全部必须实现**（协议里没有 `@optional`，Swift 少一个就编译不过）。 |
| `- setAppGroupId:` | 启动时设置，与录屏扩展相同；`LBLelinkKit` 也要 `setAppGroupId:`。 |
| `- addMirrorDeviceWithConnection:` | 传已连接的 `LBLelinkConnection`。成功回调 `mirrorAddMirrorDeviceSucceedConnection:mirrorStype:`，之后再弹系统录屏选择框；免费版非官方收端回调 `mirrorAddMirrorDeviceFailureConnection:error:`，错误码 -2800。 |
| `- stopExtensionApp` | 结束录屏扩展。只发普通停止，**跨网镜像电视不会退出**，见下一行。 |
| `LBLelinkPlayer - cloudMirrorExitMode:` | 跨网（云）镜像结束时先调，传 `LBLelinkCloudMirrorExitModeActive`，电视才退出。必须用已绑定该连接的播放器（`connection.lelinkService.lelinkPlayer`），不要新建。 |
| `- cleanMirrorDevice` | 停止后清除镜像设备信息。 |
| `- pauseMirror` / `- resumeMirror` | 暂停 / 恢复镜像。 |

关键代理方法：`mirrorAddMirrorDeviceSucceedConnection:mirrorStype:`、`mirrorAddMirrorDeviceFailureConnection:error:`、`mirrorOnError:mirrorStype:`、`mirrorStateMirroring:mirrorStype:`、`mirrorMirrorDeviceDisConnectConnection:mirrorStype:`。`mirrorStype` 区分局域网（`LBLelinkMirrorStypeLANLelink`）和跨网（`LBLelinkMirrorStypeInternetYouMe`，实际走网易或腾讯）。

录屏扩展端：`LBLelinkMirrorExtension`（`#import <LBReplayKitExtension/LBReplayKitExtension.h>`），在 `SampleHandler` 里依次 `setAppGroupId:`、`startMirror`，并转发 `paused` / `resumed` / `finished` / `processSampleBuffer:withType:`。模板见 `examples/Mirror/SampleHandler.m`。
