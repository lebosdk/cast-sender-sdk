# Marketplace metadata

## Name

iOS Sender SDK Integration

## Summary

帮助编码助手在已有 iOS 工程里检查构建环境、安装乐播发送端免费版 SDK、申请并安全配置 App 凭据，完成设备搜索、连接、媒体推送、播控和屏幕镜像接入，并处理免费版的收端限制与排障。

## Recommended use

当用户需要在 iOS App 里接入乐播发送端 SDK、实现设备搜索或投屏推送、接入屏幕镜像（录屏扩展），或处理非乐播投屏 TV 版收端、跨网本地文件限制、蓝牙发现跨网设备等问题时启用。

## Exclusions

不用于 iOS 接收端开发、TV APK 开发、Android 接入、SDK 服务端接口实现，不新建 iOS 工程，也不生成正式 SDK 产物。

## Included resources

- `SKILL.md`
- `scripts/`：环境检查、SDK 安装、推送接入、镜像接入（录屏扩展、App Group），以及 App 凭据申请和安全落盘脚本
- `references/`：SDK 产物、安装配置、凭据、API、搜索连接、错误处理、增量接入、镜像和验收指导
- `examples/`：Objective-C 推送协调者与镜像控制器、录屏扩展模板、Swift 写法

## Current version

See `VERSION` and `CHANGELOG.md`. Version `0.2.3` downloads the SDK from the CDN instead of shipping it inside the Skill. Version `0.2.0` added screen mirroring through a Broadcast Upload Extension, Bluetooth discovery of receivers outside the Wi-Fi, and connection by cast code.

## Required publisher decisions

发布前仍需填写维护者、许可证、支持渠道和兼容平台，并确认市场安装方式。凭据脚本已内置稳定的 `src`，不作为注册前置条件。凭据脚本使用正式平台 `https://openplat.hpplay.cn`。SDK 由 `obtain_sdk.py` 从 `https://lebotob.hpplay.cn/sdk/iOS/Release/ios-sender-sdk.zip` 下载，发布方需保证该地址始终是最新的正式环境免费版包。
