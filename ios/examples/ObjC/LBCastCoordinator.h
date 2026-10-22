#import <Foundation/Foundation.h>
#import <LBLelinkKit/LBLelinkKit.h>

NS_ASSUME_NONNULL_BEGIN

/// 投屏协调者：持有鉴权、搜索、连接、播放，整个 App 只用一个
@interface LBCastCoordinator : NSObject

+ (instancetype)shared;

/// 当前可投的设备，每次搜索回调整体替换
@property (nonatomic, copy, readonly) NSArray<LBLelinkService *> *services;
/// 已连接时的设备，未连接为 nil
@property (nonatomic, strong, readonly, nullable) LBLelinkService *connectedService;
/// 唯一的连接对象，镜像时交给 LBMirrorController
@property (nonatomic, strong, readonly) LBLelinkConnection *connection;
/// 设备列表或连接状态变化
@property (nonatomic, copy, nullable) void (^onChange)(void);
/// 需要展示安装引导（-1700 / -1702 / -2800）
@property (nonatomic, copy, nullable) void (^onInstallGuide)(NSDictionary *userInfo);
/// 其他错误：域 + 错误码，界面按需提示
@property (nonatomic, copy, nullable) void (^onError)(NSError *error);
/// 系统权限被拒（如本地网络），引导用户去设置里打开
@property (nonatomic, copy, nullable) void (^onPermissionDenied)(LBLelinkSystemPermissionsType type);
/// 播放状态
@property (nonatomic, copy, nullable) void (^onPlayStatus)(LBLelinkPlayStatus status);
/// 播放进度，单位秒，用于进度条
@property (nonatomic, copy, nullable) void (^onProgress)(NSInteger currentTime, NSInteger duration);
/// 视频列表当前播放的片源 ID，用于选集高亮
@property (nonatomic, copy, nullable) void (^onCurrentMediaId)(NSString *_Nullable mediaId);

/// 打开 SDK 日志，在 startWithAppId 之前调用；console：Xcode 控制台打印（SDK 默认开），file：保存到沙盒 Caches/LBLelinkKit（最多 10 MB，默认关）
- (void)enableLogConsole:(BOOL)console file:(BOOL)file;
/// 鉴权成功后开始搜索；因网络失败时，网络恢复或回到前台自动重新鉴权；注意：鉴权在后台线程执行
- (void)startWithAppId:(NSString *)appId secretKey:(NSString *)secretKey;
/// 连接搜索回调里给出的设备对象
- (void)connect:(LBLelinkService *)service;
/// 用电视上显示的投屏码查找设备，找到后自动连接；非乐播投屏 TV 版回调 onInstallGuide（-1702）
- (void)connectWithCastCode:(NSString *)castCode;
/// 用扫到的电视二维码字符串查找设备，找到后自动连接；非乐播投屏 TV 版回调 onInstallGuide（-1702）
- (void)connectWithQRCode:(NSString *)qrCode;
/// 推在线视频
- (void)playOnlineVideo:(NSString *)url;
/// 当前可用的播控，未连接为 nil；注意：开始推送后再查，每个按钮按对应的 can* 显示或隐藏
- (nullable LBCastCapability *)capability;

#pragma mark - 播控（按 capability 显示按钮）

/// 暂停，canPause
- (void)pause;
/// 继续，canPause
- (void)resumePlay;
/// 跳到指定位置，单位秒，canSeek
- (void)seekTo:(NSInteger)seconds;
/// 设置音量，范围 0 ~ 100，canVolume
- (void)setVolume:(NSInteger)value;
/// 设置倍速，rate 取 capability.rates 里的值，canRate
- (void)setPlaySpeed:(double)rate;
/// 推视频列表，从 startMediaId 开始播（nil 为第一集）；收端不支持列表返回 NO，改推单集
/// 注意：清晰度没有单独接口，在电视上切换；外层 item 设 mediaName，itemClarityArray 里每个子片源各设 mediaId / mediaURLString / clarityType，外层 mediaURLString 此时不生效
- (BOOL)playVideoList:(NSArray<LBLelinkPlayerItem *> *)items startMediaId:(nullable NSString *)startMediaId;
/// 选集：播指定片源，canSwitchItem
- (void)playMediaId:(NSString *)mediaId;
/// 选集：下一集，canSwitchItem
- (void)playNext;
/// 选集：上一集，canSwitchItem
- (void)playPrevious;
/// 停止推送，始终可用；注意：只停推送，镜像停止走 LBMirrorController
- (void)stop;

@end

NS_ASSUME_NONNULL_END
