
# SteamVR 壁纸暂停工具

当 SteamVR 运行时自动停止或暂停 Wallpaper Engine，SteamVR 关闭后自动恢复。常驻系统托盘，开机自启 — 安装一次即可忘记它的存在。

[English](README_EN.md)


<img width="512" height="512" alt="53EA5472A0EF239DD1011DE851DD1100" src="https://github.com/user-attachments/assets/d11caf12-852e-4740-8d8d-f9817c6e7c1c" />
## 功能

- **系统托盘图标** 带状态指示（绿色 = 监控中，橙色 = VR 运行中）
- **可配置动作**：SteamVR 启动时"停止"（`-control stop`）或"暂停"（`-control pause`）
- **开机自启**，最小化到系统托盘
- **自动检测** SteamVR 运行状态（进程监控）
- **手动控制**：托盘菜单可随时停止/恢复壁纸引擎
- **设置窗口**：配置轮询间隔、壁纸引擎路径、动作模式、开机自启
- **Windows 安装程序**：开始菜单快捷方式、卸载程序
- **气泡通知**：壁纸停止/恢复时弹出提示

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

## 配置

配置文件位于 `%APPDATA%\SteamVRWallpaperPause\config.json`：

```json
{
  "polling_interval": 5,
  "wallpaper_engine_path": "auto",
  "auto_start": true,
  "verbose": false,
  "action_on_vr_start": "stop"
}
```

- **polling_interval**：检查 SteamVR 进程的间隔秒数（默认：5）
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
