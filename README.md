# 帧幕 Frameveil 0.2.0

Windows x64 本地素材虚拟摄像头。支持静态图片、多图轮播和视频输入，带完整中文 GUI。

普通用户请从项目的 **Releases** 下载 `Frameveil-0.2.0-Windows-x64.zip`，完整解压后先阅读“开始使用.html”。开发源码和运行成品分别提供。

2026-11-11 用户实测：Windows 11 本机使用 **Frameveil Camera (Windows Virtual Camera)**，微信能识别并正常显示，钉钉正常显示且无报错。适配范围、版本与待测项目见 `COMPATIBILITY.md`、`VALIDATION.md`。

## 直接运行

打开 `dist\Frameveil\Frameveil.exe`。整个 `Frameveil` 文件夹需要保持完整，不能单独搬走 exe。已内置 Python、Qt、OpenCV 与 pyvirtualcam，使用者无需配置开发环境。

首次打开显示演示素材；导入自己的文件后可直接预览。摄像头输出默认关闭，每次启动都需手动开启。

首次使用输出时：

1. Windows 11：右侧「摄像头组件管理」安装 / 修复 **Windows 原生组件**，首次允许管理员授权。Windows 10 则安装 **Unity Capture**。运行不需要 Python、编译器或完整 OBS。
2. 向下滚动右侧参数区，点击「应用会议兼容预设」。Windows 11 选用原生 720p/30 FPS；Windows 10 选用 Unity 640×480/30 FPS。
3. 点击「开启虚拟摄像头」。原生设备只在输出开启期间出现，因此应先开启帧幕，再打开会议客户端的设备列表；必要时重新启动客户端以刷新列表。
4. Windows 11 在客户端选择 **Frameveil Camera (Windows Virtual Camera)**；Unity 后端选择 **Unity Video Capture**；OBS 后端选择 **OBS Virtual Camera**。必须选择帧幕当前提示的同一个设备。不要同时在 OBS 中启动同一个虚拟摄像头输出。
5. 原生后端可点击「接收自检」，由独立进程读取测试帧。自检通过仍需在实际客户端及远端确认。

预览不需要安装组件或管理员权限。组件只在用户完成管理员授权后注册。Unity 组件放在 `%ProgramData%\Frameveil\Camera`，原生组件放在 `%ProgramData%\Frameveil\Native\<内容哈希>`，避免移动便携软件后注册路径失效，并避免升级覆盖服务仍加载的文件。组件管理可卸载帧幕安装的设备，保留可能仍被进程加载的 DLL 文件。原生传输缓冲在 `%ProgramData%\Frameveil\Transport`，停止输出后清空画面；异常退出后的旧帧最多保留约 2 秒即显示黑屏。

## 已实现

- 导入或拖入多张 PNG/JPG/JPEG/BMP/WebP/TIFF 图片及 MP4/MOV/MKV/AVI/WMV/M4V/WebM 视频；实际视频格式取决于解码支持，推荐 H.264 MP4。
- 素材缩略图、上移/下移、移除、上一项/下一项、进度定位。
- 0.5–3600 秒图片轮播间隔；顺序/随机播放；列表循环开关；0/0.3/0.6/1 秒淡入淡出。
- 0.5–2 倍视频速度；暂停冻结画面；一键持续黑屏；一键开关虚拟摄像头。
- 720p、1080p、640×480；DirectShow 提供 15/24/25/30/60 FPS；Windows 原生摄像头协商 30 FPS。完整显示/居中裁剪/拉伸；镜像；自定义留边颜色。
- Windows 11 Media Foundation 原生摄像头，NV12/RGB32 格式，多分辨率协商；Windows 10/11 保留 Unity / OBS DirectShow 后端。
- 摄像头设备检测、本地日志、自动保存参数和素材路径。没有遥测或网络请求；素材不会上传。

## 建议的一轮验收（约 10 分钟）

1. **启动**：双击 exe，看到三张演示素材和活动进度条。改成 2 秒/张，观察依次切换；关闭循环，在最后一项停住；打开随机，确认不连续重复同一项。
2. **导入**：导入两张带文字或明显颜色的测试图片和一段 5–10 秒 MP4。检查中文路径、缩略图、排序、删除；拖动进度条；尝试 1.5 倍速。
3. **画面**：用竖图测试完整显示/裁剪/拉伸；用文字测试镜像；换留边颜色。停止输出后可改分辨率；60 FPS 仅在 DirectShow 后端可用。
4. **输出**：安装组件或复用 OBS；开启摄像头，状态变成「正在发送画面」，诊断中发送帧数增加。这个状态只证明发送端工作，不证明会议接收端已经连接。
5. **会议端**：先在客户端设置/入会前预览选择对应设备，再用另一个自己的账号或测试设备查看接收画面。检查图片与视频都能显示、方向一致、轮播切换正常。会议软件可能自行镜像本地预览，以另一端画面为准。
6. **控制**：暂停应停在同一画面；黑屏待机应持续全黑；恢复后继续；停止并重新开启应能恢复输出。退出后检查会议端设备状态。停止后的末帧/离线提示由客户端和组件决定。
7. **持久化**：重新打开帧幕，参数与列表恢复，输出保持关闭。移动或删除一个素材后再打开，应提示读取失败，应用仍可操作并重新导入。

