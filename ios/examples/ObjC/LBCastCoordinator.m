#import "LBCastCoordinator.h"
#import <UIKit/UIKit.h>
#import <Network/Network.h>

@interface LBCastCoordinator () <LBLelinkBrowserDelegate, LBLelinkConnectionDelegate, LBLelinkPlayerDelegate>
@property (nonatomic, copy, readwrite) NSArray<LBLelinkService *> *services;
@property (nonatomic, strong, readwrite, nullable) LBLelinkService *connectedService;
@property (nonatomic, strong) LBLelinkBrowser *browser;
@property (nonatomic, strong) LBLelinkConnection *connection;
@property (nonatomic, strong) LBLelinkPlayer *player;
/// 鉴权用的凭据，startWithAppId 时保存
@property (nonatomic, copy) NSString *appId;
@property (nonatomic, copy) NSString *secretKey;
/// 鉴权状态：是否已成功 / 进行中 / 因网络失败等待重试，默认都是 NO
@property (nonatomic, assign) BOOL authorized;
@property (nonatomic, assign) BOOL authorizing;
@property (nonatomic, assign) BOOL waitingNetwork;
/// 网络监听，网络恢复时重新鉴权
@property (nonatomic, strong) nw_path_monitor_t pathMonitor;
@end

@implementation LBCastCoordinator

+ (instancetype)shared {
    static LBCastCoordinator *instance;
    static dispatch_once_t once;
    dispatch_once(&once, ^{ instance = [[LBCastCoordinator alloc] init]; });
    return instance;
}

- (instancetype)init {
    if (self = [super init]) {
        _services = @[];
        // 免费版只保留一个连接，整个 App 复用这一个连接对象
        _connection = [[LBLelinkConnection alloc] init];
        _connection.delegate = self;
        _player = [[LBLelinkPlayer alloc] init];
        _player.delegate = self;
    }
    return self;
}

- (void)enableLogConsole:(BOOL)console file:(BOOL)file {
    [LBLelinkKit enableLog:console];
    [LBLelinkKit enableLogFileSave:file];
}

- (void)startWithAppId:(NSString *)appId secretKey:(NSString *)secretKey {
    self.appId = appId;
    self.secretKey = secretKey;
    // 注意：鉴权成功前 SDK 其他功能都不可用；网络恢复或回到前台时重新鉴权
    if (!self.pathMonitor) {
        self.pathMonitor = nw_path_monitor_create();
        nw_path_monitor_set_queue(self.pathMonitor, dispatch_get_main_queue());
        __weak typeof(self) weakSelf = self;
        nw_path_monitor_set_update_handler(self.pathMonitor, ^(nw_path_t path) {
            if (nw_path_get_status(path) == nw_path_status_satisfied) {
                [weakSelf retryAuthIfNeeded];
            }
        });
        nw_path_monitor_start(self.pathMonitor);
        [[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(retryAuthIfNeeded) name:UIApplicationDidBecomeActiveNotification object:nil];
    }
    [self auth];
}

/// 只在上次因网络失败时重试；401 / 402 等不重试，否则会进 180 秒冷却（1002）
- (void)retryAuthIfNeeded {
    if (self.waitingNetwork) {
        [self auth];
    }
}

- (void)auth {
    if (self.authorized || self.authorizing) {
        return;
    }
    self.authorizing = YES;
    self.waitingNetwork = NO;
    NSString *appId = self.appId, *secretKey = self.secretKey;
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        NSError *error = nil;
        BOOL ok = [LBLelinkKit authWithAppid:appId secretKey:secretKey error:&error];
        dispatch_async(dispatch_get_main_queue(), ^{
            self.authorizing = NO;
            if (!ok) {
                // NSURLErrorDomain（如国行首次启动未允许无线数据的 -1009）：等网络恢复或回到前台再鉴权
                // 402：secretKey 应为平台 md5Key；1002：鉴权失败后 180 秒冷却
                self.waitingNetwork = [error.domain isEqualToString:NSURLErrorDomain];
                [self reportError:error];
                return;
            }
            self.authorized = YES;
            self.browser = [[LBLelinkBrowser alloc] init];
            self.browser.delegate = self;
            // 注意：蓝牙搜索默认关闭，不打开就发现不了不在同一 Wi-Fi 的官方收端
            [self.browser enableSearchLelinkService:YES sourceStyle:LBLelinkServiceSourceStyleSearchBluetooth onError:nil];
            // 局域网 + 跨网（蓝牙、投屏码发现的设备走跨网连接）
            [self.browser searchForLelinkServiceOfType:LBLelinkServiceTypeLelink | LBLelinkServiceTypeDlnaDMC | LBLelinkServiceTypePublickNetwork];
        });
    });
}

- (void)connect:(LBLelinkService *)service {
    self.connection.lelinkService = service;
    [self.connection connect];
}

- (void)connectWithCastCode:(NSString *)castCode {
    [self.browser searchForLelinkServiceFormCastCode:castCode callBlock:^(BOOL succeed, NSError *error, NSDictionary *originalData) {
        // 成功时设备从 lelinkBrowser:didFindLelinkService:fromSourceStyle: 回调
        if (!succeed) {
            [self reportError:error];
        }
    }];
}

- (void)connectWithQRCode:(NSString *)qrCode {
    // 注意：SDK 要求子线程调用，会阻塞
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        NSError *error = nil;
        // 成功时设备从 lelinkBrowser:didFindLelinkService:fromSourceStyle: 回调（ScanQRCode）
        if (![self.browser searchForLelinkServiceFormQRCode:qrCode onError:&error]) {
            [self reportError:error];
        }
    });
}

