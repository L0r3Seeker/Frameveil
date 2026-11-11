# Frameveil Android：移植准备 / 0.1 研发原型

目标：在手机端微信、钉钉中使用用户选择的素材摄像头。当前提交是媒体工作台和输出接口骨架，**尚未实现其他应用的摄像头替换，不是可对外发布的安卓摄像头成品**。

已有工程代码：Android 原生 Java GUI；SAF 多选图片/视频和持久 URI 授权；最多 50 项素材；0.5–30 秒图片轮播；列表循环、暂停、上一项/下一项、镜像、黑屏预览；静音视频；设备适配报告手动导出。图片后台限尺寸解码，视频由系统 MediaPlayer/VideoView 解码。转到后台暂停，不维持后台播放或输出。

首期最低 API 26（Android 8.0），compile/target SDK 35。媒体解码能力受系统影响，优先 PNG/JPEG 和 H.264 MP4。当前尚未加入 Windows 端的转场、随机播放、视频倍速、图片 EXIF 方向修正和完整画面适配参数。

构建：Android Studio 打开本目录，使用 JDK 17 或 21、SDK Platform 35、Build Tools 35.0.0，运行 `gradlew.bat assembleDebug`。固定 AGP 8.13.2 / Gradle 8.13，Wrapper JAR 和发行版校验值记录在 `gradle/wrapper/origin.json`。Gradle 源自官方仓库，许可见 `Gradle-LICENSE.txt`。初次构建需要下载依赖。Windows 使用者不需要这套开发工具。

验证：纯 Java 播放时钟的 8 项检查通过。完整 Android API 编译情况、APK 构建及实机检查以 `VALIDATION.md` 为准；没有将静态检查当作手机测试。

## 输出适配路线

`output/CameraOutput.java` 定义生产端 Surface 接口；当前 `UnavailableOutput` 始终返回不可用。GUI 明确显示“手机摄像头输出尚未适配”，不提供虚假的输出成功状态。

1. 先在用户指定测试机上只读确认：Android 版本、ABI、厂商 ROM、Root/管理框架、Camera1/Camera2 使用方式、客户端版本和设备摄像头能力。原型可导出不含账号、序列号和素材路径的 JSON 报告，不申请真实摄像头/麦克风权限，不执行 Root 命令。
2. **系统虚拟摄像头路线**：评估 AOSP VirtualCamera / VirtualDeviceManager 能否由该 ROM 授权、是否仅对虚拟设备内应用可见、微信/钉钉是否可用。不把“服务存在”或“系统版本较新”视作可替换本机普通应用摄像头的证据。
3. **受控 Root 研究路线**：评估现有 Xposed/LSPosed 或 Camera Provider 方案的接口覆盖、授权、停止与恢复机制；分别验证 Java Camera1、Camera2 与 NDK 路径。先用独立测试应用收帧，再测试目标客户端。每个 ROM/客户端版本独立记录，不承诺装一个模块覆盖全部机型。
4. 输出有真实接收证据后，才实现后台服务、Surface 渲染与颜色/方向协商；随后接入轮播/视频，测试黑屏、异常退出、禁用恢复、长时间性能。发布 APK 前确定签名和升级策略。

本阶段没有对手机安装模块、Root、刷机或修改微信/钉钉。

## 调研记录（2026-11-11）

- [AOSP Virtual Camera](https://android.googlesource.com/platform/frameworks/av/+/refs/heads/main/services/camera/virtualcamera/README.md)：通过系统 VirtualDeviceManager 与生产端 Surface 提供摄像头；须核查权限和可见范围。
- [VirtualDeviceManager 示例](https://android.googlesource.com/platform/development/+/android16-qpr2-release/samples/VirtualDeviceManager/)：展示虚拟设备范围内的摄像头策略；不能直接推导手机默认桌面中的微信适配成功。
- [android_virtual_cam](https://github.com/Xposed-Modules-Repo/com.example.vcam)：Xposed 方案，README 记录目标应用作用域、方向/尺寸等限制；仅作为技术调研，未执行其模块。
- [Camera2Magic](https://github.com/Atomos-X/Camera2Magic/tree/magisk)：当前默认分支描述 Magisk alpha 和有限设备验证；当前元数据未声明许可证，不能据此直接复制或分发其代码/二进制。本项目未集成该仓库代码。
- [AGP 8.13 兼容表](https://developer.android.com/build/releases/agp-8-13-0-release-notes)、[Android SAF](https://developer.android.com/guide/topics/providers/document-provider) 是本工程构建及素材访问依据。

应用原创源码 GPL-3.0-or-later，使用项目根目录 LICENSE。
