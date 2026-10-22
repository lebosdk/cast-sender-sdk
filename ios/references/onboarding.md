# Credential onboarding

The SDK is initialized with `+[LBLelinkKit authWithAppid:secretKey:error:]`. The values come from the HPPlay open platform.

**The invariant:** `appid` = platform `appId`; `secretKey` = platform `md5Key`. Passing the platform `secret` fails with 402.

## Reuse first

If the project already passes a non-placeholder App ID and secret to `authWithAppid:secretKey:error:` (from any source), keep them. Do not run onboarding, do not print or move them.

## Skill-managed credentials

`scripts/onboard.py` registers or logs in to the platform by SMS, creates or reuses an application for the target's Bundle ID (`platformType = 2`, iOS), and writes:

- `LeboSenderSDK/skill-credentials.properties`: `appId`, `secret`, `md5Key`, and the Bundle ID they were created for (Git-ignored automatically; or pass `--credentials-file` outside the project).
- `<target dir>/SkillSdkConfig.h` for Objective-C projects: `SkillSdkAppId`, `SkillSdkAppSecret`. Swift-only targets get `SkillSdkConfig.swift` (`SkillSdkConfig.appId`, `.appSecret`) added to the target's sources. Both are Git-ignored.

| Command | Effect |
|---|---|
| `--check` | No network. Verifies the generated config maps `md5Key` correctly; fails if credentials are absent, stale, or hand-edited, or were created for another Bundle ID (the SDK signs auth with the runtime Bundle ID, so a mismatch fails with 402). Older files without a recorded Bundle ID only print a note. |
| (no `--confirm`) | Shows what would happen and stops. No SMS is sent. |
| `--confirm` | Asks for mobile number, verification code, and (new accounts) a password in macOS dialogs, then creates or reuses the application. |
| `--reset-state` | Forgets the cached login. |

The Bundle ID is resolved with `xcodebuild -showBuildSettings` (Release). Pass `--target` / `--project` when the directory is ambiguous.

If onboarding fails with a fallback URL, give it to the user to finish in a browser; they need the mobile number, application name, and Bundle ID.

## Auth behaviour to know

- Authentication is synchronous; call it off the main thread.
- After a 401 / 402 the SDK refuses to retry for 180 seconds and returns 1002 immediately, even across app restarts. Fix the credentials, then wait.
