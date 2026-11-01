"""Internationalization support — Chinese (default) and English."""

from typing import Literal

Lang = Literal["zh", "en"]

TEXTS: dict[str, dict[Lang, str]] = {
    # Tray menu — dual status lines
    "vr_running": {"zh": "SteamVR: 运行中", "en": "SteamVR: Running"},
    "vr_not_running": {"zh": "SteamVR: 未运行", "en": "SteamVR: Not Running"},
    "wp_running": {"zh": "壁纸引擎: 运行中", "en": "Wallpaper: Running"},
    "wp_paused": {"zh": "壁纸引擎: 已暂停", "en": "Wallpaper: Paused"},
    "wp_stopped": {"zh": "壁纸引擎: 已停止(释放内存)", "en": "Wallpaper: Stopped (Frees Memory)"},
    "wp_not_running": {"zh": "壁纸引擎: 未运行", "en": "Wallpaper: Not Running"},
    "settings": {"zh": "设置", "en": "Settings"},
    "exit": {"zh": "退出", "en": "Exit"},
    "autorestart": {"zh": "SteamVR 关闭后若壁纸引擎已退出则自动启动", "en": "Auto-restart wallpaper if stopped when SteamVR closes"},
    # Notifications
    "notify_pause": {"zh": "壁纸引擎已暂停 — SteamVR 正在运行", "en": "Wallpaper Engine paused — SteamVR is running"},
    "notify_stop": {"zh": "壁纸引擎已停止 — SteamVR 正在运行", "en": "Wallpaper Engine stopped — SteamVR is running"},
    "notify_resume": {"zh": "壁纸引擎已恢复 — SteamVR 已关闭", "en": "Wallpaper Engine resumed — SteamVR closed"},
    "notify_error": {"zh": "操作失败", "en": "Operation failed"},
    # Settings window
    "settings_title": {"zh": "SteamVR 壁纸暂停 — 设置", "en": "SteamVR Wallpaper Pause — Settings"},
    "polling_interval": {"zh": "轮询间隔（秒）：", "en": "Polling Interval (seconds):"},
    "wallpaper_path": {"zh": "壁纸引擎路径：", "en": "Wallpaper Engine Path:"},
    "path_hint": {"zh": "留空为自动检测", "en": "Leave empty for auto-detection"},
    "action_label": {"zh": "SteamVR 启动时：壁纸引擎", "en": "When SteamVR starts: Wallpaper Engine"},
    "action_pause": {"zh": "暂停", "en": "Pause"},
    "action_stop": {"zh": "停止", "en": "Stop"},
    "language_label": {"zh": "语言 / Language：", "en": "Language:"},
    "language_zh": {"zh": "中文", "en": "Chinese"},
    "language_en": {"zh": "English", "en": "English"},
    "language_hint": {"zh": "保存后，下次打开设置时生效。", "en": "Applies when settings are opened again."},
    "autostart": {"zh": "开机自启", "en": "Start with Windows"},
    "save": {"zh": "保存", "en": "Save"},
    "cancel": {"zh": "取消", "en": "Cancel"},
    "browse": {"zh": "浏览...", "en": "Browse..."},
    "version": {"zh": "版本：v1.2.3", "en": "Version: v1.2.3"},
    "about": {"zh": "关于", "en": "About"},
    "invalid_interval": {"zh": "轮询间隔必须为大于 0 的数字。", "en": "Polling interval must be a number greater than 0."},
    "invalid_title": {"zh": "无效输入", "en": "Invalid Value"},
    # Tray tooltip
    "tray_tooltip": {"zh": "SteamVR 壁纸暂停", "en": "SteamVR Wallpaper Pause"},
    # Log messages
    "log_starting": {"zh": "SteamVR 壁纸暂停 启动中", "en": "SteamVR Wallpaper Pause starting"},
    "log_vr_started": {"zh": "SteamVR 已启动 — 暂停壁纸引擎", "en": "SteamVR started — pausing Wallpaper Engine"},
    "log_vr_started_stop": {"zh": "SteamVR 已启动 — 停止壁纸引擎", "en": "SteamVR started — stopping Wallpaper Engine"},
    "log_vr_stopped": {"zh": "SteamVR 已关闭 — 恢复壁纸引擎", "en": "SteamVR stopped — resuming Wallpaper Engine"},
    "log_startup_check": {"zh": "启动检查：SteamVR 未运行，确保壁纸已恢复", "en": "Startup check: SteamVR not running, ensuring wallpaper resumed"},
    "log_no_path": {"zh": "未配置壁纸引擎路径", "en": "No wallpaper engine path configured"},
    "log_shutdown": {"zh": "正在关闭...", "en": "Shutting down..."},
    "log_shutdown_done": {"zh": "关闭完成", "en": "Shutdown complete"},
    "log_auto_start_enabled": {"zh": "开机自启已启用", "en": "Auto-start enabled"},
    "log_auto_start_disabled": {"zh": "开机自启已禁用", "en": "Auto-start disabled"},
}

