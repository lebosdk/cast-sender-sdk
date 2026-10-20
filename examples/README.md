# Minimal integration examples

These snippets are API-shaped examples. Use the exact callback signatures from the SDK artifact in the target project and adapt them to the host application's architecture and lifecycle.

## Device coordinator shape

Keep this logic in one application-scoped coordinator. An Activity observes its state; it does not replace listeners or stop browsing from `onPause()`/`onStop()`. The complete state and lifecycle rules are in [discovery and connection](../references/discovery-connection.md).

```java
final class SenderDeviceCoordinator {
    private final LelinkSourceSDK sdk = LelinkSourceSDK.getInstance();
    private boolean bound;
    private boolean binding;
    private boolean browsing;
    private boolean browsePending;
    private boolean restartAfterStop;
    private boolean stoppingForRefresh;
    private String lastBrowseFingerprint;
    private int repeatedBrowseResults;
    private List<LelinkServiceInfo> devices = Collections.emptyList();
    private LelinkServiceInfo connectedDevice;

    void initialize(Context context) {
        if (bound || binding) return;
        binding = true;
        sdk.setBindSdkListener(success -> {
            binding = false;
            bound = success;
            logBindResult(success);
            if (success && browsePending) {
                browsePending = false;
                startBrowseNow();
            }
        });
        sdk.setBrowseResultListener((resultCode, callbackDevices) -> {
            List<LelinkServiceInfo> snapshot = callbackDevices == null
                    ? Collections.emptyList()
                    : new ArrayList<>(callbackDevices);
            String fingerprint = browseFingerprint(resultCode, snapshot);
            boolean visibleChange = !fingerprint.equals(lastBrowseFingerprint);
            if (visibleChange) {
                logBrowseResult(resultCode, snapshot.size(), repeatedBrowseResults);
                lastBrowseFingerprint = fingerprint;
                repeatedBrowseResults = 0;
            } else {
                repeatedBrowseResults++;
            }
            if (resultCode == IBrowseListener.BROWSE_SUCCESS) {
                // Always retain the newest SDK objects even when visible content is unchanged.
                devices = snapshot;
                if (visibleChange) {
                    publishDevices(resultCode, devices);
                }
            } else if (resultCode == IBrowseListener.BROWSE_STOP) {
                boolean refreshWasRequested = stoppingForRefresh || restartAfterStop;
                browsing = false;
                stoppingForRefresh = false;
                publishBrowseFinished(refreshWasRequested
                        ? "refresh_stop"
                        : "sdk_window_complete");
                if (restartAfterStop) {
                    restartAfterStop = false;
                    startBrowseNow();
                }
            } else {
                browsing = false;
                stoppingForRefresh = false;
                if (!snapshot.isEmpty()) {
                    devices = snapshot;
                }
                publishDevices(resultCode, devices);
                handleBrowseTerminalResult(resultCode, sdk.getSinkInstallGuide());
            }
        });
        sdk.setConnectListener(new IConnectListener() {
            @Override public void onConnect(LelinkServiceInfo info, int type) {
                connectedDevice = info;
                publishConnected(info, type);
            }
            @Override public void onDisconnect(LelinkServiceInfo info, int what, int extra) {
                handleDisconnect(info, what, extra);
            }
            @Override public void onReconnecting(LelinkServiceInfo info, int type) {
                publishReconnecting(info, type);
            }
            @Override public void onReconnectSuccess(LelinkServiceInfo info, int type) {
                connectedDevice = info;
                publishConnected(info, type);
            }
        });
        registerCompletePlayerListenerBeforeBinding(sdk);
        sdk.setSdkInitInfo(
                context.getApplicationContext(),
                SkillSdkConfig.APP_ID,
                SkillSdkConfig.APP_SECRET
        ).bindSdk();
    }

    void requestBrowse() {
        if (!bound) {
            browsePending = true;
            return;
        }
        if (stoppingForRefresh) {
            restartAfterStop = true;
            return;
        }
        if (browsing) {
            restartAfterStop = true;
            stoppingForRefresh = true;
            sdk.stopBrowse();
            return;
        }
        startBrowseNow();
    }

    private void startBrowseNow() {
        devices = Collections.emptyList();
        browsing = true;
        stoppingForRefresh = false;
        lastBrowseFingerprint = null;
        repeatedBrowseResults = 0;
        sdk.startBrowse();
    }

    void connectSelected(LelinkServiceInfo selectedFromCurrentSnapshot) {
        if (bound && selectedFromCurrentSnapshot != null) {
            sdk.connect(selectedFromCurrentSnapshot);
        }
    }
}
```

