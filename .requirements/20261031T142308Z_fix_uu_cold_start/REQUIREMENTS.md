# As Is

用户确认异常发生时 UU 原本未打开。日志先出现 TIMEOUT，30 秒后出现 API_ERROR (game_id is required)。相同游戏及区服参数在 UU 就绪后实测可正常启动和停止。当前通过有 10 秒捕获输出超时的 CLI 启动客户端；doctor ready 后立即清除启动宽限期，加速仅等待六轮。

# To Be

打开客户端与调用加速接口分别处理。冷启动短暂未就绪时继续显示连接中，在有限时间内恢复；保留现有加速区服、自动化触发和退出清理规则。

# Requirements

1. 使用 Windows 原生启动方式打开安装的 UU 启动器，不捕获长期运行客户端的输出。
2. 冷启动后保留 45 秒就绪宽限期，限时重试已观察到的暂时接口失败；不隐藏 UU_BUSY 等需用户处理的错误。
   游戏启动时实测 doctor 本身也会偶发超时，就绪宽限期从首次触发开始覆盖 doctor，实际打开客户端后仍保留独立的启动等待时间。
3. 加速确认按实际经过的时间等待 45 秒，不以六次轮询为限；仅成功确认后标记为本工具开启。
4. 日志包含失败操作，升级保留配置和自启设置。

# Acceptance Criteria

1. 启动测试确认调用 ShellExecute 路径且不调用 CLI start；启动失败转成可展示错误。
2. not_running → 服务未就绪 → game_id is required → ready 测试最终成功；仅打开一次客户端；持续错误超时后显示错误；退出取消继续启动。
3. 18 秒后仍等待，45 秒后报告超时；已有加速不接管，退出仅停止本工具发起的目标加速。
   实机再次观察到 doctor ready 后 start_boost 偶发超时。此类命令结果不确定，需保留待确认请求，查询状态而不重复发起；退出时仍清理该待确认请求。明确失败的请求不保留待确认状态。
4. 错误日志能区分 doctor/status/start_app/start_boost/stop_boost；本机替换前后 config.json 哈希和自启值一致。

# Testing Plan

先加入可控时钟的冷启动、取消和超时回归测试，观察失败，再实现。运行 UU 测试及完整 unittest；检查 Python 3.10 语法兼容，打包后检查入口并替换本机版本。就绪客户端的真实加速/停止已验证；没有完成真实关闭客户端后的复测前，不声称端到端冷启动验证完成。

# Implementation Plan

1. 原生启动器发现和启动，测试带空格路径及 OSError。
2. 宽限期重试及按时间确认加速，运行状态机测试。
3. 操作日志、版本补丁更新，完整测试、打包和保留配置升级。

API 参考：https://docs.python.org/3/library/os.html#os.startfile （启动后返回，不等待应用退出）；https://docs.python.org/3/library/subprocess.html#subprocess.run （捕获输出创建管道，timeout 传入 communicate）。Serena、Lad 工具在当前会话不可用。

# Verification

- 新增测试先失败后通过；完整 unittest 共 60 项通过，18 个文件通过 Python 3.10 语法检查。
- v1.2.2 打包入口检查成功，已替换本机安装并启动设置窗口；配置 SHA256 和注册表自启值均保持不变。
- 实测 start_boost 和 doctor 均存在偶发超时，分别覆盖待确认命令与初次触发就绪宽限期。
- 用户已启动 VRC 后跳过额外启停测试。升级后只读查询得到 VRChat boosting、ping 54ms；未声称完成关闭 UU 后的端到端冷启动验证。
- 旧安装、配置及应用卸载键备份于 `%LOCALAPPDATA%/SteamVRWallpaperPause/backups/20261031T142308Z-1.2.1`。
