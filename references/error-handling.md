# Callback domains and Skill-specific results

Handle each code in its own callback. Never compare a browse result to a player error or merge `what`/`extra` from different interfaces.

| Callback | Constant | Value | Response |
| --- | --- | ---: | --- |
| `IBrowseListener.onBrowse` | `BROWSE_NO_LEBO_DEVICE` | 5 | Offer official TV app installation guide. |
| `IBrowseListener.onBrowse` | `BROWSE_MULTICAST_BLOCKED` | 6 | Troubleshoot Wi-Fi, multicast, permissions, and AP isolation. |
| `IServiceInfoParseListener.onParseResult` | `PARSE_NOT_OFFICIAL_SINK` | 13 | Do not connect; offer installation guide. |
| `IConnectListener.onDisconnect` | `WHAT_CONNECT_FAILED` + `EXTRA_CONNECT_NOT_OFFICIAL_SINK` | 212010 + 212101 | First rule out blocked LAN HTTP metadata (`Cleartext HTTP traffic ... not permitted` or `appId:0`); otherwise offer the official TV app installation guide. |
| `ILelinkPlayerListener.onError` | `WHAT_ERROR_PUSH_INIT` + `EXTRA_ERROR_PUSH_LOCAL_MEDIA_ON_IM` | 210000 + 210005 | Use a receiver-accessible HTTP(S) media URL for cross-network casting. |

Get guide data with `getSinkInstallGuide()`. Its H5 URL requires network access; use `steps` when the page cannot load. `diagnose()` is read-only but contains app ID and device metadata, so review before uploading it.

The absence of `onSeekComplete` is not itself a player error. Some receiver/protocol combinations emit `onStart` after `seekTo` and only expose the new location through `onPositionUpdate`. Decide success from position progress and a bounded timeout; keep any actual `onError(what, extra)` in the player error domain.
