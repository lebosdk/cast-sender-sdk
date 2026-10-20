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

/// 鉴权成功后开始搜索；注意：鉴权在后台线程执行
- (void)startWithAppId:(NSString *)appId secretKey:(NSString *)secretKey;
/// 连接搜索回调里给出的设备对象
- (void)connect:(LBLelinkService *)service;
/// 用电视上显示的投屏码查找设备，找到后自动连接；非乐播投屏 TV 版回调 onInstallGuide（-1702）
- (void)connectWithCastCode:(NSString *)castCode;
/// 推在线视频
- (void)playOnlineVideo:(NSString *)url;
/// 当前可用的播控，未连接为 nil
- (nullable LBCastCapability *)capability;

@end

NS_ASSUME_NONNULL_END
