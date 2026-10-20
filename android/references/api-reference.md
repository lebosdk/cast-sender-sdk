# Android Sender SDK API Reference

本文档对应当前 Skill 版本的公开发送端 API。最终 AAR 的方法签名和常量定义优先级最高；接入时如果 AAR 版本不同，应以 AAR 中的公开接口为准。

## 1. API 层次

| 类型 | 作用 |
| --- | --- |
| `LelinkSourceSDK` | 发送端高层单例，第三方 App 通常只使用这一层。 |
| `ILelinkSourceSDK` | SDK 服务代理接口；用于核对能力和实现版本差异。 |
| `LelinkPlayerInfo` | 一次媒体或镜像会话的参数。 |
| `LelinkServiceInfo` | 搜索、解析或历史记录返回的接收端信息。 |
| `ImageListInfo` | 图片列表和图片条目。 |
| `CastCapability` | 当前会话可用的播控能力。 |
| `SinkInstallGuide` | 官方接收端安装引导内容。 |

通常不要直接创建 `LelinkSourceSDK`，使用 `LelinkSourceSDK.getInstance()` 获取进程内单例。

## 2. 初始化和绑定

### 获取实例

```java
LelinkSourceSDK sdk = LelinkSourceSDK.getInstance();
```

### 设置初始化参数

```java
sdk.setSdkInitInfo(context, appId, appSecret);
sdk.setSdkInitInfo(context, appId, appSecret, oaid);
sdk.setSdkInitInfo(context, appId, appSecret, userId, appVersion, oaid);
```

| 参数 | 要求 |
| --- | --- |
| `context` | 使用 `Application` 或有效 Activity Context；建议传 `getApplicationContext()`。 |
| `appId` | 平台分配的应用标识。 |
| `appSecret` | 必须传平台 `md5Key`，绝不能传平台 `secret`；不得写入日志或提交到代码仓库。 |
| `oaid` | 可选设备标识。 |
| `userId` | 可选的宿主用户标识。 |
| `appVersion` | 可选宿主版本号。 |

在本 Skill 的自动申请结果中，平台响应的 `secret` 与 `md5Key` 是两个不同字段。SDK 参数虽然名为 `appSecret`，实际必须传平台返回的 `md5Key`。因此应使用生成的 `SkillSdkConfig.APP_SECRET`，不要传本地属性 `hpplay.appSecret`：

```java
sdk.setSdkInitInfo(
        context,
        SkillSdkConfig.APP_ID,
        SkillSdkConfig.APP_SECRET
).bindSdk();
```

### 绑定

```java
sdk.setBindSdkListener(success -> {
    if (success) {
        sdk.startBrowse();
    }
});
sdk.bindSdk();
```

也可以使用一次性绑定重载：

```java
sdk.bindSdk(context, appId, appSecret, listener);
sdk.bindSdk(context, appId, appSecret, oaid, listener);
sdk.bindSdk(context, appId, appSecret, userId, appVersion, oaid, listener);
```

相关状态和生命周期方法：

| 方法 | 说明 |
| --- | --- |
| `isBindSuccess()` | 查询当前是否绑定成功。 |
| `unBindSdk()` | 解除绑定；在应用不再使用 SDK 时调用。 |
| `bindOfChildProcess()` | 多进程场景下绑定子进程，仅在项目实际启用并检测到 SDK 多进程配置时使用。 |
| `setDebugMode(boolean)` | 开关调试日志。Release 不应无条件开启。 |
| `setDebugTimestamp(boolean)` | 日志中增加调试时间信息。 |
| `getSDKInfos(int key)` | 查询 SDK 信息，具体 key 以对应版本常量为准。 |
| `getAppID()` / `getAppSecret()` | 读取当前初始化值；不要输出 `getAppSecret()`。 |

## 3. 监听器

### 绑定监听

`IBindSdkListener.onBindCallback(boolean isBindSuccess)`：绑定完成后回调。只有 `true` 时才应启动搜索或连接。

### 搜索监听

```java
sdk.setBrowseResultListener((resultCode, devices) -> { ... });
```

回调类型是 `IBrowseListener`。常用结果：

