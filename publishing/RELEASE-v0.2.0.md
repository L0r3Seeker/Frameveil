# 帧幕 Frameveil 0.2.0 · Windows x64

图片、幻灯片和视频作为虚拟摄像头画面，中文 GUI，完整便携运行环境。

普通用户下载 **Frameveil-0.2.0-Windows-x64.zip**，完整解压，先阅读“开始使用.html”，再运行 Frameveil.exe。无需安装 Python、Qt 或完整 OBS。

Windows 11 首次在“摄像头组件管理”安装 Windows 原生组件并允许管理员授权，然后应用会议兼容预设、开启输出，在会议软件选择 **Frameveil Camera (Windows Virtual Camera)**。日常运行无需管理员权限。

本版新增 Windows 11 Media Foundation 原生摄像头。2026-11-11，Windows 11 x64 build 26200 本机用户确认微信设备出现且画面正常、钉钉画面正常无报错。系统独立接收通过 640×480、720p、1080p 和黑屏检查；13 项自动检查通过。远端接收、长期性能和其他机型仍需验证。

Windows 10 x64 1809+ 保留 Unity/OBS DirectShow 路径，尚未完成 Windows 10 实机客户端回归。Windows 7/8、ARM64 原生成品和安卓摄像头输出尚不支持。安卓工程仅为研发原型。

EXE 未签名；首次注册摄像头需要管理员授权。程序本地处理素材，视频不输出声音。详细要求和边界包含在用户包中。

附件：

- `Frameveil-0.2.0-Windows-x64.zip`：用户版，含程序、完整运行库、指南、组件、对应应用源码和许可证。
- `Frameveil-0.2.0-source.zip`：应用源码及安卓移植准备工程，不含开发工具链。
- `SHA256.json`：校验清单。

原创应用源码 GPL-3.0-or-later，第三方组件遵循各自许可。
