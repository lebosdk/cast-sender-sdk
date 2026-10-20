# SDK artifact

`scripts/obtain_sdk.py` installs the SDK into `<project dir>/LeboSenderSDK/`:

```
LeboSenderSDK/
├── LBLelinkKit.xcframework   media push (App target; the broadcast extension links it too)
└── Mirror/                   screen mirroring, device arm64 only
    ├── App/        LBReplayAppKit, NERtcSDK, TXLiteAVSDK_TRTC, TXFFmpeg, TXSoundTouch
    └── Extension/  LBReplayKitExtension, LBReplayKit, LBSREncoder, NERtcReplayKit, TXLiteAVSDK_ReplayKitExt
```

A package without `Extension/` installs media push only.

| Command | Effect |
|---|---|
| `--check` | Read-only. Prints the installed SDK version or `无`. |
| (no flag) | Downloads `https://lebotob.hpplay.cn/sdk/iOS/Release/ios-sender-sdk.zip`. This is the normal path. |
| `--local <path>` | Installs from a `.zip` or `.xcframework` the user or SDK team supplied instead, for example when the machine cannot reach the CDN. |

Validation: zip integrity, no absolute or `..` paths, the xcframework has both a device (`ios-arm64`) and a simulator slice, each slice has the binary and `LBLelinkKit.h`, and a mirror package contains all ten mirror frameworks. A failed validation leaves the installed SDK untouched. CDN downloads must stay HTTPS, also after redirects. The script prints the SHA-256 of the package for the record.

Identical content (push and mirror together) is left untouched; different content replaces both. To upgrade, rerun the script; it downloads the current package from the CDN. Do not replace a working SDK just because the request adds a feature.

The package contains media push and screen mirroring. Third-party NetEase / Tencent SDKs are slimmed to device arm64 without bitcode; NERtcSDK, TXFFmpeg, TXSoundTouch, and NERtcReplayKit are dynamic and must be embedded. The free-edition SDK version starts with 9 (for example `92717`); a version starting with 3 is the regular SDK and will not behave as described here.

If installation fails, report the printed error; do not search the web for other copies of the SDK.
