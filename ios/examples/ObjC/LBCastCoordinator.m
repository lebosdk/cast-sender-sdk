#import "LBCastCoordinator.h"

@interface LBCastCoordinator () <LBLelinkBrowserDelegate, LBLelinkConnectionDelegate, LBLelinkPlayerDelegate>
@property (nonatomic, copy, readwrite) NSArray<LBLelinkService *> *services;
@property (nonatomic, strong, readwrite, nullable) LBLelinkService *connectedService;
@property (nonatomic, strong) LBLelinkBrowser *browser;
@property (nonatomic, strong) LBLelinkConnection *connection;
@property (nonatomic, strong) LBLelinkPlayer *player;
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
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{
        NSError *error = nil;
        BOOL ok = [LBLelinkKit authWithAppid:appId secretKey:secretKey error:&error];
        dispatch_async(dispatch_get_main_queue(), ^{
            if (!ok) {
                // 402：secretKey 应为平台 md5Key；1002：鉴权失败后 180 秒冷却
                [self reportError:error];
                return;
            }
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
