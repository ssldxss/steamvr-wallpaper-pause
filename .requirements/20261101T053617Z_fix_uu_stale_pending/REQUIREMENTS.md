# As Is

用户在启动 SteamVR/VRC 时观察到连接检查成功但自动化报错。2026-11-01 日志复现：13:35:03 start_boost TIMEOUT；13:35:08 游戏退出，stop_boost 返回 API_ERROR (game is not being boosted)；13:35:23 再次启动；13:35:53 旧 pending 请求触发 START_TIMEOUT。旧请求既未在确认未加速时释放，也未在等待超时后重新发起，导致一直无法恢复。

# To Be

查询已无目标加速即完成退出清理；清理过程中目标消失也视为成功。重新启动游戏使用新请求。加速超时后先查询真实状态，目标确实不存在时允许退避后重试，保留用户已有加速；连接检查明确只验证读取接口。

# Requirements

1. 清理前查询目标加速。目标不存在或明确 not_boosting 时释放本工具状态，不调用 stop，也不报错。
2. 查询和停止之间目标消失，只有在再次查询确认已停止后才忽略明确的“game is not being boosted”错误；其他错误保留。
3. pending 超时后，如目标不存在，清除旧请求并遵循 30 秒退避重新尝试；如仍 starting，保留状态且不重复 start；已有 boosting 始终先按真实状态处理。
4. SteamVR 退出、重开后不继承已确认无效的 pending 请求；真实操作结果与 UI 连接提示清楚区分。
5. 本机升级保留配置、自启值，备份旧版本并重启本工具。

# Acceptance Criteria

1. 模拟请求超时 → 退出 → 查询空列表：状态 waiting，stop 未调用。
2. 模拟 stop 返回明确已停止错误 → 再次查询为空：状态 waiting；再次查询仍 boosting 或其他 API 错误时保持 error。
3. 45 秒超时后目标不存在，30 秒后第二次 start 能发出并确认；starting 不重复发送；其他游戏不被停止。
4. 日志事件序列重放后第二次启动发送新请求；连接成功仅描述接口可用，不覆盖真实自动化错误。
5. 完整测试通过、打包入口检查通过、安装前后配置和自启值一致。

# Testing Plan

先写日志序列、空状态清理、停止竞态和超时恢复回归测试，确认旧实现失败。完成最小修改后运行 UU 测试与完整 unittest。真实 CLI 启停验证需先确认没有既有加速及游戏进程；暂停本工具防止旧 worker 干扰，结束后恢复。不得关闭或操作其他应用窗口。

# Implementation Plan

1. 增加退出清理的状态验证及竞态测试，修正空目标/已停止处理。
2. 增加超时退避后恢复和日志序列测试，释放已证实无效的 pending。
3. 继续调查首次 start 请求超时，依据实测证据修改传输，不做无依据的超时扩容。
4. 调整连接文案、补丁版本；完整测试、构建、保留配置升级并记录验证边界。

继续使用已读取的 tdd 技能；当前没有 Serena、Lad 工具。官方 UU skill/reference 取自已安装客户端附带的归档。Python API 参考：https://docs.python.org/3/library/subprocess.html 。

# Verification

- 新增回归测试先失败后通过；完整 unittest 65 项通过。18 个 Python 文件通过 Python 3.10 语法检查，git diff --check 无空白错误。
- 真实 CLI 两轮启停中，首轮状态查询历时 18.366 秒并返回 SERVICE_UNAVAILABLE，第二轮正常确认 boosting / 53ms；说明 UU 服务有暂时不可用现象，未认定为配置或授权错误。
- 使用真实 UUWorker、真实 CLI 与当前区服，注入一次“首次 start 请求 TIMEOUT”并模拟触发进程退出：worker 返回 waiting，没有 stop API 错误。再次模拟触发 VRC 启动后，真实加速成功（51ms）；过程中真实 status 再次超时，worker 在宽限期内恢复。最后模拟退出，真实 stop 成功并确认状态空列表。触发进程快照是测试输入，未启动/关闭 SteamVR/VRC/UU 窗口。
- v1.2.3 打包入口检查通过；本机已升级并重新打开设置，配置 SHA256、自启注册表值均一致。旧安装和配置备份：`%LOCALAPPDATA%/SteamVRWallpaperPause/backups/20261101T053617Z-1.2.2`。
- 本次修复恢复逻辑与错误状态清理，没有改变 CLI HTTP 协议，也未扩大命令超时；UU 完全退出后的冷启动链路没有在本次实机操作中验证。
