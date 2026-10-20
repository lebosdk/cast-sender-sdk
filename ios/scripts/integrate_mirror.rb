#!/usr/bin/env ruby
# 给已接入推送的工程加屏幕镜像：新建录屏扩展 target、配 App Group、链接与嵌入镜像 framework。可重复执行，已有的不重复加。
# 用法：ruby integrate_mirror.rb --project <X.xcodeproj> --target <App target> [--team <团队 ID>] [--app-group <group.xxx>] [--extension <扩展名>] [--check]
# 默认：扩展名 LeboBroadcast；App Group 为 group.<App Bundle ID>；团队沿用 App 的 DEVELOPMENT_TEAM
# 注意：先跑 integrate_sdk.rb 接入推送；镜像只能真机运行，签名需要能注册 App Group 的开发者团队
require "xcodeproj"
# 注意：终端未设 UTF-8 时按 US-ASCII 读文件，Info.plist 含中文会报 invalid byte sequence
Encoding.default_external = Encoding::UTF_8
require "optparse"
require "fileutils"

opts = { check: false, extension: "LeboBroadcast" }
OptionParser.new do |o|
  o.on("--project PATH") { |v| opts[:project] = v }
  o.on("--target NAME") { |v| opts[:target] = v }
  o.on("--team ID") { |v| opts[:team] = v }
  o.on("--app-group ID") { |v| opts[:app_group] = v }
  o.on("--extension NAME") { |v| opts[:extension] = v }
  o.on("--check") { opts[:check] = true }
end.parse!
abort("需要 --project 与 --target") unless opts[:project] && opts[:target]

SDK_DIR = "LeboSenderSDK"
APP_FRAMEWORKS = %w[LBReplayAppKit NERtcSDK TXLiteAVSDK_TRTC TXFFmpeg TXSoundTouch]
EXT_FRAMEWORKS = %w[LBReplayKitExtension LBReplayKit LBSREncoder NERtcReplayKit TXLiteAVSDK_ReplayKitExt]
# 动态库，嵌入 App 的 Frameworks 目录；扩展从 @executable_path/../../Frameworks 加载 NERtcReplayKit
EMBEDDED = %w[NERtcSDK TXFFmpeg TXSoundTouch NERtcReplayKit]
APP_SYSTEM_FRAMEWORKS = %w[ReplayKit AVKit CoreMotion MetalPerformanceShaders Accelerate]
APP_SYSTEM_LIBS = %w[c++ z sqlite3 xml2 resolv]
EXT_SYSTEM_FRAMEWORKS = %w[ReplayKit MediaPlayer]
EXT_SYSTEM_LIBS = %w[c++ z sqlite3 xml2]
TEMPLATE_DIR = File.expand_path("../examples/Mirror", __dir__)

project_path = File.expand_path(opts[:project])
project_dir = File.dirname(project_path)
project = Xcodeproj::Project.open(project_path)
app = project.native_targets.find { |t| t.name == opts[:target] }
abort("工程里没有 target：#{opts[:target]}") unless app
abort("先运行 obtain_sdk.py 安装含镜像的 SDK：缺少 #{SDK_DIR}/Mirror") unless File.directory?(File.join(project_dir, SDK_DIR, "Mirror", "Extension"))
abort("先运行 integrate_sdk.rb 接入推送") unless app.frameworks_build_phase.files_references.compact.any? { |r| r.path.to_s.end_with?("LBLelinkKit.xcframework") }

release = app.build_configurations.find { |c| c.name == "Release" } || app.build_configurations.first
bundle_id = release.build_settings["PRODUCT_BUNDLE_IDENTIFIER"].to_s
team = opts[:team] || release.build_settings["DEVELOPMENT_TEAM"].to_s
abort("App 没有设置签名团队，用 --team 指定") if team.empty?
app_group = opts[:app_group] || (bundle_id.include?("$") ? nil : "group.#{bundle_id}")
abort("Bundle ID 含变量，用 --app-group 指定 App Group") unless app_group
ext_name = opts[:extension]
changes = []