| 常量 | 含义 |
| --- | --- |
| `BROWSE_SUCCESS` | 搜索结果可用。设备列表可能为空，仍需检查列表。 |
| `BROWSE_TIMEOUT` | 搜索超时。 |
| `BROWSE_STOP` | 搜索结束；既可能由宿主调用 `stopBrowse()` 触发，也可能是 SDK 约 30 秒搜索窗口自然结束。 |
| `BROWSE_NETWORK_DISCONNECTED` | 网络切换或断开。 |
| `BROWSE_NO_LEBO_DEVICE` | 收到过设备响应，但没有符合 `channel.type == 1` 的 APK 收端。 |
| `BROWSE_MULTICAST_BLOCKED` | 搜索期间没有收到设备响应，优先排查网络和组播。 |

搜索与连接的状态管理、生命周期和设备对象保留规则见 [discovery-connection.md](discovery-connection.md)。SDK 在一次搜索中可能高频重复返回完全相同的 `BROWSE_SUCCESS` 结果。生成的应用每次都要复制并替换内部最新对象，但日志和 UI 只记录首次、内容指纹变化和终止事件，并汇总被抑制的重复次数，不能逐条刷屏。所有非成功结果仍需保留各自数值语义，不能统一渲染成空列表。

### 连接监听

通过 `setConnectListener(IConnectListener)` 注册。主要回调：

- `onConnect(info, connectType)`：连接成功，可以开始媒体投屏。
- `onDisconnect(info, what, extra)`：断开或连接失败；必须同时判断 `what` 和 `extra`。
- `onReconnecting(info, connectType)`：重连中。
- `onReconnectSuccess(info, connectType)`：重连成功。

### 播放监听

推荐使用 `setNewPlayListener(INewPlayerListener)`；兼容旧接入可使用 `setPlayListener(ILelinkPlayerListener)`。两者只能由宿主统一管理，避免多个页面互相覆盖监听器。

播放回调包括：加载、开始、暂停、完成、停止、Seek 完成、信息、错误、音量和进度。`onStart` 是可重复的播放状态通知，同一视频会话中可能约每 30 秒再次出现，也会在暂停恢复或 seek 后出现；不得在其中重复创建会话资源、重复埋点“首次播放”或再次发起投屏。一次性初始化应绑定宿主自己的 cast session/request ID 并做幂等保护。`onError` 的错误域见 [error-handling.md](error-handling.md)。

## 4. 搜索和解析设备

### 局域网搜索

```java
sdk.startBrowse();
sdk.startBrowse(true, true); // useLelink, useDlna
sdk.stopBrowse();
```

普通接入由长期存活的设备协调器调用这些方法。不要在 Activity/Fragment 的 `onPause()` 或 `onStop()` 中自动 `stopBrowse()`；二维码相机、权限页面和系统授权界面会触发这些生命周期回调。刷新搜索时先请求停止，等待 `BROWSE_STOP` 后再启动，避免重叠的 stop/start。

`startBrowse(BrowserConfigBean)` 用于自定义搜索配置；配置对象字段以目标 AAR 的 `BrowserConfigBean` 为准。

### 二维码、投屏码和 NFC

宿主应用必须在最终合并 Manifest 的 `<application>` 上包含 `android:usesCleartextTraffic="true"`。扫码和投屏码解析会通过电视动态局域网 IP 的 HTTP `DnsTxtInfo` 接口补全设备 App ID 等元数据；若被 Android 明文流量策略拦截，APK 收端也可能因 App ID 为空而在连接阶段返回 `212010/212101`。

```java
IServiceInfoParseListener parseListener = (resultCode, info) -> {
    // Handle PARSE_SUCCESS and the remaining parse-domain codes.
};
sdk.addQRCodeToLelinkServiceInfo(qrUrl, parseListener);
sdk.addPinCodeToLelinkServiceInfo(pinCode, parseListener);
sdk.addNfcTagToLelinkServiceInfo(intent, parseListener);
```

`addQRCodeToLelinkServiceInfo` 和 `addPinCodeToLelinkServiceInfo` 同时保留了 `IServiceInfoParseListener` 与废弃 `IParceResultListener` 两个重载，两个接口的 lambda 形状相同。Java 中不能直接把未定类型的 lambda 作为第二个参数；必须像上例一样先声明 `IServiceInfoParseListener` 变量，或显式转换为该类型。只有 `PARSE_SUCCESS` 且 `LelinkServiceInfo` 非空时才调用 `connect(info)`。`PARSE_NOT_OFFICIAL_SINK` 不应重试连接，应展示 `getSinkInstallGuide()`。

