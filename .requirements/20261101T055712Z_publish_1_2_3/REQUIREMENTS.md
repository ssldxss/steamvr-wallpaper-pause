# As Is

本地 master 比 origin/master 领先一个已授权提交，另有 UU 自动加速、设置界面及恢复逻辑等尚未提交的工作。GitHub 最新 Release 为 1.1.3。运行版本为 1.2.3，本机配置已改成 1 秒，但源码和安装器的新安装默认值仍为 5 秒。没有自动发布工作流，本机没有 Inno Setup 编译器。

# To Be

将当前已完成工作提交推送到现有 master；构建并发布 1.2.3 安装程序与独立程序，附发布说明和校验值。新安装默认检测 SteamVR/VRC 的间隔为 1 秒，升级保留原有配置。README 下载入口指向最新 Release。

# Requirements

1. 提交当前授权范围内的源代码、测试和设计/需求文档，不提交本机配置、日志、构建缓存或编译器。
2. 默认间隔、命令行帮助、设置提示和安装配置均为 1 秒，UU 状态轮询不改变；已有配置保持原值。
3. 使用当前源代码重新构建独立 exe 和 Inno Setup 安装包，优先使用构建环境已有编译器。
4. 通过测试和打包验证后，推送 master 及 1.2.3 标签；GitHub Release 对应相同提交，附件内容与本地产物哈希一致。

# Acceptance Criteria

1. 提交文件清单中没有构建产物及本机敏感配置，完成后 Git 工作区干净。
2. 临时配置目录首次启动为 1 秒，旧配置兼容测试仍通过；用户的真实配置不改写。
3. unittest、Python 3.10 语法与打包入口检查通过；安装器编译成功，验证包内程序与构建 exe 一致。
4. GitHub master 和版本标签均指向发布提交；Release 可读取，安装器/独立 exe/校验文件上传完整且可校验。

# Testing Plan

复用现有测试，配置常量和文案不添加镜像实现的测试；在隔离配置目录手工验证默认值与文件保留。构建后检查冻结入口，验证安装器内容和发布资产摘要。发布前检查全部差异和文件清单。

# Implementation Plan

1. 同步默认值与文档下载入口，运行已有测试与隔离默认配置检查。
2. 本机编译器安装被自动审批拦截，改用 GitHub Windows 2022 构建环境预装的 Inno Setup 6（官方 runner 软件清单已验证），不在本机安装工具。新增手动构建工作流、独立入口和隔离安装验证；下载远程产物进行发布。
3. 准备发布说明，提交推送及打标签，再上传并发布 GitHub Release。

工具限制：GitHub 连接工具不提供 Release 资产上传，使用本机已登录的 gh CLI。Serena/Lad 当前不可用。官方文档：https://jrsoftware.org/isdl.php 、https://jrsoftware.org/ishelp/topic_setupcmdline.htm 。

构建环境参考：https://github.com/actions/runner-images/blob/main/images/windows/Windows2022-Readme.md 。工作流只有读取仓库权限，不会自动发布；验证成功后由当前任务上传 Release 资产。