# 在 LeboSenderSDK 分组下找或建文件引用，路径相对工程目录
sdk_group = project.main_group.find_subpath(SDK_DIR, true)
sdk_group.set_source_tree("<group>")
sdk_group.set_path(SDK_DIR)
ref_for = lambda do |rel|
  sdk_group.files.find { |f| f.path == rel } || sdk_group.new_reference(rel)
end
xcframework_ref = sdk_group.files.find { |f| f.path.to_s.end_with?("LBLelinkKit.xcframework") }

linked = ->(target, name) { target.frameworks_build_phase.files_references.compact.any? { |r| File.basename(r.path.to_s, ".*") == name } }
add_frameworks = lambda do |target, names, dir|
  names.each do |name|
    next if linked.call(target, name)
    changes << "#{target.name} 链接 #{name}"
    target.frameworks_build_phase.add_file_reference(ref_for.call("Mirror/#{dir}/#{name}.framework"), true) unless opts[:check]
  end
end
add_system = lambda do |target, frameworks, libs|
  frameworks.each do |name|
    next if linked.call(target, name)
    changes << "#{target.name} 链接 #{name}.framework"
    target.add_system_framework(name) unless opts[:check]
  end
  libs.each do |name|
    next if linked.call(target, "lib#{name}")
    changes << "#{target.name} 链接 lib#{name}.tbd"
    target.add_system_library_tbd(name) unless opts[:check]
  end
end
add_list_setting = lambda do |target, key, values|
  target.build_configurations.each do |c|
    current = c.build_settings[key]
    current = current.split if current.is_a?(String)
    current = ["$(inherited)"] if current.nil? || current.empty?
    missing = values - current
    next if missing.empty?
    changes << "#{target.name} #{c.name} #{key} 加 #{missing.join(' ')}"
    c.build_settings[key] = current + missing unless opts[:check]
  end
end
# 写入 entitlements 的 App Group；文件不存在就新建并设为 CODE_SIGN_ENTITLEMENTS
add_app_group = lambda do |target, default_rel|
  rel = target.build_configurations.map { |c| c.build_settings["CODE_SIGN_ENTITLEMENTS"] }.compact.first || default_rel
  path = File.join(project_dir, rel)
  ent = File.exist?(path) ? Xcodeproj::Plist.read_from_path(path) : {}
  groups = ent["com.apple.security.application-groups"] || []
  unless groups.include?(app_group)
    changes << "#{target.name} entitlements 加 App Group #{app_group}"
    unless opts[:check]
      FileUtils.mkdir_p(File.dirname(path))
      ent["com.apple.security.application-groups"] = groups + [app_group]
      Xcodeproj::Plist.write_to_path(ent, path)
    end
  end
  target.build_configurations.each do |c|
    next if c.build_settings["CODE_SIGN_ENTITLEMENTS"] == rel
    changes << "#{target.name} #{c.name} 设置 CODE_SIGN_ENTITLEMENTS" if c.build_settings["CODE_SIGN_ENTITLEMENTS"].nil?
    c.build_settings["CODE_SIGN_ENTITLEMENTS"] = rel unless opts[:check]
  end
end

