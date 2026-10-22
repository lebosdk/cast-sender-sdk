#import "LBQRScanViewController.h"
#import <AVFoundation/AVFoundation.h>

@interface LBQRScanViewController () <AVCaptureMetadataOutputObjectsDelegate>
@property (nonatomic, strong) AVCaptureSession *session;
@property (nonatomic, strong) AVCaptureVideoPreviewLayer *previewLayer;
@property (nonatomic, assign) BOOL handled;
@end

@implementation LBQRScanViewController

- (void)viewDidLoad {
    [super viewDidLoad];
    self.view.backgroundColor = UIColor.blackColor;
    [AVCaptureDevice requestAccessForMediaType:AVMediaTypeVideo completionHandler:^(BOOL granted) {
        dispatch_async(dispatch_get_main_queue(), ^{
            if (granted) {
                [self startSession];
            } else {
                [self showMessage:@"请在 设置 > 隐私 > 相机 中允许访问"];
            }
        });
    }];
}

- (void)viewDidLayoutSubviews {
    [super viewDidLayoutSubviews];
    self.previewLayer.frame = self.view.bounds;
}

- (void)viewWillDisappear:(BOOL)animated {
    [super viewWillDisappear:animated];
    AVCaptureSession *session = self.session;
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{ [session stopRunning]; });
}

- (void)startSession {
    AVCaptureDevice *device = [AVCaptureDevice defaultDeviceWithMediaType:AVMediaTypeVideo];
    AVCaptureDeviceInput *input = device ? [AVCaptureDeviceInput deviceInputWithDevice:device error:nil] : nil;
    // 模拟器没有摄像头
    if (!input) {
        [self showMessage:@"当前设备没有可用的摄像头"];
        return;
    }
    AVCaptureSession *session = [[AVCaptureSession alloc] init];
    AVCaptureMetadataOutput *output = [[AVCaptureMetadataOutput alloc] init];
    if (![session canAddInput:input] || ![session canAddOutput:output]) {
        [self showMessage:@"摄像头不可用"];
        return;
    }
    [session addInput:input];
    [session addOutput:output];
    // 注意：类型要在 addOutput 之后设置
    [output setMetadataObjectsDelegate:self queue:dispatch_get_main_queue()];
    output.metadataObjectTypes = @[AVMetadataObjectTypeQRCode];

    self.previewLayer = [AVCaptureVideoPreviewLayer layerWithSession:session];
    self.previewLayer.videoGravity = AVLayerVideoGravityResizeAspectFill;
    self.previewLayer.frame = self.view.bounds;
    [self.view.layer addSublayer:self.previewLayer];
    self.session = session;
    // 注意：startRunning 会阻塞，放子线程
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED, 0), ^{ [session startRunning]; });
}

- (void)showMessage:(NSString *)text {
    UILabel *label = [[UILabel alloc] initWithFrame:self.view.bounds];
    label.text = text;
    label.textColor = UIColor.whiteColor;
    label.textAlignment = NSTextAlignmentCenter;
    label.numberOfLines = 0;
    label.autoresizingMask = UIViewAutoresizingFlexibleWidth | UIViewAutoresizingFlexibleHeight;
    [self.view addSubview:label];
}

#pragma mark - AVCaptureMetadataOutputObjectsDelegate

- (void)captureOutput:(AVCaptureOutput *)output didOutputMetadataObjects:(NSArray<__kindof AVMetadataObject *> *)metadataObjects fromConnection:(AVCaptureConnection *)connection {
    // 同一个码会连续回调多次，只处理第一次
    if (self.handled) return;
    AVMetadataMachineReadableCodeObject *code = metadataObjects.firstObject;
    if (![code isKindOfClass:[AVMetadataMachineReadableCodeObject class]] || code.stringValue.length == 0) return;
    self.handled = YES;
    NSString *value = code.stringValue;
    void (^onScan)(NSString *) = self.onScan;
    if (self.navigationController && self.navigationController.topViewController == self) {
        [self.navigationController popViewControllerAnimated:YES];
    } else {
        [self dismissViewControllerAnimated:YES completion:nil];
    }
    if (onScan) onScan(value);
}

@end
