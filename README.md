# cast-sender-sdk

HPPlay/Lelink（乐播）发送端 SDK 接入 Skill 集合，适用于 Codex 和 Claude Code。每个平台是一个独立 Skill，
各自有 `SKILL.md`、`references/`、`scripts/`、`examples/`、`VERSION` 和 `CHANGELOG.md`。

| 目录 | Skill 名 | 用途 |
| --- | --- | --- |
| [`android/`](android/README.md) | `android-sender-sdk` | Android 发送端接入 |
| [`ios/`](ios/SKILL.md) | `ios-sender-sdk` | iOS 发送端接入（推送 + 镜像） |

本仓库不包含 SDK 产物（AAR / xcframework）、平台账号凭证或任何特定应用的标识。

## Installation

先 clone 到任意位置，再把需要的平台目录链接进 Skills 目录（链接名即 Skill 名）：

```bash
git clone https://github.com/<owner>/cast-sender-sdk.git ~/src/cast-sender-sdk

# Claude Code
ln -s ~/src/cast-sender-sdk/android ~/.claude/skills/android-sender-sdk
ln -s ~/src/cast-sender-sdk/ios ~/.claude/skills/ios-sender-sdk

# Codex
ln -s ~/src/cast-sender-sdk/android ~/.codex/skills/android-sender-sdk
ln -s ~/src/cast-sender-sdk/ios ~/.codex/skills/ios-sender-sdk
```

安装后重启或重新加载会话。Claude Code 用 `/android-sender-sdk`、`/ios-sender-sdk` 调用，Codex 用
`$android-sender-sdk`、`$ios-sender-sdk` 调用；也可以直接描述接入需求自动触发。

## Development Checks

```bash
python3 -m py_compile android/scripts/*.py ios/scripts/*.py
ruby -c ios/scripts/integrate_sdk.rb ios/scripts/integrate_mirror.rb
git diff --check
```

## License

Skill 源码采用 [MIT License](LICENSE)。安全问题见 [SECURITY.md](SECURITY.md)，贡献规范见 [CONTRIBUTING.md](CONTRIBUTING.md)。
乐播 SDK、服务接口和接收端应用受其各自许可与条款约束。