高级解析入口：

```java
sdk.createLelinkSeviceInfo(parameter, parseListener);
sdk.createLelinkServiceInfoList(parameters, listParseListener);
```

`SinkParameterBean` 的字段由业务服务提供，不能用随机值替代。

## 5. 连接和设备记录

```java
sdk.connect(device);
sdk.disconnect(device);
List<LelinkServiceInfo> connected = sdk.getConnectInfos();
```

`device` 必须是当前一次搜索或解析回调返回的原对象，或设备列表刷新后按稳定 key 找到的最新对象，不能只根据名称、IP 重新构造。只有 `IConnectListener.onConnect` 表示连接成功；`connect()` 调用返回不代表已经连接。

Skill 免费版同一时间只维护一个连接；连接新设备前 SDK 会处理旧连接。宿主 UI 应以连接回调更新状态，不要仅根据 `connect()` 返回时间判断成功。

历史和收藏设备：

| 方法 | 说明 |
| --- | --- |
| `enableHistoryDevice(boolean)` | 开关历史设备能力。 |
| `setHistoryDeviceListener(listener)` | 设置历史设备回调。 |
| `getHistoryDeviceList(onlineType, netType)` | 查询历史设备。 |
| `removeHistoryDevice(list, deleteType)` | 删除部分或全部历史设备。 |
| `setFavoriteDeviceListener(listener)` | 设置收藏设备回调。 |
| `addFavoriteDevice(info)` | 添加收藏。 |
| `removeFavoriteDevice(list)` | 移除收藏。 |
| `getFavoriteDeviceList(onlineType, netType)` | 查询收藏。 |
| `setFavoriteDeviceAlias(info, alias)` | 修改收藏别名。 |

查询类型常量包括 `ALL_DEVICE`、`ONLINE_DEVICE`、`OFFLINE_DEVICE` 和 `LOCAL_DEVICE`；历史删除类型包括 `REMOVE_HISTORY_PART`、`REMOVE_HISTORY_ALL`。

## 6. 媒体投屏

### 直接 URL/路径

```java
sdk.startPlayMedia(urlOrPath, mediaType, isLocalMedia);
```

`mediaType` 使用 `MEDIA_TYPE_VIDEO`、`MEDIA_TYPE_AUDIO`、`MEDIA_TYPE_IMAGE` 或 `MEDIA_TYPE_MICRO_APP`。跨网设备不能使用发送端本地路径或 URI；必须提供接收端可访问的 HTTP(S) 地址。

### 参数对象

```java
LelinkPlayerInfo info = new LelinkPlayerInfo();
info.setLelinkServiceInfo(device);
info.setType(LelinkSourceSDK.MEDIA_TYPE_VIDEO);
info.setUrl(url);
sdk.startPlayMedia(info);
```

`LelinkPlayerInfo` 常用字段：

| 方法 | 说明 |
| --- | --- |
| `setLelinkServiceInfo(info)` | 指定目标设备。 |
| `setType(type)` | 设置媒体或镜像类型。 |
| `setUrl(url)` | 设置网络地址。 |
| `setLocalPath(path)` | 设置本地路径；跨网限制仍生效。 |
| `setLocalUri(uri)` | 设置本地 URI；按宿主权限提供可读授权。 |
| `setStartPosition(seconds)` | 设置起播位置。 |
| `setCastPwd(password)` | 设置接收端要求的连接密码。 |
| `setPlayList(list, id, period, head, tail)` | 设置视频列表。 |
| `setImageList(list, id, period)` | 设置图片列表。 |
| `setMediaAsset(asset)` | 补充媒体名称、时长等信息。 |

### 立即投屏

```java
sdk.startPlayMediaImmed(device, path, mediaType, isLocalMedia);
sdk.startPlayMediaImmed(device, uri, mediaType);
```

立即投屏绕过部分当前会话流程，适合明确指定目标设备的场景；仍需处理播放回调和错误码。

## 7. 图片和视频列表

### 视频列表