# 1. 录屏扩展 target
ext = project.native_targets.find { |t| t.name == ext_name }
if ext.nil?
  changes << "新建录屏扩展 target #{ext_name}（#{bundle_id}.#{ext_name}）"
  unless opts[:check]
    ext = project.new_target(:app_extension, ext_name, :ios, "12.0", nil, :objc)
    ext_dir = File.join(project_dir, ext_name)
    FileUtils.mkdir_p(ext_dir)
    File.write(File.join(ext_dir, "SampleHandler.h"), File.read(File.join(TEMPLATE_DIR, "SampleHandler.h")))
    File.write(File.join(ext_dir, "SampleHandler.m"), File.read(File.join(TEMPLATE_DIR, "SampleHandler.m")).gsub("__LEBO_APP_GROUP_ID__", app_group))
    app_info = File.join(project_dir, release.build_settings["INFOPLIST_FILE"].to_s)
    app_plist = File.file?(app_info) ? Xcodeproj::Plist.read_from_path(app_info) : {}
    Xcodeproj::Plist.write_to_path({
      "CFBundleDevelopmentRegion" => "$(DEVELOPMENT_LANGUAGE)",
      "CFBundleDisplayName" => "投屏镜像",
      "CFBundleExecutable" => "$(EXECUTABLE_NAME)",
      "CFBundleIdentifier" => "$(PRODUCT_BUNDLE_IDENTIFIER)",
      "CFBundleInfoDictionaryVersion" => "6.0",
      "CFBundleName" => "$(PRODUCT_NAME)",
      "CFBundlePackageType" => "$(PRODUCT_BUNDLE_PACKAGE_TYPE)",
      "CFBundleShortVersionString" => app_plist["CFBundleShortVersionString"] || "$(MARKETING_VERSION)",
      "CFBundleVersion" => app_plist["CFBundleVersion"] || "$(CURRENT_PROJECT_VERSION)",
      "NSAppTransportSecurity" => { "NSAllowsArbitraryLoads" => true },
      "NSExtension" => {
        "NSExtensionPointIdentifier" => "com.apple.broadcast-services-upload",
        "NSExtensionPrincipalClass" => "SampleHandler",
        "RPBroadcastProcessMode" => "RPBroadcastProcessModeSampleBuffer",
      },
    }, File.join(ext_dir, "Info.plist"))
    group = project.main_group.new_group(ext_name, ext_name)
    ext.add_file_references([group.new_file("SampleHandler.m")])
    group.new_file("SampleHandler.h")
    group.new_file("Info.plist")
    ext.build_configurations.each do |c|
      s = c.build_settings
      s["PRODUCT_BUNDLE_IDENTIFIER"] = "#{bundle_id}.#{ext_name}"
      s["PRODUCT_NAME"] = "$(TARGET_NAME)"
      s["INFOPLIST_FILE"] = "#{ext_name}/Info.plist"
      s["DEVELOPMENT_TEAM"] = team
      s["CODE_SIGN_STYLE"] = "Automatic"
      s["SKIP_INSTALL"] = "YES"
      s["ENABLE_BITCODE"] = "NO"
      s["TARGETED_DEVICE_FAMILY"] = "1,2"
      %w[MARKETING_VERSION CURRENT_PROJECT_VERSION].each { |k| s[k] = release.build_settings[k] if release.build_settings[k] }
      s["LD_RUNPATH_SEARCH_PATHS"] = ["$(inherited)", "@executable_path/Frameworks", "@executable_path/../../Frameworks"]
    end
  end
end

unless opts[:check] && ext.nil?
  add_list_setting.call(ext, "OTHER_LDFLAGS", ["-ObjC"])
  add_list_setting.call(ext, "FRAMEWORK_SEARCH_PATHS", ["$(PROJECT_DIR)/#{SDK_DIR}/Mirror/Extension"])
  add_frameworks.call(ext, EXT_FRAMEWORKS, "Extension")
  if xcframework_ref && !linked.call(ext, "LBLelinkKit")
    changes << "#{ext_name} 链接 LBLelinkKit.xcframework"
    ext.frameworks_build_phase.add_file_reference(xcframework_ref, true) unless opts[:check]
  end
  add_system.call(ext, EXT_SYSTEM_FRAMEWORKS, EXT_SYSTEM_LIBS)
  add_app_group.call(ext, "#{ext_name}/#{ext_name}.entitlements")
end

