
# SteamVR 壁纸暂停工具

[English](README_EN.md)

一个给VRChat和其他steamvr玩家做的小工具

当 SteamVR 运行时自动停止或暂停 Wallpaper Engine，SteamVR 关闭后自动恢复。常驻系统托盘，开机自启 — 安装一次即可忘记它的存在。

## 快速开始

[安装程序](https://github.com/ssldxss/steamvr-wallpaper-pause/releases/latest/download/SteamVRWallpaperPause-Setup.exe)

[安装程序(蓝凑云)](https://zako.lanzoul.com/iZIL74e9746f)

密码:

```  
aey9
```

## ZakoZako!

<img width="300" height="300" alt="53EA5472A0EF239DD1011DE851DD1100" src="https://github.com/user-attachments/assets/d11caf12-852e-4740-8d8d-f9817c6e7c1c" />
<img width="300" height="300" alt="image" src="https://github.com/user-attachments/assets/97d9fca7-7643-4b45-981a-6ff4694b8f85" />


## 功能

- **系统托盘图标** 带状态指示（绿色 = 监控中，橙色 = VR 运行中）
- **可配置动作**：SteamVR 启动时"停止"（`-control stop`）或"暂停"（`-control pause`）
- **开机自启**，最小化到系统托盘
- **自动检测** SteamVR 运行状态（进程监控）
- **手动控制**：托盘菜单可随时停止/恢复壁纸引擎
- **设置窗口**：配置轮询间隔、壁纸引擎路径、动作模式、开机自启
- **UU 自动加速（可选）**：VRChat、SteamVR 或任一程序启动时自动打开 UU 并加速 VRChat；可选择区服和退出后停止
- **连接引导**：逐步说明 UU 授权入口，支持只读检查连接；路径与轮询间隔放在高级设置中
- **Windows 安装程序**：开始菜单快捷方式、卸载程序
- **气泡通知**：壁纸停止/恢复时弹出提示

## 设置 UU 自动加速

1. 在托盘菜单打开“设置”，进入“连接引导”。
2. 安装并登录网易 UU，打开首页右上角菜单 → 设置 → AI 设置，手动开启授权。
3. 关闭 UU 的设置窗口，回到本工具点击“检查连接”。
4. 点击“启用自动加速”，选择触发时机和具体区服（如“智能匹配”“日本”），并保存设置。

开启 UU 选项时会自动读取实际区服；未加载成功时显示连接提示，区服列表不提供
“沿用 UU 设置”或空白选项。连接检查失败不会清空此前已选的具体区服。

此功能默认关闭。UU 未运行时可自动打开；已有的加速会沿用当前节点。
“游戏退出后停止”只作用于本工具启动的加速，不会停止用户原有的加速。
SteamVR 是触发条件，加速目标始终是 VRChat。默认关闭的“游戏退出后停止”
意味着加速将继续运行；选择“任一程序启动时”时，需要两个程序都退出才会结束会话。

控制工具会优先从本机已安装的技能或 UU 自带技能包中查找，无需安装 Codex。
若自动查找失败，可以在“高级设置”中选择 `uu-cli.exe`。UU 授权必须由用户
在官方客户端内开启，本工具不会自动修改该权限。

开发时可安全预览设置界面（不修改真实配置或开机启动）：

```bash
python scripts/preview_settings.py
python scripts/preview_settings.py --language en --enabled --size 780x560
```

## 开发环境要求

- Python 3.10+
- 依赖：`pystray`、`Pillow`、`psutil`（见 `requirements.txt`）
- PyInstaller（打包 exe）
- Inno Setup 6（构建安装程序）

## 快速开始（开发）

```bash
# 安装依赖
pip install -r requirements.txt

# 控制台模式运行（调试用）
python src/main.py --console --verbose

# 正常模式运行（仅托盘）
python src/main.py
```

## 构建安装程序

```bash
# 1. 使用 PyInstaller 编译独立 exe
build.bat

# 2. 用 Inno Setup Compiler 打开 installer/setup.iss 并编译
#    输出：installer/Output/SteamVRWallpaperPause-Setup.exe
```

也可以在 GitHub Actions 中手动运行 **Build Windows release**，选择要构建的分支或标签。
流程会运行测试、构建独立程序和安装包、验证首次安装及升级配置保留，并提供下载产物和 SHA256 校验文件。

## 配置

配置文件位于 `%APPDATA%\SteamVRWallpaperPause\config.json`：

```json
{
  "polling_interval": 1,
  "wallpaper_engine_path": "auto",
  "auto_start": true,
  "verbose": false,
  "action_on_vr_start": "stop"
}
```

- **polling_interval**：检查 SteamVR / VRChat 进程的间隔秒数（默认：1）；升级保留已有配置。
- **wallpaper_engine_path**：`wallpaper32.exe` 路径，设为 `"auto"` 自动检测（默认："auto"）
- **auto_start**：是否开机自启（默认：true）
- **verbose**：启用详细日志（默认：false）
- **action_on_vr_start**：`"stop"` 或 `"pause"` — SteamVR 启动时的动作（默认："stop"）

## 工作原理

1. 每隔 N 秒检查 `vrserver.exe`（SteamVR）是否在运行
2. SteamVR 启动 → 通过 `wallpaper32.exe -control stop/pause` 停止或暂停壁纸
3. SteamVR 退出 → 通过 `wallpaper32.exe -control play` 恢复壁纸
4. 仅在状态变化时执行操作，运行期间不重复发送命令

## 许可证

MIT