```java
sdk.appendPlayList(list, period, headDuration, tailDuration);
sdk.playDrama(dramaId);
sdk.playNextDrama();
sdk.playPreDrama();
sdk.clearPlayList();
```

### 图片列表

```java
sdk.appendImageList(imageList, period);
sdk.playImageWithKey(imageId);
sdk.playNextImage();
sdk.playPreImage();
sdk.clearImageList();
```

每个 `ImageListInfo.ImageItem` 应有稳定唯一的 `id` 和接收端可访问的 URL。投屏前检查 `isSupportImageList(device)`。`period` 的单位是秒；列表协议有效时长和接收端实际自动切图策略应以接收端版本验证为准。

## 8. 播控和能力查询

通用播控：

```java
sdk.pause();
sdk.resume();
sdk.seekTo(positionSeconds);
sdk.addVolume();
sdk.subVolume();
sdk.setVolume(percent);
sdk.stopPlay();
sdk.stopPlayByReason(reason);
```

调用 `seekTo` 前先检查当前会话能力。不同接收端/协议版本不保证回调 `onSeekComplete`：实测可能只再次回调 `onStart`。将 seek 作为异步请求，通过 `onPositionUpdate` 到达目标位置附近来确认结果，设置业务超时，并把 `onSeekComplete` 当作可用时的快速确认；不能仅因缺少该回调就判定失败或永久保持 loading。

视频/音频扩展播控：

```java
sdk.isSupportRate(device);
sdk.setRate(rate);
sdk.queryRate();
sdk.isSupportSubtitle(device);
sdk.setSubtitle(url);
sdk.isSupportTrack(device);
sdk.selectTrack(index);
sdk.isSupportSetRealVolume(device);
sdk.queryRealVolume();
sdk.setRealVolume(volume);
```

能力查询：

```java
CastCapability capability = sdk.queryCastCapability();
boolean canPlayLocal = sdk.canPlayLocalMedia(device);
boolean canPlayScreen = sdk.canPlayScreen(device);
```

`queryCastCapability()` 没有连接设备时返回 `null`。界面应根据 `canPause`、`canSeek`、`canVolume`、`canRate`、`canSwitchItem`、`canDefinition` 和 `canPlayLocalMedia` 决定是否显示控制项。

## 9. 图片缩放和反控

图片缩放：

```java
sdk.isSupportPhotoScale(device);
sdk.queryPhotoScale();
sdk.setPhotoScaleListener(listener);
sdk.setPhotoTransform(scale, translationX, translationY);
sdk.setPhotoMaxScale(maxScale);
```

反控功能：

```java
sdk.isSupportReverseControl(device);
sdk.registerSinkKeyEvent();
sdk.setSinkKeyEventListener(listener);
sdk.unregisterSinkKeyEvent();
sdk.registerSinkTouchEvent();
sdk.setSinkTouchEventListener(listener);
sdk.unregisterSinkTouchEvent();
```

反控需要接收端支持、系统权限和宿主 UI 配合；不应默认展示入口。

## 10. 镜像、网页投屏和录屏

如果用户已明确要求媒体推送、实时镜像，或要求在现有能力上新增其中一种能力，直接以该请求确定范围，不再展示选择菜单。只有首次完整集成且范围仍不明确时，才在当前终端展示编号菜单：`1. 仅媒体推送（默认）`、`2. 仅手机屏幕实时镜像`、`3. 媒体推送 + 手机屏幕实时镜像`。只接受 `1`、`2` 或 `3`，其他输入重新提示。等待 30 秒仍未选择时采用选项 `1`，并告知用户已使用默认项。选项 `1` 不加入镜像专属权限、MediaProjection、采集、音频、通知和前台服务逻辑；选项 `2` 不实现媒体 URL 推送及其播放控制；选项 `3` 实现两种能力。该菜单是功能范围选择，不使用 `[y/n]`。

镜像入口：

```java
sdk.startMirror(playerInfo);
sdk.startDlnaMirror(playerInfo);
sdk.stopPlay();
sdk.isMirroring();
```

普通第三方应用必须走 MediaProjection 授权流程。`LelinkPlayerInfo.useSystemMirrorCapture` 的默认值是 `false`，普通应用应保持未设置或明确设为 `false`：

