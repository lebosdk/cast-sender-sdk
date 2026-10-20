# Changelog

## 0.33.0

- Renamed the Skill from `android-sender-sdk` to `cast-sender-sdk` and aligned its directory, package, metadata, and HTTP User-Agent.
- Kept the registered onboarding source label `android-sender-sdk` stable and continued recognizing generated configs carrying the legacy Skill marker.

## 0.32.0

- Switched automatic SDK acquisition from the debug artifact to the production release AAR at `https://lebotob.hpplay.cn/sdk/android/release/source-leboapk-release.aar`.
- Retained HTTPS redirect enforcement, AAR structure validation, SHA-256 reporting, and atomic installation behavior.

## 0.31.0

- Switched credential registration, authentication, application creation, and browser fallback from the pre-release platform to `https://openplat.hpplay.cn`.
- Kept authentication state isolated by endpoint so cached test-platform tokens cannot be reused in production.

## 0.30.0

- Made generated hosts add AndroidX Core, a valid notification icon, Git initialization, optional repository-mirror wiring, USB Host filtering protection, and least-privilege Manifest overrides.
- Reused exact Gradle distributions from the Skill cache, `GRADLE_USER_HOME`/`~/.gradle` wrapper cache, or `PATH` before downloading from `services.gradle.org`; local Wrapper creation now skips Gradle's otherwise redundant online URL validation.
- Corrected every onboarding command to include required `--project-dir` and `--app-name` arguments.
- Disambiguated QR/PIN listener overload examples and documented browse callback coalescing, automatic `BROWSE_STOP`, repeatable player `onStart`, and seek completion without `onSeekComplete`.
- Added merged-Manifest, foreground-notification, dependency, store-filtering, privacy, callback, and restricted-network acceptance coverage.

## 0.29.0

- Made MediaProjection the required default mirroring path for ordinary applications.
- Reserved `useSystemMirrorCapture(true)` for confirmed system-app system-capture integrations and documented that it skips ordinary MediaProjection authorization.
- Added mirror examples, acceptance checks, and troubleshooting for accidental permission-path bypass.

## 0.28.0

- Added an incremental integration path that preserves an existing SDK artifact, initialization, credentials, discovery, connection, and working casting modes.
- Skipped the casting-scope menu when the user explicitly requests a capability or asks to add one to an existing integration.
- Reused existing non-placeholder App ID and SDK App Secret values without registration, login, or migration into the Skill-managed credential format.

## 0.27.0

- Changed Skill-free receiver eligibility from a fixed package name to the server channel classification: receiver App IDs are accepted when `channel.type == 1`.
- Documented that missing App ID metadata can cause APK receiver channel validation to fail.

## 0.26.0

- Required `android:usesCleartextTraffic="true"` on the host application's `<application>` and added it to newly generated projects so the SDK can read receiver metadata from dynamic LAN HTTP endpoints.
- Added Debug and Release merged-Manifest verification for the cleartext policy.
- Documented how a blocked `DnsTxtInfo` request leaves receiver eligibility metadata empty and can falsely surface as connection error `212010/212101`.

## 0.25.0

- Made an empty current directory the implicit new-project destination instead of asking for a path.
- Required the first no-project response to show a concrete application-name numbered menu and wait for that single selection.
- Prohibited asking for application name and `applicationId` together; the package-name menu now appears only after the name is selected.
- Added stable fallback candidates for both menus while retaining `自己输入` as the final option.

## 0.24.0

- Made `SkillSdkConfig.APP_SECRET = platform md5Key` an invariant and explicitly prohibited platform `secret` in SDK initialization.
- Added generated-config verification to onboarding and made read-only preflight fail for missing, stale, manually changed, or incorrectly mapped SDK config without exposing credential values.
- Required onboarding preflight immediately before every Debug and Release build.
- Removed redundant package confirmation for existing projects whose `applicationId` is already determined.

## 0.23.0

- Added a required discovery/connection controller contract derived from the working demo ownership model.
- Prevented generated integrations from stopping browse during transient Activity/Fragment `onPause()` or `onStop()` transitions.
- Required exact callback device objects, serialized browse refresh, connection-success gating, defensive list snapshots, and per-domain diagnostic events.
- Documented Skill-free receiver filtering and separated QR camera decoding from SDK QR/PIN parsing.

## 0.22.0

- Made the documented registration-to-login transition explicit: registration error `1101` now reports the transition and reuses the same mobile number and verification code without another SMS or prompt.
- Scoped cached registered-account state to the exact saved mobile number and clear old authentication state when the number changes, so retries still start from registration.
- Documented that account existence is decided by registration and that Skill login is verification-code based, with no invented status-check or password-login endpoint.

## 0.21.0

- Added Chinese and English titles, guidance, validation, and retry prompts throughout platform-account onboarding dialogs and terminal fallback.
- Added bilingual Continue and Cancel labels to native dialog backends that support custom button text.

