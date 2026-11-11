# 帧幕 0.2：系统要求与适配范围

本文件区分设计覆盖范围、已经完成的测试和仍需实机验证的部分。操作系统支持不等于某个会议客户端必然支持所有虚拟摄像头。

| 平台 | 输出路径 | 当前状态 |
| --- | --- | --- |
| Windows 11 x64，build 22000+ | Frameveil Camera，系统 Media Foundation 虚拟摄像头 | build 26200 实机注册、三种分辨率独立接收及黑屏通过；用户确认本机微信、钉钉正常显示 |
| Windows 10 x64，1809+ | Unity Capture / OBS，DirectShow | 保留路径；本机完成 DirectShow 接收测试，未在 Windows 10 实机完成回归 |
| Windows 7 / 8 / 8.1 | 无 | 当前 Qt/Python 成品不支持 |
| Windows ARM64 | 尚无原生 ARM64 成品 | 不承诺 x64 仿真环境下的摄像头组件兼容性 |
| macOS / Linux | 可复用媒体时间轴，输出与打包需要另行适配 | 未提供成品 |
| Android | 原生 Java 媒体工作台骨架；系统摄像头输出待适配 | 已建立工程并完成 Java/API 编译检查，未提供 APK、未做手机实测 |

## 硬件和安装要求

- CPU：Intel/AMD x86-64。兼容预设以 720p/30 FPS 为目标；较慢机器先用 640×480。没有依赖 CUDA 或独立显卡。CPU 合成不代表已经覆盖所有处理器及驱动组合。
- 内存：建议 4 GB 或更多；这是使用建议，尚无低内存设备压测结果。
- 磁盘：预留 600 MB 给便携程序、组件和日志，另加用户素材占用。原生传输缓冲约 8 MB。
- 使用者不需要安装 Python、Visual Studio、编译器或配置 PATH。
- 预览无需管理员权限；首次注册系统摄像头 COM 组件需要 Windows 管理员授权。普通使用以非管理员运行。
- Windows 原生后端需要系统的 Media Foundation / Camera Frame Server 能力；N/精简版或禁用了媒体组件的系统需单独验证，不能直接按标准版推定兼容。
- Windows 原生路径当前协商 30 FPS，提供 640×480、1280×720、1920×1080，NV12/RGB32；DirectShow 另有其他帧率设置。
- 当前原生传输每台电脑支持一个发送实例；多用户会话并发尚未验证。
- 界面最低逻辑工作区 900×520；小屏自动采用较窄侧栏，中间工作台可滚动。高 DPI 缩放后若逻辑分辨率低于此范围，不保证完整布局。

## 钉钉、微信的验证边界

已记录的问题：钉钉 8.5.5.260903002 打开 OBS Virtual Camera 失败；微信 4.2.0.13 未显示 DirectShow 虚拟设备（用户反馈）。本机检查确认 OBS/Unity 的 32/64 位 COM 注册路径有效，两个客户端均为 x64，因此组件位数不是已发现的根因。

新增 Windows 11 原生路径是针对现代摄像头枚举/接收接口的兼容性改动。2026-11-11，用户按原生路径完成本机测试：

| 客户端（本机此前记录版本） | 设备 | 用户反馈 | 已确认范围 |
| --- | --- | --- | --- |
| 微信 4.2.0.13 x64 | Frameveil Camera (Windows Virtual Camera) | 设备出现，画面正常 | 设备枚举与客户端显示通过 |
| 钉钉 8.5.5.260903002 x64 | Frameveil Camera (Windows Virtual Camera) | 画面正常，没有报错 | 客户端打开与显示通过 |

远端接收及长时间运行尚未确认；其他客户端版本、系统和机型仍需回归。本次验证解决了本机原问题，但没有将旧 OBS/Unity 路径标记为这两个客户端兼容，也没有将单机结果扩大为全平台保证。

测试应记录：Windows 版本/build、CPU、显卡/驱动、客户端完整版本、所选设备名、是否枚举、是否能预览、远端是否可见、开关恢复情况。优先使用自己的测试账号和设备。

## 安卓后续路线

可复用的部分：素材列表、播放时间轴、缩放/镜像/轮播参数和测试用例。GUI、解码、生命周期与摄像头输出采用平台适配层重新实现；Windows COM DLL 不能直接移入 APK。

已建立 `android/` 原生工程，提供素材导入/预览、图片轮播、静音视频、暂停/镜像/黑屏和设备报告导出代码，输出接口明确返回尚未实现。移植目标已按用户选择确定为手机端微信/钉钉；下一步需基于首台手机的系统、Root/框架和客户端信息验证输出路线，详见 `android/README.md`。

安卓 Camera2 是应用访问系统摄像头的接口。面向其他普通应用提供新摄像头，涉及 Camera Provider/HAL 和系统集成，不能承诺普通免 Root APK 可直接替换微信/钉钉的摄像头输入。后续需要分别评估：手机作为电脑的视频来源、应用明确支持的输入接口，以及具备系统集成权限的设备。当前没有做 Root、系统刷写或应用注入。

依据：[Qt 6.11 Windows 构建与平台表](https://doc.qt.io/qt-6.11/windows-building.html)、[Microsoft IMFVirtualCamera](https://learn.microsoft.com/en-us/windows/win32/api/mfvirtualcamera/nn-mfvirtualcamera-imfvirtualcamera)、[Android Camera Provider/HAL 集成](https://source.android.com/docs/core/camera/external-usb-cameras)。这些资料描述平台接口，不能代替帧幕的实机兼容性测试。