```java
LelinkPlayerInfo playerInfo = new LelinkPlayerInfo();
playerInfo.setLelinkServiceInfo(connectedDeviceFromOnConnect);
playerInfo.useSystemMirrorCapture(false); // 普通应用；也可以不调用，默认即为 false
sdk.startMirror(playerInfo);
```

不要为了免弹授权框或简化权限处理而调用 `useSystemMirrorCapture(true)`。该值会让 SDK 跳过普通应用的 MediaProjection 授权路径，通常会导致普通应用镜像失败；只有已确认宿主是系统应用、具备 SDK 支持的系统采集路径，并且用户明确要求该集成时才可设为 `true`。不能仅凭设备归属、平台签名、已授予运行时权限或期望隐藏授权框来推断可使用系统采集模式。

镜像相关配置包括分辨率、码率、旋转、音频采集、镜像通知、4K/H265/SRT 能力查询等。普通应用的镜像必须单独处理 MediaProjection 授权、音频和前台服务权限，不能按 URL 投屏流程处理。

网页投屏入口：

```java
sdk.startWebPresentationPreview(context, url, params);
sdk.startWebPresentationMirror(info, context, url, params);
sdk.stopWebPresentationPreview();
sdk.stopWebPresentation();
sdk.isWebPresentationPreviewOnly();
sdk.isWebPresentationRunning();
```

网页预览不连接接收端；升级为正式投屏后使用 `stopWebPresentation()`。触摸分发、预览 Surface、自动全屏和 WebView 操作通过对应 `setWebPresentation*` 方法完成。

录屏入口：

```java
sdk.startScreenRecord(recordConfig, listener);
sdk.pauseScreenRecord();
sdk.resumeScreenRecord();
sdk.stopScreenRecord();
sdk.isScreenRecording();
sdk.isScreenRecordPaused();
sdk.getScreenRecordDuration();
```

这些高级能力不属于基础 Skill 集成，只有宿主明确需要时才启用。

## 11. 外部音视频帧

```java
sdk.enableExternalAudio();
sdk.updateAudioData(data, audioFrame);
sdk.updatePCMData(sampleRate, channel, format, data, offset, length);
sdk.disableExternalAudio();

sdk.enableExternalVideo();
sdk.updateVideoData(data, videoFrame);
sdk.disableExternalVideo();
```

调用方必须保证帧格式、时间戳、线程和生命周期符合目标 SDK 版本，否则可能造成编码失败或播放异常。不要在普通 URL 投屏中调用这些入口。

## 12. 透传、日志和诊断

```java
sdk.setSendPassCallback(callback);
sdk.setPassThroughListener(listener);
sdk.setLogCallback(callback);
sdk.enableLogCache(true);
String logDir = sdk.getLogDir();
String diagnosis = sdk.diagnose();
```

`diagnose()` 只读取本地状态，但可能包含 App ID、设备名称、包名和连接信息。上传前必须脱敏。日志上传和反馈接口需由宿主提供用户授权和隐私说明。

## 13. 常量速查

| 类别 | 常量 |
| --- | --- |
| 媒体类型 | `MEDIA_TYPE_VIDEO`、`MEDIA_TYPE_AUDIO`、`MEDIA_TYPE_IMAGE`、`MEDIA_TYPE_MICRO_APP` |
| 镜像分辨率 | `RESOLUTION_HIGH`、`RESOLUTION_MIDDLE`、`RESOLUTION_AUTO` |
| 镜像码率 | `BITRATE_HIGH`、`BITRATE_MIDDLE`、`BITRATE_LOW` |
| 镜像数据通道 | `MIRROR_DATA_TCP_CHANNEL`、`MIRROR_DATA_LELINK_CHANNEL`、`MIRROR_DATA_SRT_CHANNEL` |
| 播放速度 | `PLAYBACK_SPEED1` 至 `PLAYBACK_SPEED6` |
| 设备筛选 | `ALL_DEVICE`、`ONLINE_DEVICE`、`OFFLINE_DEVICE`、`LOCAL_DEVICE` |
| 历史删除 | `REMOVE_HISTORY_PART`、`REMOVE_HISTORY_ALL` |

完整错误码见 [error-handling.md](error-handling.md) 以及目标 SDK AAR 中实际发布的公开常量；
集成时应以已安装 SDK 的接口和常量为准。

## 14. 释放顺序

