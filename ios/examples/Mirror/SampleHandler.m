#import "SampleHandler.h"
#import <LBReplayKitExtension/LBReplayKitExtension.h>
#import <LBLelinkKit/LBLelinkKit.h>

/// 与主 App 相同的 App Group，由 integrate_mirror.rb 生成时填入
static NSString * const kLeboAppGroupId = @"__LEBO_APP_GROUP_ID__";

@interface SampleHandler () <LBLelinkMirrorExtensionDelegate>
@end

@implementation SampleHandler

- (void)broadcastStartedWithSetupInfo:(NSDictionary<NSString *, NSObject *> *)setupInfo {
    [LBLelinkKit setAppGroupId:kLeboAppGroupId];
    [LBLelinkMirrorExtension sharedInstance].delegate = self;
    [[LBLelinkMirrorExtension sharedInstance] setAppGroupId:kLeboAppGroupId];
    [[LBLelinkMirrorExtension sharedInstance] startMirror];
}

- (void)broadcastPaused {
    [[LBLelinkMirrorExtension sharedInstance] paused];
}

- (void)broadcastResumed {
    [[LBLelinkMirrorExtension sharedInstance] resumed];
}

- (void)broadcastFinished {
    [[LBLelinkMirrorExtension sharedInstance] finished];
    [[LBLelinkMirrorExtension sharedInstance] stopMirror];
}

- (void)processSampleBuffer:(CMSampleBufferRef)sampleBuffer withType:(RPSampleBufferType)sampleBufferType {
    [[LBLelinkMirrorExtension sharedInstance] processSampleBuffer:sampleBuffer withType:sampleBufferType];
}

/// 结束录屏并在系统提示里显示原因
- (void)finishWithMessage:(NSString *)message {
    dispatch_async(dispatch_get_main_queue(), ^{
        NSError *error = [NSError errorWithDomain:@"LeboMirror" code:-1 userInfo:@{NSLocalizedFailureReasonErrorKey: message}];
        [self finishBroadcastWithError:error];
    });
}

#pragma mark - LBLelinkMirrorExtensionDelegate

- (void)hostAppResponseWithStarted:(BOOL)started {
}

- (void)hostAppStopExtensionApp {
    [self finishWithMessage:@"已停止镜像"];
}

- (void)lelinkMirrorExtensionError:(NSError *)error {
    [self finishWithMessage:[NSString stringWithFormat:@"镜像出错：%ld", (long)error.code]];
}

@end
