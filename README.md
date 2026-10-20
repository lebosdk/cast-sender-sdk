# cast-sender-sdk

`cast-sender-sdk` is a Codex Skill for integrating an Android sender application
with the HPPlay/Lelink sender SDK. It guides the agent through project setup,
build-environment preparation, official AAR acquisition, credential onboarding,
device discovery, connection, media casting, screen mirroring, playback control,
troubleshooting, and acceptance checks.

本仓库是 Codex Skill 源码，不是 Android 接收端应用，也不包含 SDK AAR、平台账号凭证或
任何特定应用的 `applicationId`。

## What It Covers

- Detecting an existing Android application or creating a clean sender host.
- Preparing a compatible JDK, Android SDK, platform tools, and Gradle Wrapper.
- Downloading and validating the official release sender AAR when it is needed.
- Reusing existing host-managed credentials or onboarding Skill-managed credentials safely.
- Implementing discovery, QR/PIN parsing, device selection, connection, media casting,
  image/video lists, playback controls, capability checks, and ordinary-app screen mirroring.
- Preserving callback domains, numeric error codes, lifecycle state, and receiver troubleshooting.
- Verifying merged manifests, AndroidX Core, cleartext LAN metadata access, notification icons,
  USB Host filtering, R8/release behavior, and foreground mirror-service behavior.

The Skill does not implement Android receiver/TV applications, server APIs, or formal AAR
publication.

## Installation

Clone this repository into the Codex Skills directory:

```bash
git clone https://github.com/<owner>/cast-sender-sdk.git \
  ~/.codex/skills/cast-sender-sdk
```

Restart or reload the Codex session after installation. The Skill is named
`cast-sender-sdk`, so request it as `$cast-sender-sdk` or describe an Android sender SDK
integration task.

The exact path can be changed if the host environment uses a different Skills directory;
keep the repository root itself as the directory containing `SKILL.md`.

## Repository Layout

| Path | Purpose |
| --- | --- |
| `SKILL.md` | Trigger metadata, workflow, safety rules, and integration contract |
| `references/` | Project setup, environment, SDK API, installation, errors, troubleshooting, and acceptance guidance |
| `examples/` | Platform-neutral Java integration shapes |
| `scripts/create_android_project.py` | Create a minimal Android sender host after identity confirmation |
| `scripts/prepare_android_env.py` | Check or prepare JDK, Android SDK, and Gradle |
| `scripts/obtain_sdk_aar.py` | Check, download, validate, and install the official AAR |
| `scripts/onboard.py` | Check or obtain platform credentials and write ignored local configuration |
| `VERSION` / `CHANGELOG.md` | Skill release version and change history |

## Safe Workflow

The agent should inspect the target project first and classify the request as a full or
incremental integration. Read-only checks use `--check` and must run before mutating steps.
For example:

```bash
python3 scripts/prepare_android_env.py \
  --project-dir /path/to/android-project \
  --check

python3 scripts/obtain_sdk_aar.py \
  --project-dir /path/to/android-project \
  --check

python3 scripts/onboard.py \
  --project-dir /path/to/android-project \
  --app-name "Sender App" \
  --check
```

The AAR check still downloads the current artifact into a temporary location so that its
ZIP structure and checksum can be validated; it does not install it into the project.
Onboarding `--check` does not send SMS, authenticate, create an application, or write
credentials. Only run mutating commands after the required user confirmations described in
`SKILL.md` have completed.

For an existing integration, preserve its working AAR, App ID, SDK App Secret, coordinator,
discovery flow, and casting capabilities. Do not trigger registration or login merely because
the project does not use this Skill's generated configuration.

## Security and Privacy

- Never commit `local.properties`, `SkillSdkConfig.java`, AARs, tokens, passwords, verification
  codes, platform `secret`, `md5Key`, or private keys.
- Skill-generated SDK configuration maps `APP_ID` to platform `appId` and `APP_SECRET` to
  platform `md5Key`; platform `secret` must never be passed to SDK initialization.
- Credentials and resumable onboarding state are local files. Review `git status` and
  `git diff --cached` before every push.
- `diagnose()` output can contain app and device information. Review and redact it before
  uploading logs or opening a public issue.
- Screen mirroring in an ordinary Android application uses MediaProjection consent. Do not
  enable system capture merely to suppress the consent dialog.
- The sender SDK reads receiver metadata over the LAN. The host application must explicitly
  allow the required cleartext metadata access and should review the merged Manifest.

See [SECURITY.md](SECURITY.md) for vulnerability reporting guidance.

## Requirements

- Codex with Skill support.
- Python 3 with the standard library; the scripts have no third-party Python dependency.
- An Android application project for integration, or an empty working directory for creation.
- Network access when downloading the official AAR, Android tools, Gradle, or using onboarding.
- Android SDK licenses must be reviewed and accepted by the developer when requested.

The scripts do not require a globally installed Gradle, JDK, or Android SDK in advance; the
environment workflow can reuse or prepare user-local tools. It must not place machine-specific
paths or credentials in tracked files.

## Development Checks

Before submitting repository changes, run:

```bash
python3 -m py_compile scripts/*.py
git diff --check
```

Do not run onboarding or artifact acquisition against a real account as a repository test.
Use isolated temporary projects and `--check` for read-only validation.

## License and Third-Party Services

The Skill source is available under the [MIT License](LICENSE). The HPPlay/Lelink Android
sender SDK, its service endpoints, Android dependencies, and any receiver applications remain
subject to their own licenses and terms. This repository does not grant rights to redistribute
those third-party artifacts.