The generated `SkillSdkConfig.APP_SECRET` contains the platform `md5Key`, which is the value expected by the SDK's `appSecret` parameter. Do not replace it with the platform response's separate `secret` field.

The helper names above represent host UI/state hooks. `browseFingerprint` must use the result code plus stable device keys and UI-visible fields, not list/object identity. Implement the hooks so every distinct bind, browse, parse, connect, disconnect, and playback transition preserves its callback domain and numeric codes. Post UI updates to the main thread and use a defensive list snapshot. A spontaneous `BROWSE_STOP` is the SDK's normal end of its browse window; only label it as an explicit stop when the coordinator had a matching pending request.

## QR or PIN parse and connect

```java
IServiceInfoParseListener parseListener = (resultCode, info) -> {
    logParseResult(resultCode, info != null); // Do not log decodedText.
    if (resultCode == IServiceInfoParseListener.PARSE_SUCCESS && info != null) {
        sdk.connect(info);
    } else if (resultCode == IServiceInfoParseListener.PARSE_NOT_OFFICIAL_SINK) {
        showInstallGuide(sdk.getSinkInstallGuide());
    }
};
sdk.addQRCodeToLelinkServiceInfo(decodedText, parseListener);
// The PIN API uses the same explicitly typed listener:
// sdk.addPinCodeToLelinkServiceInfo(pinCode, parseListener);
```

Call this only after the camera Activity returns `RESULT_OK` with non-empty text. Camera decoding and SDK parsing are separate stages. Do not inline the lambda: both methods also have a deprecated listener overload with the same lambda shape, so Java reports an ambiguous method reference without the explicit `IServiceInfoParseListener` type.

## URL casting

```java
LelinkPlayerInfo info = new LelinkPlayerInfo();
info.setLelinkServiceInfo(connectedDeviceFromOnConnect);
info.setType(LelinkSourceSDK.MEDIA_TYPE_VIDEO);
info.setUrl(publicUrl);
sdk.startPlayMedia(info);
```

Treat player `onStart` as a repeatable state notification, not one-time setup. The SDK may emit it roughly every 30 seconds during one video or after a seek. Guard session initialization with the host's cast request/session ID. After `seekTo`, use `onPositionUpdate` plus a tolerance and timeout as the portable completion signal; `onSeekComplete` is optional across receiver/protocol versions.

## Screen mirroring from an ordinary application

```java
LelinkPlayerInfo info = new LelinkPlayerInfo();
info.setLelinkServiceInfo(connectedDeviceFromOnConnect);
info.useSystemMirrorCapture(false); // Optional: false is the default for ordinary apps.
sdk.startMirror(info);
```

Keep the normal MediaProjection consent flow. Do not change this to `useSystemMirrorCapture(true)` to suppress the consent UI: `true` skips the ordinary-app authorization path and is reserved for a confirmed system application with the SDK-supported system capture path.

## Image list

```java
ImageListInfo.ImageItem item = new ImageListInfo.ImageItem();
item.id = "image-1";
item.setUrl("https://receiver-can-fetch.example/image.jpg");
ImageListInfo group = new ImageListInfo();
group.urls = new ImageListInfo.ImageItem[]{item};

LelinkPlayerInfo info = new LelinkPlayerInfo();
info.setLelinkServiceInfo(connectedDeviceFromOnConnect);
info.setType(LelinkSourceSDK.MEDIA_TYPE_IMAGE);
info.setUrl(item.getUrl());
info.setImageList(new ImageListInfo[]{group}, item.id, 3600);
sdk.startPlayMedia(info);
```

Use `isSupportImageList(connectedDeviceFromOnConnect)` before presenting list controls. Validate IDs and URLs before sending.