# 2. App target：链接、嵌入动态库与扩展、App Group、签名团队
add_list_setting.call(app, "FRAMEWORK_SEARCH_PATHS", ["$(PROJECT_DIR)/#{SDK_DIR}/Mirror/App", "$(PROJECT_DIR)/#{SDK_DIR}/Mirror/Extension"])
add_list_setting.call(app, "LD_RUNPATH_SEARCH_PATHS", ["@executable_path/Frameworks"])
add_frameworks.call(app, APP_FRAMEWORKS, "App")
# 注意：App 端的网易云镜像也用到 NERtcReplayKit 里的 NEScreenShareHost
add_frameworks.call(app, %w[NERtcReplayKit], "Extension")
add_system.call(app, APP_SYSTEM_FRAMEWORKS, APP_SYSTEM_LIBS)

embed = app.copy_files_build_phases.find { |p| p.symbol_dst_subfolder_spec == :frameworks }
embedded = embed ? embed.files_references.compact.map { |r| File.basename(r.path.to_s, ".*") } : []
EMBEDDED.each do |name|
  next if embedded.include?(name)
  changes << "#{app.name} 嵌入 #{name}.framework（Embed & Sign）"
  next if opts[:check]
  embed ||= app.new_copy_files_build_phase("Embed Frameworks").tap { |p| p.symbol_dst_subfolder_spec = :frameworks }
  dir = EXT_FRAMEWORKS.include?(name) ? "Extension" : "App"
  bf = embed.add_file_reference(ref_for.call("Mirror/#{dir}/#{name}.framework"), true)
  bf.settings = { "ATTRIBUTES" => %w[CodeSignOnCopy RemoveHeadersOnCopy] }
end

if ext
  plugins = app.copy_files_build_phases.find { |p| p.symbol_dst_subfolder_spec == :plug_ins }
  unless plugins && plugins.files_references.compact.include?(ext.product_reference)
    changes << "#{app.name} 嵌入录屏扩展 #{ext_name}.appex"
    unless opts[:check]
      plugins ||= app.new_copy_files_build_phase("Embed Foundation Extensions").tap { |p| p.symbol_dst_subfolder_spec = :plug_ins }
      plugins.add_file_reference(ext.product_reference, true).settings = { "ATTRIBUTES" => ["RemoveHeadersOnCopy"] }
    end
  end
  unless app.dependencies.any? { |d| d.target == ext }
    changes << "#{app.name} 依赖 #{ext_name}"
    app.add_dependency(ext) unless opts[:check]
  end
end

app.build_configurations.each do |c|
  next unless c.build_settings["DEVELOPMENT_TEAM"].to_s.empty?
  changes << "#{app.name} #{c.name} 签名团队设为 #{team}"
  c.build_settings["DEVELOPMENT_TEAM"] = team unless opts[:check]
end
add_app_group.call(app, "#{app.name}/#{app.name}.entitlements")

# 3. App 端 App Group 常量，供 LBLelinkMirrorEngine / LBLelinkKit setAppGroupId 使用
app_src = File.dirname(File.join(project_dir, release.build_settings["INFOPLIST_FILE"].to_s))
config_h = File.join(app_src, "LeboMirrorConfig.h")
content = "// 由 integrate_mirror.rb 生成：与录屏扩展相同的 App Group\n#import <Foundation/Foundation.h>\n\nstatic NSString * const LeboMirrorAppGroupId = @\"#{app_group}\";\nstatic NSString * const LeboMirrorExtensionBundleId = @\"#{bundle_id}.#{ext_name}\";\n"
unless File.exist?(config_h) && File.read(config_h) == content
  changes << "生成 #{config_h.sub(project_dir + '/', '')}"
  File.write(config_h, content) unless opts[:check]
end

if changes.empty?
  puts "镜像已接入，无需改动：#{app.name} + #{ext_name}（App Group #{app_group}）"
elsif opts[:check]
  puts "待接入项：", changes.map { |c| "  - #{c}" }
  exit 1
else
  project.save
  puts "已接入镜像（App Group #{app_group}，团队 #{team}）：", changes.map { |c| "  - #{c}" }
end
