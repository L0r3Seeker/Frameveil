# GitHub Releases 发布准备

计划位置：账号 `L0r3Seeker`，公开仓库 `Frameveil`，版本标签 `v0.2.0`。截至准备阶段尚未创建该仓库或发布 Release，下面的地址仅在发布成功后有效。

用户下载页格式：`https://github.com/L0r3Seeker/Frameveil/releases/latest`

该版本文件直链格式：`https://github.com/L0r3Seeker/Frameveil/releases/download/v0.2.0/Frameveil-0.2.0-Windows-x64.zip`

## 使用准备好的发布脚本

在本机安装官方 [GitHub CLI](https://cli.github.com/)，执行 `gh auth login`，由账号持有者在浏览器完成登录。不要把密码或令牌发给助手。

在项目根目录运行 `powershell -ExecutionPolicy Bypass -File publishing/publish.ps1`。该脚本会校验附件，准备干净源码目录，创建公开仓库、推送代码并上传 Release。**运行此脚本会公开项目源码和安装包。** 它不会上传素材偏好、日志、私人文件、开发工具链或签名密钥。若同名仓库已存在则停止，避免修改已有项目。

脚本不要求在普通用户电脑安装 Git/CLI；这是发布者使用的流程。当前 GitHub 连接器只支持仓库内容等部分操作，没有创建仓库和上传 Release 二进制附件的接口，所以不能仅凭连接器登录状态完成发布。

## 网页方式

在 GitHub 建立公开 Frameveil 仓库并上传源码，随后创建 `v0.2.0` Release，将 `RELEASE-v0.2.0.md` 内容作为说明，上传 release 目录中的用户 ZIP、源码 ZIP、SHA256.json。确认下载页面实际可访问后再发朋友圈。

## 朋友圈入口

推荐在朋友圈发布一张软件截图及下载页链接文字。也可将已经生效的下载页生成二维码放在图片中，好友保存/识别后查看。当前交付包是 Windows 软件，手机上看到入口后仍需在 Windows 电脑下载和运行；微信内置浏览器是否直接下载，取决于客户端与链接处理，可复制到电脑或外部浏览器。

GitHub Releases 提供二进制附件下载，每个附件小于 2 GiB，当前约 110 MiB 用户包在此范围内。参考 [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)。访问表现依赖接收者网络，可另外保留网盘镜像，但不在未经验证时宣称人人都能在微信内一键下载。