建议在宿主的应用级控制器中执行：

1. 停止搜索：`stopBrowse()`。
2. 停止当前媒体或镜像：`stopPlay()`；网页投屏使用对应 `stopWebPresentation*()`。
3. 断开当前设备：`disconnect(info)`。
4. 解除 SDK 绑定：`unBindSdk()`，仅在整个应用不再使用 SDK 时调用。

页面销毁不等于 SDK 生命周期结束。若 SDK 由多个页面共享，页面只应移除自身 UI 引用，不要擅自解除全局绑定。

## 15. 其他公开 API 索引

下列入口属于可选或场景专用能力。它们仍是公开 API，但不建议在基础 URL/图片列表接入中默认开启。

| 能力 | 公开入口 | 说明 |
| --- | --- | --- |
| 权限/来源配置 | `setPermissionMode(mode, tsn)`、`setSourceID(id)`、`setConnectDeviceReport(...)` | 对接特定平台权限、来源标识或连接上报策略；需要平台参数。 |
| 设备在线检测 | `startOnlineCheck(listener, infos)` | 批量检查设备在线状态，结果异步返回。 |
| 防骚扰验证 | `sendHarassVerifyNum(verifyNum)` | 连接流程要求验证码时使用，处理对应连接回调。 |
| 一键投屏/镜像 | `easyPush(container)`、`easyMirror(container)`、`setEasyCastListener(listener)`、`dismissBrowserUI()` | 使用 SDK 自带设备列表 UI；宿主不需要自定义搜索页面时使用。 |
| 投屏码和短链生成 | `createPinCode(listener)`、`createShortUrl(listener)` | 生成供其他设备连接的业务数据，依赖云端服务。 |
| DLNA 单图 | `startPlayDlnaImage(...)`、`updateDlnaImage(...)`、`stopPlayDlnaImage()` | 单张图片持续投屏；与图片列表 API 的能力判定不同。 |
| 透传 | `setSendPassCallback(...)`、`setPassThroughListener(...)`、`setOption(...)`、`getOption(...)` | 发送或接收协议扩展消息；必须使用双方约定的 option 和数据格式。 |
| 搜索扩展 | `setBleBrowseStateListener(...)`、`setSearchBannerDataCallback(...)` | 蓝牙搜索状态或搜索页扩展数据。 |
| 收藏/历史高级配置 | `startBrowseHistory(...)`、`setHistoryDeviceListener(...)`、`setFavoriteDeviceListener(...)` | 需要宿主自行处理在线/离线筛选和删除结果。 |
| 镜像 UI 与水印 | `setMirrorChangeListener(...)`、`setWatermarkInfo(...)`、`setWatermarkVisible(...)`、`setMirrorScreenSecret(...)` | 镜像状态、水印和屏幕安全配置。 |
| 镜像通道和能力 | `enableMultiChannel(...)`、`isSupportMultiChannel(...)`、`switchMirror(...)`、`isSinkMirrorSupport4K()`、`isSinkMirrorSupportH265()`、`isSinkSupportSrt()` | 仅在镜像协议和接收端版本满足条件时使用。 |
| 外部采集/录制 | `registerDlnaMirrorCapture(...)`、`startRecord(...)`、`startScreenRecord(...)` | 外部采集或屏幕录制，需额外权限和生命周期管理。 |
| 日志和反馈 | `enableLogCache(...)`、`uploadLog(...)`、`getLogDir()`、`setLogCallback(...)` | 需要隐私授权；上传前脱敏。 |
| 临时限制/云投 | `isSupportTempRestrict(...)`、`enableTempRestrict(...)`、`disableCloudCast(...)`、`enableCloudMultiCast(...)` | 由平台策略控制，不应在普通业务中自行切换。 |
| 网页投屏交互 | `runOnWebPresentationWebView(...)`、`setWebPresentationPreviewSurface(...)`、`clearWebPresentationPreviewSurface(...)`、`setWebPresentationAutoFullscreen(...)`、`dispatchTouchToWebPresentation(...)` | 配合网页预览或网页投屏的 WebView、Surface 和触摸事件。 |

上述方法的参数对象和回调接口应以最终 SDK 的 JavaDoc/源码为准。Skill 只规定调用边界，不替业务方定义平台专用参数。
