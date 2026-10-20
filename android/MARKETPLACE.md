# Marketplace metadata

## Name

Cast Sender SDK Integration

## Summary

帮助编码助手选择或创建 Android 工程、自动准备构建环境、获取 SDK AAR、申请并安全配置 App 凭据，并完成发送端 SDK 集成、投屏能力和排障。

## Recommended use

当用户需要接入 Android 发送端 SDK、实现设备搜索或投屏、处理图片列表、连接失败和公网本地文件限制时启用。

## Exclusions

不用于 Android 接收端开发、TV APK 开发、SDK 服务端接口实现或生成正式 AAR。

## Included resources

- `SKILL.md`
- `scripts/`：Android 工程创建、构建环境准备、SDK AAR 获取，以及 App 凭据申请和安全落盘脚本
- `references/`：工程选择、构建环境、SDK 产物、API、安装、错误处理、排障和验收指导
- `examples/`：平台无关的 Java 接入片段

## Current version

See `VERSION` and `CHANGELOG.md`. Version `0.33.0` renames the Skill to `cast-sender-sdk` while preserving onboarding compatibility.

## Repository metadata

- Maintainer: the GitHub repository owner and listed contributors.
- License: MIT; see `LICENSE`.
- Support: GitHub Issues for reproducible non-sensitive problems; use the private security
  reporting process in `SECURITY.md` for vulnerabilities or credential exposure.
- Compatibility: Codex Skill environments with Python 3 and Android sender host projects.
- Installation: clone the repository so its root is the directory containing `SKILL.md`; see
  `README.md`.

凭据脚本已内置稳定的 `src`，不作为注册前置条件，并固定使用生产平台
`https://openplat.hpplay.cn`。SDK AAR 固定从
`https://lebotob.hpplay.cn/sdk/android/release/source-leboapk-release.aar` 下载；使用者
应在运行脚本前确认自己有权访问并使用这些第三方服务和 SDK 产物。
