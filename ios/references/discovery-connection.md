# Discovery and connection

Keep one long-lived coordinator (an app-scoped object, not a view controller) that owns the auth state, `LBLelinkBrowser`, the selected `LBLelinkService`, `LBLelinkConnection`, and `LBLelinkPlayer`. View controllers observe it.

Order:

1. Authenticate on a background queue. Do not search until it returns YES; on NO, show the error code (see onboarding for 402 / 1002).
2. Create the browser, set the delegate, enable Bluetooth discovery with `enableSearchLelinkService:YES sourceStyle:LBLelinkServiceSourceStyleSearchBluetooth onError:nil` (off by default; without it official receivers outside the Wi-Fi are never found), then call `searchForLelinkServiceOfType:`.
3. Replace the device list on every `didFindLelinkServices:`. Keep the `LBLelinkService` objects as delivered; never rebuild one from a name or IP.
4. On user selection, set `connection.lelinkService` to that exact object and call `connect` once. Do not call `connect` again while a connect is in flight; it fails with -2301.
5. Only in `lelinkConnection:didConnectToService:` assign `player.lelinkConnection = connection` (every time, including reconnects) and enable push UI. Binding earlier fails with -3003.
6. On `disConnectToService:` disable push UI; keep the browser running so the user can reconnect.

Free edition specifics:

- The list contains only official Lebo TV receivers. If search sees devices but none qualify, the browser reports -1700 about 10 seconds after the search starts.
- One connection at a time. Reuse one `LBLelinkConnection` object; connecting another object disconnects the previous one.
- QR code and cast code results go through the same eligibility check and fail with -1702.

iOS shows the local-network permission prompt on the first search. If the user denies it, search finds nothing; guide them to Settings > Privacy > Local Network.
