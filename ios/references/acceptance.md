# Acceptance

A successful build is not enough. Check, and report which items could not be verified (for example no TV available):

| Check | How |
|---|---|
| Credentials map `md5Key` | `onboard.py --check` prints `SDK credential mapping is valid` (Skill-managed only) |
| Project wired | `integrate_sdk.rb --check` prints `已接入，无需改动` |
| Simulator build | `xcodebuild -project <X> -scheme <S> -destination 'platform=iOS Simulator,name=<device>' build` |
| Device build without signing | `xcodebuild -project <X> -scheme <S> -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO build` |
| Auth | `authWithAppid:` returns YES; `diagnose` shows `auth=1` and a version starting with 9 |
| Search | An official Lebo TV app on the same Wi-Fi appears in `didFindLelinkServices:` (the simulator uses the Mac's network) |
| Connect and push | `didConnectToService:`, then `playStatus` reaches `Playing` for an online video |
| Controls | `queryCastCapability` is logged and the UI hides disallowed controls |
| Error paths | With no official receiver, -1700 arrives with the install guide in `userInfo`; it is shown, not swallowed |
| Mirroring wired (if requested) | `integrate_mirror.rb --check` prints `镜像已接入，无需改动`; the device build contains `PlugIns/<extension>.appex` and the four embedded frameworks |
| Mirroring on device (if requested) | Install on a real device, add the mirror device, start the broadcast from the picker; the TV shows the screen on the LAN, and across networks when the phone is off the TV's Wi-Fi |
| Mirroring stop on device (if requested) | Stop a cross-network mirror from the App and once from Control Center; the TV leaves the mirror screen both times |
| Secrets | No password, code, token, `secret`, or `md5Key` in logs; `git status` does not show `SkillSdkConfig` or `skill-credentials.properties` |
