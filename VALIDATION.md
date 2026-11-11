# 帧幕本地验证记录

## 0.2.0：Windows 原生摄像头

日期：2026-11-11。Windows 11 x64，内核 build 26200。本节记录同一台机器的结果，不表示已覆盖所有系统、硬件或会议客户端。

- 首次管理员注册成功，安装进程退出码为 0。原生媒体源注册指向 `%ProgramData%\Frameveil\Native` 的固定内容哈希目录；之后宿主和接收测试均以普通用户运行。
- 原生设备名称为 **Frameveil Camera (Windows Virtual Camera)**。输出开启时通过 Windows Media Foundation 枚举；停止输出后结束会话。旧 OBS/Unity DirectShow 路径保留。
- `python tools/validate_native.py` 通过：发送自制彩色测试卡，由另一个独立进程按 Frameveil 设备名称读取 NV12 帧。1280×720（1,382,400 字节）、640×480（460,800 字节）、1920×1080（3,110,400 字节）均取得正确长度、非黑画面。
- 720p 接收帧与原测试卡的平均像素绝对误差为 **0.347/255**，包含 RGB/NV12 转换误差；640×480 对 16:9 输入保留上下留边。
- 运行中改为黑屏后，独立接收帧的所有 RGB 分量均为 **0**。
- 修复接收探针退出时 COM 对象释放顺序引起的崩溃；修正后完整接收测试正常退出。媒体源修复了状态判断、重启媒体类型读取和 NV12 步幅，传输使用完整帧发布检查。
- 13 项自动检查通过：9 项媒体引擎检查及 4 项原生帧传输检查。这里的单元检查不能替代真实会议验收。
- 便携 GUI 0.2 实际启动成功，并导出界面截图 `artifacts/Frameveil-0.2-preview.png`。原生组件和接收探针已与便携目录同步。
- 用户完成 Windows 原生设备客户端实测：微信反馈“设备出现，画面正常”；钉钉反馈“画面正常，没有报错”。本机此前记录的客户端版本为微信 4.2.0.13、钉钉 8.5.5.260903002。原先的微信不枚举、钉钉打开报错问题，已在本机通过切换 Frameveil 原生路径验证解决。

接收证据：`artifacts/native-validation.json`、`native-1280x720.png`、`native-640x480.png`、`native-1920x1080.png`、`native-blackout.png` 及对应 NV12 原始帧。测试只发送生成的测试卡，没有访问实体摄像头或麦克风。

**仍待验证**：真实会议的远端接收、长时间轮播/视频与开关恢复；全新无开发工具的 Windows 机器；Windows 10 DirectShow 回归；其他 CPU/GPU/驱动组合；长期性能、N/精简版和多用户并发。本机客户端显示通过来自用户反馈，尚未确认远端接收，也未证明旧 OBS/Unity 路径在这两个客户端中可用。

原生媒体源 SHA-256：`210dd8f9721e0bc9805f334cbe9eca34887be5c6aceb3a380a4409deee0ea6b9`。全部原生组件校验值见 `vendor/native/manifest.json`，发行包校验值见 `release/SHA256.json`。

## 0.1.0：历史 DirectShow 结果

日期：2026-11-10。Windows 11（内核 build 26200），Python 3.11.9 开发环境；成品包含独立运行环境。

- 9 项引擎检查通过：轮播与结束、暂停、黑屏恢复、淡入淡出、比例/镜像、中文路径视频、定位/速度/循环、随机单轮结束、损坏素材处理、暂停时切换素材（部分用例组合覆盖）。
- 实际 GUI 窗口检查：中文三栏布局、稳定约 30 FPS 预览、开启输出、黑屏、退出释放设备。
- 独立 EXE 实际启动通过。已修正构建机 PATH 中 Poppler ICU 被错误打包的问题；移除该非应用依赖，使用 Windows 自带 ICU API；统一 Qt 配套 MSVC 运行库。此修正纳入 build.ps1 流程。
- 从成品 GUI 开启 OBS Virtual Camera，以独立 FFmpeg DirectShow 进程按设备名接收：1280×720 RGB 画面成功；与输入演示图平均像素误差 2.041/255（含颜色空间转换）。证据：artifacts/camera-received.png、同名 JSON。
- 从成品 GUI 开启黑屏：独立接收画面所有像素为 0。证据：artifacts/camera-blackout.png、同名 JSON。
- Unity Capture 内置 32/64 位 DLL 的 SHA-256 校验通过，来源为官方固定提交的 HTTPS 源码归档；没有修改 DLL。

尚未验证：钉钉/微信的真实会议及远端接收、Unity Capture 首次管理员注册与卸载流程、无开发工具的全新 Windows 机器、60 FPS/1080p 持续性能。

本机已有 OBS Virtual Camera，本次复用了它，没有注册额外系统摄像头，没有访问真实摄像头或麦克风，没有发起会议或对外发送素材。

本地 DirectShow 接收成功不代表所有会议客户端都支持此设备。请按 README 的验收步骤完成客户端测试。
