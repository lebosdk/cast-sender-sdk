#import "LBMirrorController.h"
#import <ReplayKit/ReplayKit.h>
#import <LBReplayAppKit/LBReplayAppKit.h>
#import "LeboMirrorConfig.h"

@interface LBMirrorController () <LBLelinkMirrorEngineDelegate>
@property (nonatomic, assign, readwrite) BOOL mirroring;
/// 正在镜像的连接
@property (nonatomic, strong, nullable) LBLelinkConnection *connection;
/// 是否跨网（云）镜像，默认 NO
@property (nonatomic, assign) BOOL cloudMirroring;
@end

@implementation LBMirrorController

+ (instancetype)shared {
    static LBMirrorController *instance;
    static dispatch_once_t once;
    dispatch_once(&once, ^{ instance = [[LBMirrorController alloc] init]; });
    return instance;
}

- (void)setup {
    [LBLelinkKit setAppGroupId:LeboMirrorAppGroupId];
    [[LBLelinkMirrorEngine shareInstance] setAppGroupId:LeboMirrorAppGroupId];
    [LBLelinkMirrorEngine shareInstance].delegate = self;
}

- (void)startWithConnection:(LBLelinkConnection *)connection {
    // 注意：connection 必须已连接；免费版对非乐播投屏 TV 版会回调 -2800
    self.connection = connection;
    [[LBLelinkMirrorEngine shareInstance] addMirrorDeviceWithConnection:connection];
}

- (void)stop {
    [self sendCloudExitIfNeeded];
    [[LBLelinkMirrorEngine shareInstance] stopExtensionApp];
    [[LBLelinkMirrorEngine shareInstance] cleanMirrorDevice];
}

/// 跨网镜像结束时通知电视退出
/// 注意：跨网镜像不发这条，电视不会退出；必须用已绑定该连接的播放器发送
- (void)sendCloudExitIfNeeded {
    if (!self.cloudMirroring) {
        return;
    }
    self.cloudMirroring = NO;
    id player = self.connection.lelinkService.lelinkPlayer;
    if ([player isKindOfClass:LBLelinkPlayer.class]) {
        [(LBLelinkPlayer *)player cloudMirrorExitMode:LBLelinkCloudMirrorExitModeActive];
    }
}

/// 弹出系统录屏选择框，只列出本 App 的录屏扩展
- (void)showBroadcastPicker {
    dispatch_async(dispatch_get_main_queue(), ^{
        if (RPScreenRecorder.sharedRecorder.isRecording) {
            return;
        }
        RPSystemBroadcastPickerView *picker = [[RPSystemBroadcastPickerView alloc] initWithFrame:CGRectMake(0, 0, 44, 44)];
        picker.preferredExtension = LeboMirrorExtensionBundleId;
        picker.showsMicrophoneButton = NO;
        for (UIView *view in picker.subviews) {
            if ([view isKindOfClass:UIButton.class]) {
                [(UIButton *)view sendActionsForControlEvents:UIControlEventTouchDown | UIControlEventTouchUpInside];
            }
        }
    });
}

- (void)updateMirroring:(BOOL)mirroring {
    dispatch_async(dispatch_get_main_queue(), ^{
        self.mirroring = mirroring;
        if (self.onStateChange) self.onStateChange(mirroring);
    });
}

- (void)reportError:(NSError *)error {
    dispatch_async(dispatch_get_main_queue(), ^{ if (self.onError && error) self.onError(error); });
}

#pragma mark - LBLelinkMirrorEngineDelegate（协议里的方法全部必须实现）

- (void)mirrorAddMirrorDeviceSucceedConnection:(LBLelinkConnection *)lelinkConnection mirrorStype:(LBLelinkMirrorStype)mirrorStype {
    self.cloudMirroring = (mirrorStype & LBLelinkMirrorStypeInternetYouMe) != 0;
    [self showBroadcastPicker];
}

- (void)mirrorAddMirrorDeviceFailureConnection:(LBLelinkConnection *)lelinkConnection error:(NSError *)error {
    [self reportError:error];
}

- (void)mirrorOnError:(NSError *)error mirrorStype:(LBLelinkMirrorStype)mirrorStype {
    [self reportError:error];
}

- (void)mirrorDidBroadcastExtensionStartedMirrorStype:(LBLelinkMirrorStype)mirrorStype {
}

- (void)mirrorDidBroadcastExtensionStopedMirrorStype:(LBLelinkMirrorStype)mirrorStype {
    // 用户从控制中心停止录屏时走这里
    [self sendCloudExitIfNeeded];
    [[LBLelinkMirrorEngine shareInstance] cleanMirrorDevice];
    [self updateMirroring:NO];
}

- (void)mirrorMirrorDeviceDidConnectConnection:(LBLelinkConnection *)lelinkConnection mirrorStype:(LBLelinkMirrorStype)mirrorStype {
}

- (void)mirrorMirrorDeviceDisConnectConnection:(LBLelinkConnection *)lelinkConnection mirrorStype:(LBLelinkMirrorStype)mirrorStype {
    [self updateMirroring:NO];
}

- (void)mirrorStateMirroring:(BOOL)mirroring mirrorStype:(LBLelinkMirrorStype)mirrorStype {
    [self updateMirroring:mirroring];
}

- (void)mirrorPublicStreamQuality:(NSDictionary *)quality andRTCQualitys:(NSArray<NSDictionary *> *)rtcQualitys {
}

- (void)mirrorQualityVideoFPS:(int)videoFPS videoBitRate:(int)bitRate resolution:(CGSize)resolution {
}

- (void)mirrorPublicRTCQualitys:(NSDictionary *)rtcQuality {
}

- (void)mirrorReceiveVideoFrame:(id)videoFrame {
}

- (void)mirrorReceiveAudioFrame:(id)audioFrame {
}

- (void)mirrorCloudProviderSource:(LBCloudMirrorProviderType)providerSource {
    self.cloudMirroring = YES;
}

@end