## 0.20.0

- Changed new-project application name and `applicationId` collection to explicit numbered terminal menus with two candidates and a final custom-input option.
- Changed casting scope to a numbered three-mode terminal menu with media-only as the 30-second default.
- Allowed visible terminal entry after a warning when secret input cannot disable echo.

## 0.19.0

- Added terminal fallback when graphical account dialogs are unavailable.
- Kept verification-code, password, and password re-entry input hidden with `getpass` in terminal mode.

## 0.18.0

- Added a native Windows account-input backend using the built-in Windows PowerShell and WinForms.
- Kept Tk as a fallback when the native Windows dialog backend is unavailable.

## 0.17.0

- Restored modal account input for mobile numbers, verification codes, passwords, password re-entry, and account selection.
- Masked verification-code and password fields and removed terminal input fallback for onboarding data.

## 0.16.0

- Improved empty-project identity entry: application name and `applicationId` are resolved one at a time from numbered candidates or a custom value accepted with Enter.
- Kept one final strict `[y/n]` approval for the exact identity pair before project creation.

## 0.15.0

- Added an explicit preflight confirmation phase so project identity, mirroring scope, SDK licenses, and app registration approval are resolved before SDK integration actions begin.
- Removed the late saved-mobile reuse confirmation from onboarding; authentication now collects the mobile number as ordinary data entry.
- Clarified that password re-entry is credential validation rather than an approval prompt.

## 0.14.0

- Standardized every binary user confirmation on strict case-insensitive `y` or `n`; empty and other responses are not confirmation.
- Relabeled the timed mirroring list as `y` for media push plus real-time phone-screen mirroring and `n` for the media-push-only default.
- Changed saved-mobile reuse to require an explicit `y` or `n` instead of accepting Enter as yes.

## 0.13.0

- Replaced the mirroring yes/no prompt with a fixed two-item single-select list: media push only, or media push plus real-time phone-screen mirroring.
- Kept the 30-second timeout and made `仅媒体推送` the explicit default selection.

## 0.12.0

- Required the user to enter or select and explicitly confirm both the application name and `applicationId` before an empty Android project can be created.
- Added a `--confirm` creation guard; `--check` remains read-only and displays the exact identity values for confirmation.

## 0.11.0

- Added a 30-second mirroring scope choice before casting implementation; timeout defaults to media push only.
- Added an interactive registration reminder to retain the platform username and password for later application-information changes.

## 0.10.0

- Corrected generated SDK credentials so `SkillSdkConfig.APP_SECRET` is populated from the platform `md5Key`, which is the value the Android sender SDK uses.
- Kept the platform `secret` and `md5Key` as separate ignored `local.properties` values.

## 0.9.0

- Replaced the terminal confirmation prompt with a current-session confirmation followed by `--confirm`.
- Generated an ignored `SkillSdkConfig.java` containing `appId` and `appSecret` so SDK integration can continue immediately after onboarding.

## 0.8.0

- Added the stable built-in onboarding source `android-sender-sdk`, so missing channel configuration no longer blocks registration.
- Kept `--src` only as an optional override and removed publisher approval or preregistration requirements from the Skill workflow.

## 0.7.0

- Made missing credential onboarding an active integration step that registers or authenticates the platform account and creates or reuses the application after confirmation.
- The onboarding script now detects the Android `applicationId` from the application module instead of accepting it as a command-line argument.
- Fixed pre-release onboarding to the test platform and removed production/test command-line selection and credential tagging.

## 0.6.0

- Replaced user-provided AAR and optional CDN fallback flows with an automatic download from the fixed official CDN URL.
- The artifact helper now downloads on every run, validates the AAR, reports its SHA-256, and atomically updates the managed project copy when needed.

## 0.5.0

- Added detection of an existing Android application and safe creation of a clean project when none exists.
- Added validation and installation of a user-provided SDK AAR.
- Added an HTTPS CDN fallback that remains disabled until the publisher configures its URL and SHA-256.

## 0.4.0

- Added project-aware checks for JDK, Android SDK packages, platform tools, and the Gradle Wrapper.
- Added user-local, checksum-verified setup for missing build tools without administrator access.
- Added guarded Android SDK license handling and Gradle environment verification.
- Removed the standalone demo from the distributed Skill; integration is validated against the tester's clean host app.

## 0.3.0

- Added interactive App credential onboarding with resumable authentication and browser fallback.
- Added guarded local credential storage and onboarding guidance for coding agents.
- Added explicit production/test endpoint selection for onboarding integration tests.

## 0.2.0

- Added the complete public sender API reference, including advanced APIs and release lifecycle guidance.

## 0.1.0

- Added portable Android sender SDK integration workflow.
- Added API, installation, error handling, troubleshooting, and acceptance references.
- Added platform-neutral Java examples for binding, browsing, URL casting, and image lists.
- Added a standalone Android demo project with external AAR injection.
- Added marketplace metadata.
