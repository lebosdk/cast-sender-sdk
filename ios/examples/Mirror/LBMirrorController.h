#import <Foundation/Foundation.h>
#import <LBLelinkKit/LBLelinkKit.h>

NS_ASSUME_NONNULL_BEGIN

/// App 端镜像控制：添加镜像设备、拉起系统录屏选择框、停止镜像，整个 App 只用一个
@interface LBMirrorController : NSObject

+ (instancetype)shared;

/// 是否正在镜像
@property (nonatomic, assign, readonly) BOOL mirroring;
/// 镜像状态变化
@property (nonatomic, copy, nullable) void (^onStateChange)(BOOL mirroring);
/// 镜像错误（域 + 错误码）；-2800 时 userInfo 带安装引导
@property (nonatomic, copy, nullable) void (^onError)(NSError *error);

/// 启动时调用一次（鉴权后即可），设置与录屏扩展相同的 App Group
- (void)setup;
/// 用已连接的连接对象开始镜像；成功后自动弹出系统录屏选择框
- (void)startWithConnection:(LBLelinkConnection *)connection;
/// 停止镜像（结束录屏扩展）
- (void)stop;

@end

NS_ASSUME_NONNULL_END
