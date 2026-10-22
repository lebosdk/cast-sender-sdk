# Acceptance

A successful build is not enough. Check, and report which items could not be verified (for example no TV available):

| Check | How |
|---|---|
| Credentials map `md5Key` | `onboard.py --check` prints `SDK credential mapping is valid` (Skill-managed only) |
| Project wired | `integrate_sdk.rb --check` (plus `--camera` when QR scan was picked) prints `已接入，无需改动` |
| Simulator build (scope 1 only) | `xcodebuild -project <X> -scheme <S> -destination 'platform=iOS Simulator,name=<device>' build`; with mirroring the mirror frameworks are device-only and this build fails by design |
| Device build without signing | `xcodebuild -project <X> -scheme <S> -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO build` |
| Auth | `authWithAppid:` returns YES; `diagnose` shows `auth=1` and a version starting with 9 |
| Search | An official Lebo TV app on the same Wi-Fi appears in `didFindLelinkServices:` (the simulator uses the Mac's network) |
| Connect and push (scope 1 or 3) | `didConnectToService:`, then `playStatus` reaches `Playing` for an online video |
| Connection methods (if picked) | Cast code and / or QR scan connect to an official TV; with the phone off the TV's Wi-Fi (e.g. cellular) the connection still succeeds and an online video plays; cross-network mirroring too when mirroring was requested. QR scan needs a real device |
| Logs (if picked) | `enableLogConsole:file:` is called before auth with the picked items; with `2`, after a run `Library/Caches/LBLelinkKit` in the App container holds a log file, and searching it for the `md5Key` finds nothing |
| Controls (scope 1 or 3) | The control menu was shown (or the request named the controls); every picked control is in the UI and follows its `capability` flag; stop is always present; `queryCastCapability` is logged |
| Error paths | With no official receiver, -1700 arrives with the install guide in `userInfo`; it is shown, not swallowed |
| Mirroring wired (scope 2 or 3) | `integrate_mirror.rb --check` prints `镜像已接入，无需改动`; the device build contains `PlugIns/<extension>.appex` and the four embedded frameworks |
| Mirroring on device (scope 2 or 3) | Install on a real device, add the mirror device, start the broadcast from the picker; the TV shows the screen on the LAN, and across networks when the phone is off the TV's Wi-Fi |
| Mirroring stop on device (scope 2 or 3) | Stop a cross-network mirror from the App and once from Control Center; the TV leaves the mirror screen both times |
| Secrets | No password, code, token, `secret`, or `md5Key` in logs; `git status` does not show `SkillSdkConfig` or `skill-credentials.properties` |
