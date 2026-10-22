#!/usr/bin/env ruby
# 把 LeboSenderSDK/LBLelinkKit.xcframework 接入指定 App target，可重复执行，已有的配置不重复添加。
# 用法：ruby integrate_sdk.rb --project <X.xcodeproj> --target <App target> [--camera] [--check]
# 改动：链接 xcframework（静态库，不嵌入）与 MediaPlayer.framework；OTHER_LDFLAGS 加 -ObjC；
#      Info.plist 加本地网络说明、蓝牙说明、Bonjour 服务 _leboremote._tcp、ATS 允许 HTTP 明文；
#      --camera 时再加相机说明（扫码连接用）。
# 注意：--check 只报告缺什么，不改工程。
require "xcodeproj"
# 注意：终端未设 UTF-8 时按 US-ASCII 读文件，Info.plist 含中文会报 invalid byte sequence
Encoding.default_external = Encoding::UTF_8
require "optparse"

opts = { check: false, camera: false }
OptionParser.new do |o|
  o.on("--project PATH") { |v| opts[:project] = v }
  o.on("--target NAME") { |v| opts[:target] = v }
  o.on("--camera") { opts[:camera] = true }
  o.on("--check") { opts[:check] = true }
end.parse!
abort("需要 --project 与 --target") unless opts[:project] && opts[:target]

FRAMEWORK_REL = "LeboSenderSDK/LBLelinkKit.xcframework"
BONJOUR = "_leboremote._tcp"
LOCAL_NETWORK_TEXT = "用于在局域网内搜索并连接电视进行投屏"
BLUETOOTH_TEXT = "用于发现附近可投屏的电视"
CAMERA_TEXT = "用于扫描电视上的二维码连接投屏"

project_path = File.expand_path(opts[:project])
project_dir = File.dirname(project_path)
project = Xcodeproj::Project.open(project_path)
target = project.native_targets.find { |t| t.name == opts[:target] }
abort("工程里没有 target：#{opts[:target]}") unless target
abort("先运行 obtain_sdk.py 安装 SDK：缺少 #{FRAMEWORK_REL}") unless File.directory?(File.join(project_dir, FRAMEWORK_REL))

changes = []

# 1. 链接 xcframework
phase = target.frameworks_build_phase
linked = phase.files_references.compact.map { |r| r.path.to_s }
unless linked.any? { |p| p.end_with?("LBLelinkKit.xcframework") }
  changes << "链接 LBLelinkKit.xcframework"
  unless opts[:check]
    group = project.main_group.find_subpath("LeboSenderSDK", true)
    group.set_source_tree("<group>")
    group.set_path("LeboSenderSDK")
    ref = group.files.find { |f| f.path == "LBLelinkKit.xcframework" } || group.new_reference("LBLelinkKit.xcframework")
    phase.add_file_reference(ref, true)
  end
end

# 2. 链接 MediaPlayer.framework（静态库自动链接没带上它）
unless linked.any? { |p| p.end_with?("MediaPlayer.framework") }
  changes << "链接 MediaPlayer.framework"
  target.add_system_framework("MediaPlayer") unless opts[:check]
end

# 3. -ObjC：静态库里的分类和只靠运行时查找的类要整体链入
target.build_configurations.each do |config|
  flags = config.build_settings["OTHER_LDFLAGS"]
  flags = flags.split if flags.is_a?(String)
  flags = ["$(inherited)"] if flags.nil? || flags.empty?
  next if flags.include?("-ObjC")
  changes << "#{config.name} OTHER_LDFLAGS 加 -ObjC"
  config.build_settings["OTHER_LDFLAGS"] = flags + ["-ObjC"] unless opts[:check]
end

# 4. Info.plist：没有 INFOPLIST_FILE 时新建一个，与 Xcode 生成的 Info.plist 合并
plist_rel = target.build_configurations.map { |c| c.build_settings["INFOPLIST_FILE"] }.compact.first
if plist_rel.nil?
  plist_rel = "#{target.name}/Info.plist"
  changes << "新建 #{plist_rel} 并设为 INFOPLIST_FILE"
  unless opts[:check]
    path = File.join(project_dir, plist_rel)
    Xcodeproj::Plist.write_to_path({}, path) unless File.exist?(path)
    target.build_configurations.each { |c| c.build_settings["INFOPLIST_FILE"] = plist_rel }
  end
end
plist_path = File.join(project_dir, plist_rel.gsub("$(SRCROOT)/", "").gsub("$(PROJECT_DIR)/", ""))
plist = File.exist?(plist_path) ? Xcodeproj::Plist.read_from_path(plist_path) : {}
plist_changed = false
unless plist["NSLocalNetworkUsageDescription"]
  changes << "Info.plist 加 NSLocalNetworkUsageDescription"
  plist["NSLocalNetworkUsageDescription"] = LOCAL_NETWORK_TEXT
  plist_changed = true
end
# 注意：没有蓝牙说明时系统不允许蓝牙扫描，跨网的官方收端就发现不了
unless plist["NSBluetoothAlwaysUsageDescription"]
  changes << "Info.plist 加 NSBluetoothAlwaysUsageDescription"
  plist["NSBluetoothAlwaysUsageDescription"] = BLUETOOTH_TEXT
  plist_changed = true
end
# 注意：没有相机说明时打开摄像头会直接崩溃
if opts[:camera] && !plist["NSCameraUsageDescription"]
  changes << "Info.plist 加 NSCameraUsageDescription"
  plist["NSCameraUsageDescription"] = CAMERA_TEXT
  plist_changed = true
end
services = plist["NSBonjourServices"] || []
unless services.include?(BONJOUR)
  changes << "Info.plist NSBonjourServices 加 #{BONJOUR}"
  plist["NSBonjourServices"] = services + [BONJOUR]
  plist_changed = true
end
# 注意：SDK 跨网播控（含停止镜像）走 http://<IP> 推送，必须 NSAllowsArbitraryLoads；
#      同时存在 NSAllowsLocalNetworking 等键时系统会忽略 NSAllowsArbitraryLoads，所以一并去掉
ats = plist["NSAppTransportSecurity"] || {}
ATS_OVERRIDES = %w[NSAllowsLocalNetworking NSAllowsArbitraryLoadsInWebContent NSAllowsArbitraryLoadsForMedia]
unless ats["NSAllowsArbitraryLoads"] == true && (ats.keys & ATS_OVERRIDES).empty?
  changes << "Info.plist ATS 设 NSAllowsArbitraryLoads（去掉 #{ATS_OVERRIDES.join('/')}）"
  plist["NSAppTransportSecurity"] = ats.reject { |k, _| ATS_OVERRIDES.include?(k) }.merge("NSAllowsArbitraryLoads" => true)
  plist_changed = true
end
Xcodeproj::Plist.write_to_path(plist, plist_path) if plist_changed && !opts[:check]

if changes.empty?
  puts "已接入，无需改动：#{target.name}"
elsif opts[:check]
  puts "待接入项：", changes.map { |c| "  - #{c}" }
  exit 1
else
  project.save
  puts "已接入 #{target.name}：", changes.map { |c| "  - #{c}" }
end
