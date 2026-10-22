#import <UIKit/UIKit.h>

NS_ASSUME_NONNULL_BEGIN

/// 扫电视上的投屏二维码，扫到后回调字符串并自动关闭；注意：Info.plist 需有 NSCameraUsageDescription（integrate_sdk.rb --camera）
@interface LBQRScanViewController : UIViewController

/// 扫到的二维码字符串，交给 [LBCastCoordinator connectWithQRCode:]
@property (nonatomic, copy, nullable) void (^onScan)(NSString *value);

@end

NS_ASSUME_NONNULL_END