TEXTS.update({
    "app_name": {"zh": "VR 助手", "en": "VR Companion"},
    "app_tagline": {"zh": "随 VR 自动就位。", "en": "Set it once.\nStay immersed."},
    "nav_automation": {"zh": "自动化", "en": "Automation"},
    "nav_connection": {"zh": "连接引导", "en": "Connect UU"},
    "nav_advanced": {"zh": "高级设置", "en": "Advanced"},
    "automation_intro": {"zh": "让壁纸和网络随游戏自动切换。", "en": "Let your wallpaper and connection follow your game."},
    "wallpaper_heading": {"zh": "壁纸引擎", "en": "Wallpaper Engine"},
    "wallpaper_intro": {"zh": "SteamVR 启动时处理壁纸，退出后恢复。", "en": "Control wallpapers during SteamVR and restore them afterward."},
    "wallpaper_mode": {"zh": "进入 VR 时", "en": "When VR starts"},
    "mode_stop": {"zh": "停止，释放壁纸内存", "en": "Stop and free wallpaper memory"},
    "mode_pause": {"zh": "暂停壁纸", "en": "Pause wallpapers"},
    "restart_short": {"zh": "退出 VR 后，重新打开已关闭的壁纸引擎", "en": "Reopen Wallpaper Engine after VR if it was closed"},
    "uu_heading": {"zh": "网易 UU", "en": "NetEase UU"},
    "uu_intro": {"zh": "游戏启动后自动加速 VRChat。", "en": "Automatically accelerate VRChat when your session starts."},
    "uu_enable": {"zh": "自动加速 VRChat", "en": "Automatically accelerate VRChat"},
    "uu_trigger": {"zh": "触发时机", "en": "Start when"},
    "uu_trigger_vrchat": {"zh": "VRChat 启动时", "en": "VRChat starts"},
    "uu_trigger_steamvr": {"zh": "SteamVR 启动时", "en": "SteamVR starts"},
    "uu_trigger_either": {"zh": "任一程序启动时", "en": "Either app starts"},
    "uu_region": {"zh": "加速区服", "en": "Region"},
    "uu_region_hint": {"zh": "请选择具体区服；已有加速会保留当前节点。", "en": "Choose a region. Existing acceleration keeps its node."},
    "uu_region_connect": {"zh": "连接 UU 后选择区服", "en": "Connect UU to choose a region"},
    "uu_region_loading": {"zh": "正在读取区服…", "en": "Loading regions…"},
    "uu_region_required": {"zh": "请先连接 UU，并选择具体加速区服。", "en": "Connect UU and select an acceleration region first."},
    "uu_region_unavailable": {"zh": "未读取到可用区服，请重新检查连接。", "en": "No regions were returned. Check the connection again."},
    "uu_auto_launch": {"zh": "UU 未运行时自动打开", "en": "Open UU automatically when needed"},
    "uu_stop_on_exit": {"zh": "游戏退出后停止本工具启动的加速", "en": "Stop acceleration started here when the session ends"},
    "uu_configure": {"zh": "设置连接", "en": "Set up connection"},
    "general_heading": {"zh": "后台运行", "en": "In the background"},
    "startup_hint": {"zh": "登录 Windows 后在系统托盘运行。", "en": "Run quietly in the system tray after signing into Windows."},
    "startup_error": {"zh": "无法更新开机启动，请检查当前账号权限后重试。", "en": "Could not update Windows startup. Check your account permissions and try again."},
    "save_settings": {"zh": "保存设置", "en": "Save settings"},
    "save_hint": {"zh": "保存后生效，关闭窗口后继续后台监控。", "en": "Changes apply on save. Monitoring continues after closing this window."},
    "connection_intro": {"zh": "完成一次授权，之后交给自动化。", "en": "Connect once, then let automation take over."},
    "connection_heading": {"zh": "连接状态", "en": "Connection status"},
    "connection_unchecked": {"zh": "尚未检查", "en": "Not checked yet"},
    "connection_hint": {"zh": "仅验证连接，不会启停加速；实际加速状态请查看“自动化”页面。", "en": "This checks the connection without starting or stopping acceleration. See Automation for live acceleration status."},
    "connection_ready": {"zh": "连接检查通过", "en": "Connection check passed"},
    "connection_checking": {"zh": "正在检查…", "en": "Checking…"},
    "connection_check": {"zh": "检查连接", "en": "Check connection"},
    "connection_recheck": {"zh": "重新检查", "en": "Check again"},
    "connection_enable": {"zh": "启用自动加速", "en": "Enable automation"},
    "guide_heading": {"zh": "首次连接", "en": "First-time setup"},
    "guide_step_1": {"zh": "打开网易 UU", "en": "Open NetEase UU"},
    "guide_detail_1": {"zh": "确认已安装客户端，并登录你的账号。", "en": "Install the desktop client and sign into your account."},
    "guide_step_2": {"zh": "在 UU 中开启授权", "en": "Enable authorization in UU"},
    "guide_detail_2": {"zh": "首页右上角菜单 → 设置 → AI 设置 → 开启授权。", "en": "Open the top-right menu > Settings > AI Settings, then enable authorization."},
    "guide_step_3": {"zh": "回到这里检查连接", "en": "Return here to check the connection"},
    "guide_detail_3": {"zh": "先关闭 UU 的设置窗口，再点击“检查连接”。", "en": "Close UU's settings window first, then choose Check connection."},
    "guide_manual": {"zh": "授权需要你在 UU 中手动开启。", "en": "Authorization must be enabled manually in UU."},
    "uu_open": {"zh": "打开 UU", "en": "Open UU"},
    "uu_download": {"zh": "下载网易 UU", "en": "Download NetEase UU"},
    "uu_opened": {"zh": "已请求打开 UU。完成授权后，请回到这里检查。", "en": "UU has been opened. Return here after completing authorization."},
    "advanced_intro": {"zh": "通常保持默认即可，遇到识别问题时再调整。", "en": "Defaults work for most setups. Adjust these if detection needs help."},
    "advanced_detection": {"zh": "检测与路径", "en": "Detection and paths"},
    "advanced_poll_hint": {"zh": "间隔越短，响应越快；默认 1 秒。", "en": "Shorter intervals respond sooner. Default: 1 second."},
    "uu_cli_path": {"zh": "UU 控制工具", "en": "UU control tool"},
    "uu_cli_hint": {"zh": "留空时从 UU 客户端或已安装的技能中自动查找。", "en": "Leave blank to find the tool in UU or an installed skill."},
    "language_heading": {"zh": "界面语言", "en": "Interface language"},
    "uu_status_disabled": {"zh": "未启用", "en": "Disabled"},
    "uu_status_pending_enable": {"zh": "保存后启用", "en": "Enabled after saving"},
    "uu_status_pending_disable": {"zh": "保存后停用", "en": "Disabled after saving"},
    "uu_status_waiting": {"zh": "等待游戏启动", "en": "Waiting for a session"},
    "uu_status_connecting": {"zh": "正在准备加速", "en": "Preparing acceleration"},
    "uu_status_boosting": {"zh": "加速中", "en": "Accelerating"},
    "uu_status_stopping": {"zh": "正在停止加速", "en": "Stopping acceleration"},
    "uu_status_error": {"zh": "需要检查 UU", "en": "Check UU"},
    "uu_error_CLI_MISSING": {"zh": "未找到控制工具。请更新 UU，或在高级设置中选择 uu-cli.exe。", "en": "Control tool not found. Update UU or select uu-cli.exe in Advanced."},
    "uu_error_UU_NOT_INSTALLED": {"zh": "请先安装网易 UU 并登录账号。", "en": "Install NetEase UU and sign into your account first."},
    "uu_error_UU_NOT_RUNNING": {"zh": "请打开 UU，或允许在需要时自动打开。", "en": "Open UU, or allow it to open automatically when needed."},
    "uu_error_SERVICE_UNAVAILABLE": {"zh": "请在 UU 的 AI 设置中开启授权，关闭设置窗口后重新检查。", "en": "Enable authorization in UU's AI Settings, close that window, and check again."},
    "uu_error_UU_BUSY": {"zh": "请关闭 UU 中的设置或其他弹窗，再重新检查。", "en": "Close settings or other dialogs in UU, then check again."},
    "uu_error_TIMEOUT": {"zh": "UU 响应超时，请稍后重新检查。", "en": "UU did not respond in time. Try checking again shortly."},
    "uu_error_START_TIMEOUT": {"zh": "暂未确认加速，稍后会自动重试。也可在 UU 中检查登录、会员和节点状态。", "en": "Acceleration is not confirmed yet; it will be checked again shortly. You can also check your account, membership and node in UU."},
    "uu_error_INVALID_RESPONSE": {"zh": "UU 返回了无法识别的数据，请更新客户端后重新检查。", "en": "UU returned an unexpected response. Update the client and check again."},
    "uu_error_generic": {"zh": "请确认 UU 已登录且网络正常，再重新检查。", "en": "Check that UU is signed in and online, then try again."},
})


def t(key: str, lang: Lang = "zh") -> str:
    """Get translated text for the given key.

    Args:
        key: Translation key.
        lang: Language code, "zh" or "en". Defaults to "zh".

    Returns:
        Translated string, or the key itself if not found.
    """
    entry = TEXTS.get(key, {})
    return entry.get(lang, key)


def uu_status_text(state, lang: Lang = "zh") -> str:
    text = t("uu_status_" + state.key, lang)
    if state.key == "boosting" and state.ping is not None:
        text += f" · {state.ping:.0f} ms"
    return text


def uu_error_text(code: str, lang: Lang = "zh") -> str:
    key = "uu_error_" + code
    return t(key if key in TEXTS else "uu_error_generic", lang)
