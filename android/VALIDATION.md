# 安卓移植准备验证

2026-11-11。尚未连接手机或安装 APK。

- `PlaylistClockTest` 8 项检查通过：到时切换、暂停保留剩余时长、恢复时刻、视频完成切换、循环、单轮停止、空列表和间隔下限。
- Gradle/AGP 版本按官方兼容表固定；Wrapper 原始 JAR 校验后保留来源与 SHA-256。
- 全部 Java 源文件使用官方 Android SDK Platform 35 的 android.jar 完成编译检查（Java 17 目标字节码），无编译错误；仅有旧 API/编译器选项提示。SDK 归档与 Google 仓库目录中的 SHA-1 一致。
- AndroidManifest、主题和图标 XML 语法检查通过。这不包含 aapt 资源链接、Gradle 整体构建或 APK 安装验证。
- GUI、Android 生命周期、视频解码、SAF 持久授权、设备报告导出尚需 APK 构建与手机实测。
- CameraOutput 是接口，当前实现明确不可用，没有实现手机微信/钉钉虚拟摄像头。

验收时依次检查：导入/重启恢复 → 图片轮播/暂停/循环 → 静音 MP4 → 前后台切换 → 报告导出。系统输出适配单独建立只读基线与恢复方案，不能用本地预览通过替代目标客户端接收测试。