- (void)playOnlineVideo:(NSString *)url {
    LBLelinkPlayerItem *item = [[LBLelinkPlayerItem alloc] init];
    item.mediaType = LBLelinkMediaTypeVideoOnline;
    item.mediaURLString = url;
    [self.player playWithItem:item];
}

- (LBCastCapability *)capability {
    LBCastCapability *capability = [self.player queryCastCapability];
    // 验收要求打出能力查询结果
    NSLog(@"[LBCast] queryCastCapability: %@", capability);
    return capability;
}

#pragma mark - 播控

- (void)pause {
    [self.player pause];
}

- (void)resumePlay {
    [self.player resumePlay];
}

- (void)seekTo:(NSInteger)seconds {
    [self.player seekTo:seconds];
}

- (void)setVolume:(NSInteger)value {
    [self.player setVolume:value];
}

- (void)setPlaySpeed:(double)rate {
    [self.player setPlaySpeedWithRate:[self.player playSpeedRateTypeWithRate:rate]];
}

- (BOOL)playVideoList:(NSArray<LBLelinkPlayerItem *> *)items startMediaId:(NSString *)startMediaId {
    if (![self.player canPushVideoList]) {
        return NO;
    }
    // 0：片源长期有效
    [self.player pushVideoList:items validPeriod:0 startMediaId:startMediaId];
    return YES;
}

- (void)playMediaId:(NSString *)mediaId {
    [self.player playVideoListToMediaId:mediaId];
}

- (void)playNext {
    [self.player playNextMediaInVideoList];
}

- (void)playPrevious {
    [self.player playPrevMediaInVideoList];
}

- (void)stop {
    [self.player stop];
}

#pragma mark - 错误分流

- (void)reportError:(NSError *)error {
    if (!error) return;
    dispatch_async(dispatch_get_main_queue(), ^{
        BOOL guide = (error.code == -1700 || error.code == -1702 || error.code == -2800) && error.userInfo[LBSkillInstallGuideURLKey];
        if (guide && self.onInstallGuide) {
            self.onInstallGuide(error.userInfo);
        } else if (self.onError) {
            self.onError(error);
        }
    });
}

- (void)notifyChange {
    dispatch_async(dispatch_get_main_queue(), ^{ if (self.onChange) self.onChange(); });
}

#pragma mark - LBLelinkBrowserDelegate

- (void)lelinkBrowser:(LBLelinkBrowser *)browser didFindLelinkServices:(NSArray<LBLelinkService *> *)services {
    self.services = services ?: @[];
    [self notifyChange];
}

- (void)lelinkBrowser:(LBLelinkBrowser *)browser onError:(NSError *)error {
    [self reportError:error];
}

// 投屏码 / 扫码解析出的设备直接连接；注意：云端匹配等其他来源也走这里，不自动连
// 注意：不要实现 didFindLelinkServiceFromQRCode:，扫码会两个回调都走，且它会重复回调
- (void)lelinkBrowser:(LBLelinkBrowser *)browser didFindLelinkService:(LBLelinkService *)lelinkService fromSourceStyle:(LBLelinkServiceSourceStyle)sourceStyle {
    if (sourceStyle != LBLelinkServiceSourceStyleInputCastCode && sourceStyle != LBLelinkServiceSourceStyleScanQRCode) {
        return;
    }
    dispatch_async(dispatch_get_main_queue(), ^{ [self connect:lelinkService]; });
}

// 必须实现
- (void)lelinkBrowser:(LBLelinkBrowser *)browser permissionsPolicyDenied:(LBLelinkSystemPermissionsType)systemPermissionsType {
    dispatch_async(dispatch_get_main_queue(), ^{ if (self.onPermissionDenied) self.onPermissionDenied(systemPermissionsType); });
}

#pragma mark - LBLelinkConnectionDelegate

- (void)lelinkConnection:(LBLelinkConnection *)connection didConnectToService:(LBLelinkService *)service {
    // 注意：每次连接成功后重新赋值，播放器在赋值时才取连接的内部通道
    self.player.lelinkConnection = connection;
    self.connectedService = service;
    [self notifyChange];
}

- (void)lelinkConnection:(LBLelinkConnection *)connection disConnectToService:(LBLelinkService *)service {
    self.connectedService = nil;
    [self notifyChange];
}

- (void)lelinkConnection:(LBLelinkConnection *)connection onError:(NSError *)error {
    [self reportError:error];
}

// 必须实现：SDK 开始自动重连，结果仍走连接成功 / 断开回调
- (void)lelinkConnectionDidStartRetryConnect:(LBLelinkConnection *)connection {
}

#pragma mark - LBLelinkPlayerDelegate

- (void)lelinkPlayer:(LBLelinkPlayer *)player playStatus:(LBLelinkPlayStatus)playStatus {
    dispatch_async(dispatch_get_main_queue(), ^{ if (self.onPlayStatus) self.onPlayStatus(playStatus); });
}

- (void)lelinkPlayer:(LBLelinkPlayer *)player progressInfo:(LBLelinkProgressInfo *)progressInfo {
    if (!progressInfo) return;
    NSInteger current = progressInfo.currentTime, duration = progressInfo.duration;
    dispatch_async(dispatch_get_main_queue(), ^{ if (self.onProgress) self.onProgress(current, duration); });
}

- (void)lelinkPlayer:(LBLelinkPlayer *)player currentMediaId:(NSString *)mediaId {
    dispatch_async(dispatch_get_main_queue(), ^{ if (self.onCurrentMediaId) self.onCurrentMediaId(mediaId); });
}

- (void)lelinkPlayer:(LBLelinkPlayer *)player onError:(NSError *)error {
    [self reportError:error];
}

@end
