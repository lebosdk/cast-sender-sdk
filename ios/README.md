# ios-sender-sdk

`ios-sender-sdk` is a Codex / Claude Code Skill for integrating the HPPlay/Lelink (Lebo) iOS
sender SDK free edition into an existing Xcode app. It guides the agent through environment
checks, SDK acquisition, project wiring, credential onboarding, device discovery, connection,
media push, playback control, screen mirroring, error handling, and acceptance checks.

本目录是 Skill 源码，不是 iOS 接收端应用，也不包含 SDK 产物、平台账号凭证或任何特定应用的 Bundle ID。

## What It Covers

- Checking Xcode, the `xcodeproj` Ruby library, and the target Xcode project; selecting an
  App target.
- Downloading and validating the official SDK package from the CDN and installing
  `LBLelinkKit.xcframework`.
- Wiring the target: linking, `-ObjC`, local network and Bluetooth usage descriptions, Bonjour
  service, and ATS settings.
- Reusing existing credentials or onboarding Skill-managed credentials safely.
- Implementing search (including Bluetooth discovery and cast-code connection), connection,
  online/local media push, playback control, capability query, and diagnostics.
- Screen mirroring through a Broadcast Upload Extension with an App Group, on top of a working
  media-push integration.

The Skill does not create new Xcode projects, implement receiver/TV applications, implement
server APIs, or produce formal SDK packages.

## Installation

Link this directory into the Skills directory as `ios-sender-sdk`, for example:

```bash
ln -s /path/to/ios-sender-sdk ~/.claude/skills/ios-sender-sdk
ln -s /path/to/ios-sender-sdk ~/.codex/skills/ios-sender-sdk
```

Restart or reload the session, then request it as `/ios-sender-sdk` (Claude Code) or
`$ios-sender-sdk` (Codex), or describe an iOS sender SDK integration task.

## Directory Layout

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Trigger metadata, workflow, free-edition rules, and boundaries |
| `references/` | SDK artifact, installation, onboarding, API, discovery/connection, errors, incremental integration, mirroring, and acceptance guidance |
| `examples/` | Objective-C push coordinator, mirror controller, broadcast extension template, and Swift usage |
| `scripts/check_env.py` | Read-only check of Xcode, `xcodeproj`, and the target project |
| `scripts/obtain_sdk.py` | Check, download, validate, and install the official SDK package |
| `scripts/integrate_sdk.rb` | Wire the SDK into an App target; repeatable |
| `scripts/integrate_mirror.rb` | Add the broadcast extension, App Group, and mirror frameworks; repeatable |
| `scripts/onboard.py` | Check or obtain platform credentials and write ignored local configuration |
| `VERSION` / `CHANGELOG.md` | Skill release version and change history |

## Safe Workflow

Run read-only checks before any mutating step:

```bash
python3 -I scripts/check_env.py --project-dir /path/to/ios-project

python3 -I scripts/obtain_sdk.py --project-dir /path/to/ios-project --check

ruby scripts/integrate_sdk.rb --project /path/to/App.xcodeproj --target App --check

python3 -I scripts/onboard.py \
  --project-dir /path/to/ios-project \
  --app-name "Sender App" \
  --check
```

`--check` does not modify the project, send SMS, authenticate, or create an application. Only
run mutating commands after the required user confirmations described in `SKILL.md` have completed.

For an existing integration, preserve its SDK copy, App ID, SDK secret, and coordinator. Do not
trigger registration or login merely because the project does not use this Skill's generated
configuration.

## Free-Edition Limits

- Only the official Lebo TV receiver app (乐播投屏 TV 版) is eligible; other receivers are filtered
  from search and rejected on connect.
- Only one connection at a time.
- Over a cross-network connection, local media cannot be pushed; push a URL the TV can reach.
- Mirroring runs on a real device only and needs a signing team that can register an App Group.

## Security and Privacy

- Never commit `SkillSdkConfig`, `LeboSenderSDK/skill-credentials.properties`, SDK packages,
  tokens, passwords, verification codes, platform `secret`, `md5Key`, or private keys.
- The SDK secret is the platform `md5Key`; platform `secret` must never be passed to
  `authWithAppid:secretKey:error:`.
- `+[LBLelinkKit diagnose]` output contains the app ID and device names. Review and redact it
  before sharing.

## Requirements

- Codex or Claude Code with Skill support.
- macOS with a full Xcode installation.
- Python 3 with the standard library.
- Ruby with the `xcodeproj` library (`sudo gem install xcodeproj`, or install CocoaPods).
- An existing Xcode project with an iOS App target.
- Network access when downloading the SDK or using onboarding.

Media push works on the simulator and on devices; screen mirroring requires a real device.

## Development Checks

```bash
python3 -m py_compile scripts/*.py
ruby -c scripts/integrate_sdk.rb scripts/integrate_mirror.rb
git diff --check
```

Do not run onboarding or SDK acquisition against a real account as a repository test.