请记录：系统版本、钉钉/微信版本、所选摄像头名字、分辨率、是否能枚举、是否能打开、接收端是否正常，以及日志中的异常。优先使用专门的测试会议。

## 边界

- 不读取真实摄像头、麦克风；只向虚拟摄像头发送本地素材画面。视频音轨不输出。
- 不包含人脸生成、动作生成、客户端注入或绕过检测。静态照片不会自然运动。
- 不承诺钉钉或微信所有版本支持虚拟摄像头。有些客户端没有选择入口或会过滤虚拟设备；需要本机测试确认。
- GIF/APNG/WebP 动画暂不作为动画播放，导入时拒绝多帧图片；请转为 MP4。
- 快捷键仅在应用内有效，不是系统全局快捷键。关闭帧幕不会主动选择真实摄像头；会议软件自己的自动回退行为需确认。
- 大量文件导入、超高分辨率图片、视频初次打开可能短暂等待；每次导入最多处理 200 个文件。
- 初版未购买代码签名证书；EXE 不是签名发行版。

## 日志与数据

`%LOCALAPPDATA%\Frameveil\settings.json`：偏好及素材路径，不复制素材本身。路径失效后需重新导入。

`%LOCALAPPDATA%\Frameveil\frameveil.log`：轮换日志。可在右侧「诊断 / 日志」中打开文件夹。

## 源码开发

Python 3.11 x64。本机开发环境的依赖已写入 `requirements.txt`：

```powershell
python -m pip install -r requirements.txt
python tools/prepare_assets.py
python tools/build_native.py
python main.py
python -m unittest discover -s tests -v
.\build.ps1
```

`prepare_assets.py` 仅用于开发构建：生成原创图标和测试素材，从官方固定提交下载 Unity Capture，记录 SHA-256。普通使用不运行此脚本、不联网下载依赖。

原生组件构建需要 MSVC 2022 x64 工具集、Windows SDK 10.0.26100、WIL 头文件。`build_native.py` 支持 `FRAMEVEIL_TOOLCHAIN` 指向便携工具链，或项目内 `.build-tools/msvc`。成品包含编译后的组件，不要求使用者安装这些开发工具。

## 调研与架构

调研：2026-11-10。

- https://github.com/letmaik/pyvirtualcam — 帧发送 API，Windows 支持 OBS / Unity Capture；本项目采用该库，不包含现有 GUI 的复制代码。
- https://github.com/schellingb/UnityCapture — DirectShow 摄像头组件；固定提交 `3ed54c325e0ad71afcf4f246c07e5e17b3d7f2d2`，MIT filter，内置原始 DLL 和授权。
- https://github.com/obsproject/obs-studio — 成熟的完整制作/虚拟摄像头方案，本版可复用已安装的 OBS 摄像头。
- https://github.com/Mahdi-hasan-shuvo/virtualcam-studio — 已有类似图片/视频列表 GUI，参考功能范围，界面和播放引擎为本项目独立编写。
- https://github.com/jozeta/camtest — 原生 DirectShow 静态图/GIF/幻灯片方案，可作为后续自有设备开发参考。

架构：PySide6 GUI → 命令队列 → 独立媒体线程（OpenCV/Pillow 合成 RGB）→ pyvirtualcam → 系统虚拟摄像头 → 会议客户端。

0.2 将输出抽为适配层：DirectShow 使用 pyvirtualcam；Windows 原生路径使用 CPU 帧缓冲、独立会话宿主与 Media Foundation 媒体源。原生媒体源基于 StillCam / VCamSample 的 MIT 授权代码修改，许可见 `native/third_party`。

GUI 从有界最新帧邮箱取预览，避免积压；设备和解码器仅由媒体线程持有，退出时释放。输出格式在发送期间锁定，其他播放参数可以实时更改。

原创应用源码使用 GPL-3.0-or-later，第三方组件各自遵循原授权，见 `THIRD_PARTY.md`、`LICENSE` 和 `licenses`。

本机实测结果与尚未验证的部分见 `VALIDATION.md`。

通用系统、硬件要求、平台状态和安卓后续边界见 `COMPATIBILITY.md`，不将单机成功视为所有设备兼容。
