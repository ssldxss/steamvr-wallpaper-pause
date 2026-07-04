"""Internationalization support — Chinese (default) and English."""

from typing import Literal

Lang = Literal["zh", "en"]

TEXTS: dict[str, dict[Lang, str]] = {
    # Tray menu
    "status_monitoring": {"zh": "状态：监控中", "en": "Status: Monitoring"},
    "status_vr_active": {"zh": "状态：VR 运行中 — 壁纸已暂停", "en": "Status: VR Active — Wallpaper Paused"},
    "status_vr_stopped": {"zh": "状态：VR 运行中 — 壁纸已停止", "en": "Status: VR Active — Wallpaper Stopped"},
    "settings": {"zh": "设置", "en": "Settings"},
    "exit": {"zh": "退出", "en": "Exit"},
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
    "language_hint": {"zh": "重启程序后生效", "en": "Takes effect after restart"},
    "autostart": {"zh": "开机自启", "en": "Start with Windows"},
    "save": {"zh": "保存", "en": "Save"},
    "cancel": {"zh": "取消", "en": "Cancel"},
    "browse": {"zh": "浏览...", "en": "Browse..."},
    "version": {"zh": "版本：v1.1.0", "en": "Version: v1.1.0"},
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
