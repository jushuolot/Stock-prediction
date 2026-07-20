# Stock Assistant 产品进化路线图

目标：**简单、便捷、快速**完成个股与市场分析；每次迭代可独立使用，并同步 GitHub。

## 当前版本定位

| 阶段 | 主题 | 状态 | 交付物 |
|------|------|------|--------|
| **P1** | 结构 + 可读资料 | ✅ 已完成 | 工作台导航、可读简报导出、Tab 命名 |
| **P2** | 页面模块化 | ✅ 已完成 | `src/ui/pages/*` 拆分 app.py |
| **P3** | 一键分析链路 | ✅ 已完成 | 选标的 → 自动拉行情/评分/简报/路线 |
| **P4** | 协作与公网 | ✅ 已完成 | Streamlit Cloud 稳定部署、分享链接模板 |
| **P5** | 智能持久化 | ✅ 已完成 | 摘要/简报落盘、今日速览、健康检测、新手引导 |
| **P6** | 体验极限 | ✅ 已完成 | 移动端、定时刷新、多简报合并 HTML/PDF |
| **P7** | 智能增强 | ✅ 已完成 | 板块联动、语音朗读、只读 JSON 快照 |
| **P8** | 生态扩展 | ✅ 已完成 | Webhook/邮件推送、多用户隔离、cron 脚本 |
| **P9** | 运维观测 | ✅ 已完成 | 推送日志、重试队列、健康告警 Webhook |
| **P10** | 导出增强 | ✅ 已完成 | CSV、筛选排序、备份脚本 |
| **P11** | 文档与版本 | ✅ 已完成 | 页脚版本、进化日志、snapshot v2 |
| **P12** | 百步进化 | ✅ 已完成 | [120 步清单](docs/EVOLUTION_100.md)、v1.8.0 |
| **P13** | 智能提醒 | ✅ 已完成 | 涨跌幅/评分阈值、提醒 Markdown |
| **P14** | 运维脚本 | ✅ 已完成 | evolve_verify、health_check_cron、历史 CSV |
| **P15** | 体验抛光 | ✅ 已完成 | 评分徽章、深链接 tab、v1.9.0 step 150 |
| **P16** | 双股对比 | ✅ 已完成 | 并排涨跌幅/评分/摘要、对比 Markdown |
| **P17** | 提醒推送 | ✅ 已完成 | 提醒 Webhook、自动推送、alert_push |
| **P18** | 体验与 v2 | ✅ 已完成 | ?tab= 自动切换、v2.0.0 step 180 |
| **P19** | 自选分组 | ✅ 已完成 | watch_groups 偏好、分组筛选与管理 |
| **P20** | 历史趋势 | ✅ 已完成 | trend_summary、工作台/历史页 📈 趋势 |
| **P21** | 备份导入 | ✅ 已完成 | JSON 备份下载/合并导入、v2.1.0 step 210 |
| **P22** | 快捷筛选 | ✅ 已完成 | 搜索页快捷筛选、代码列表复制 |
| **P23** | 定时摘要 | ✅ 已完成 | cron 摘要含提醒、`--alerts-only` |
| **P24** | 体验抛光 | ✅ 已完成 | 深色偏好持久化、v2.2.0 step 240 |
| **P25** | 板块热力图 | ✅ 已完成 | sector_heatmap、工作台 🗺 板块分布 |
| **P26** | 批量操作 | ✅ 已完成 | 多选删除、批量加入分组 |
| **P27** | 文档与 v2.3 | ✅ 已完成 | EVOLUTION 241–270、v2.3.0 step 270 |
| **P28** | 笔记/标注 | ✅ 已完成 | user_prefs.watch_notes、工作台笔记 expander |
| **P29** | 性能/缓存 | ✅ 已完成 | 摘要刷新 60s in-session 缓存 |
| **P30** | 文档与 v2.4 | ✅ 已完成 | EVOLUTION 271–300、v2.4.0 step 300 |
| **P31** | 笔记导出 | ✅ 已完成 | 速览/CSV/JSON 备份含 watch_notes |
| **P32** | 健康面板 | ✅ 已完成 | 缓存统计、上次刷新、推送日志尾部 |
| **P33** | 文档与 v2.5 | ✅ 已完成 | EVOLUTION 301–330、v2.5.0 step 330 |
| **P34** | 搜索历史 | ✅ 已完成 | user_prefs.search_history、搜索页 chips 重搜 |
| **P35** | 提醒模板 | ✅ 已完成 | 保守/均衡/激进 阈值一键套用 |
| **P36** | 文档与 v2.6 | ✅ 已完成 | EVOLUTION 331–360、v2.6.0 step 360 |
| **P37** | 工作台仪表盘 | ✅ 已完成 | dashboard_stats、均分/涨跌/提醒概览 |
| **P38** | 只读分享 | ✅ 已完成 | ?readonly=1 隐藏编辑控件 |
| **P39** | 文档与 v2.7 | ✅ 已完成 | EVOLUTION 361–390、v2.7.0 step 390 |
| **P40** | 多语言文案 | ✅ 已完成 | user_prefs.locale、Tab/仪表盘 i18n lite |
| **P41** | 快捷键提示 | ✅ 已完成 | 页脚 ?tab= / ?readonly=1 链接提示 |
| **P42** | 文档与 v2.8 | ✅ 已完成 | EVOLUTION 391–420、v2.8.0 step 420 |
| **P43** | 自选排序 | ✅ 已完成 | user_prefs.watch_sort、工作台排序持久化 |
| **P44** | 分析周报 | ✅ 已完成 | weekly_report、历史页下载 .md |
| **P45** | 文档与 v2.9 | ✅ 已完成 | EVOLUTION 421–450、v2.9.0 step 450 |
| **P46** | 价格目标提醒 | ✅ 已完成 | user_prefs.price_targets、watch_alerts 现价对比 |
| **P47** | 数据新鲜度 | ✅ 已完成 | stale_hours、freshness_badge、工作台 stale 列 |
| **P48** | 文档与 v3.0 | ✅ 已完成 | EVOLUTION 451–480、v3.0.0 step 480 |
| **P49** | 组合权重视图 | ✅ 已完成 | user_prefs.watch_weights、工作台 ⚖ 饼图 |
| **P50** | cron 周报 | ✅ 已完成 | weekly_report_cron.py、STOCK_USER |
| **P51** | 文档与 v3.1 | ✅ 已完成 | EVOLUTION 481–510、v3.1.0 step 510 |
| **P52** | 相似股推荐 | ✅ 已完成 | similar_pick、工作台 🔗 同板块推荐 |
| **P53** | 会话恢复提示 | ✅ 已完成 | welcome_banner、启动欢迎条 |
| **P54** | 文档与 v3.2 | ✅ 已完成 | EVOLUTION 511–540、v3.2.0 step 540 |
| **P55** | 分析结果置顶 | ✅ 已完成 | user_prefs.pinned_tickers、工作台置顶 |
| **P56** | 错误重试 UI | ✅ 已完成 | retry_fetch_ui、失败行 🔄 重试 |
| **P57** | 文档与 v3.3 | ✅ 已完成 | EVOLUTION 541–570、v3.3.0 step 570 |
| **P58** | 快捷加自选 | ✅ 已完成 | watchlist_add、搜索页逐行加入自选 |
| **P59** | 邮件主题 | ✅ 已完成 | digest_push 日期+提醒数主题行 |
| **P60** | 文档与 v3.4 | ✅ 已完成 | EVOLUTION 571–600、v3.4.0 step 600 |
| **P61** | 600步庆祝 | ✅ 已完成 | milestone_banner、confetti 横幅 |
| **P62** | 失败汇总 | ✅ 已完成 | fetch_failures_summary、刷新后折叠列表 |
| **P63** | 文档与 v3.5 | ✅ 已完成 | EVOLUTION 601–630、v3.5.0 step 630 |
| **P64** | 自选 CSV 导入 | ✅ 已完成 | watchlist_csv_import、工作台 CSV 合并 |
| **P65** | 提醒静默时段 | ✅ 已完成 | quiet_hours、自动 Webhook 静默跳过 |
| **P66** | 文档与 v3.6 | ✅ 已完成 | EVOLUTION 631–660、v3.6.0 step 660 |
| **P67** | 自选 CSV 导出 | ✅ 已完成 | watchlist_csv_export、工作台导出 |
| **P68** | 最近查看 | ✅ 已完成 | user_prefs.recent_viewed、工作台 chips |
| **P69** | 文档与 v3.7 | ✅ 已完成 | EVOLUTION 661–690、v3.7.0 step 690 |
| **P70** | 组合涨跌贡献 | ✅ 已完成 | contribution、工作台 📈 expander |
| **P71** | 侧边栏折叠状态 | ✅ 已完成 | user_prefs.sidebar_collapsed、快速上手 expander |
| **P72** | 文档与 v3.8 | ✅ 已完成 | EVOLUTION 691–720、v3.8.0 step 720 |
| **P73** | 相对板块强弱 | ✅ 已完成 | sector_relative、工作台 🏆 相对板块 |
| **P74** | 机构式一页纸 | ✅ 已完成 | institutional_onepager、📄 下载一页纸 |
| **P75** | 文档与 v3.9 | ✅ 已完成 | EVOLUTION 721–750、v3.9.0 step 750 |
| **P76** | 板块龙头对标 | ✅ 已完成 | sector_leader、工作台 👑 龙头对标 |
| **P77** | 一页纸 cron 推送 | ✅ 已完成 | push_digest `--with-onepager`、重点提醒摘要 |
| **P78** | 文档与 v4.0 | ✅ 已完成 | EVOLUTION 751–780、v4.0.0 step 780 |
| **P79** | 风险雷达 | ✅ 已完成 | risk_radar、工作台 ⚠️ 风险雷达 |
| **P80** | 每日作战清单 | ✅ 已完成 | battle_plan、📋 今日作战清单 |
| **P81** | 文档与 v4.1 | ✅ 已完成 | EVOLUTION 781–810、v4.1.0 step 810 |
| **P82** | 作战清单 cron | ✅ 已完成 | battle_plan_cron.py、STOCK_USER、--stdout |
| **P83** | 风险汇总推送 | ✅ 已完成 | digest 含 risk_radar 摘要（提醒时） |
| **P84** | 文档与 v4.2 | ✅ 已完成 | EVOLUTION 811–840、v4.2.0 step 840 |
| **P85** | 多标的作战优先级 | ✅ 已完成 | priority_queue、🎯 今日优先关注 |
| **P86** | 合并导出包 | ✅ 已完成 | battle+digest+onepager zip/md 下载 |
| **P87** | 文档与 v4.3 | ✅ 已完成 | EVOLUTION 841–870、v4.3.0 step 870 |
| **P88** | 优先级 Webhook 推送 | ✅ 已完成 | digest Top 3、`STOCK_PUSH_PRIORITY=1` |
| **P89** | 首页作战入口 | ✅ 已完成 | 「今日先看这3只」Top 3 快捷跳转 |
| **P90** | 文档与 v4.4 | ✅ 已完成 | EVOLUTION 871–900、v4.4.0 step 900 |
| **P91** | 900步庆祝 | ✅ 已完成 | milestone_banner 900、公开数据能力地图 |
| **P92** | 一键全开推送 | ✅ 已完成 | `STOCK_PUSH_ALL=1` / `--push-all` cron |
| **P93** | 文档与 v4.5 | ✅ 已完成 | EVOLUTION 901–930、v4.5.0 step 930 |
| **P94** | 能力地图跳转 | ✅ 已完成 | ?tab=watch&expand=、watch_expander_nav |
| **P95** | 公开数据手册 | ✅ 已完成 | docs/PUBLIC_DATA_PLAYBOOK.md、侧边栏链接 |
| **P96** | 文档与 v4.6 | ✅ 已完成 | EVOLUTION 931–960、v4.6.0 step 960 |
| **P97** | 手册内置预览 | ✅ 已完成 | 侧边栏作战手册前 80 行 expander |
| **P98** | 千步预热 | ✅ 已完成 | milestone 1000 预热横幅、页脚千步提示 |
| **P99** | 文档与 v5.0 | ✅ 已完成 | EVOLUTION 961–1000、v5.0.0 step 1000 |
| **P100** | v5庆祝横幅 | ✅ 已完成 | v5_celebration_banner、独立会话旗标 |
| **P101** | 自选健康分 | ✅ 已完成 | portfolio_health、仪表盘 metric、工作台 expander |
| **P102** | 文档与 v5.1 | ✅ 已完成 | EVOLUTION 1001–1030、v5.1.0 step 1030 |
| **P103** | 私人选股花园 | ✅ 已完成 | 默认单页 garden、极简 UI |
| **P104** | 自动筛 A 股 | ✅ 已完成 | daily_picks、买/观望信号 |
| **P105** | 推荐命中率 | ✅ 已完成 | pick_tracker、成绩单、PRIVATE_GARDEN.md、v5.2.0 |

**v5.2 定位**：从「七页功能堆叠」收束为 **私人选股花园** — 一页刷新 A 股推荐、记录并核对命中率；密码门即私密空间；专家模式保留完整能力。在 v5.0 千步里程碑后，用独立 v5 庆祝条收束版本感知，并以「自选健康分」把均分/提醒/新鲜度/板块分散合成 0–100 傻瓜指标，**非**真实风控或交易指令。

**v5.0 定位**：在 v4.6 作战手册基础上，侧边栏内置手册关键章节预览，并以 **1000 步**里程碑收束百步进化周期；强调公开数据流程可读性，**非**真实交易指令。

**v4.6 定位**：在 v4.5 能力地图基础上，深链接直达工作台 expander，并发布「公开数据作战手册」，帮助散户用固定流程对齐机构看板习惯，**非**真实交易指令。

**v4.5 定位**：在 v4.4 注意力聚焦基础上，用「能力地图」串联相对板块/一页纸/作战清单/优先关注，并支持 cron 一键全开推送，**非**真实交易指令。

**v4.2 定位**：在公开数据边缘强化「傻瓜式运维闭环」——定时落盘作战清单、推送摘要自动附带风险旗标汇总，**非**真实风控或交易指令。

## P1：信息架构（本次）

**问题**：7 个 Tab 平铺、功能分散、缺少「读完就能决策」的文档。

**改动**：
1. 侧边栏 **三步工作流**：发现 → 分析 → 导出
2. Tab 按使用顺序编号命名
3. **分析工作台** 增加「可读分析简报」（Markdown，可下载）
4. 行动路线报告可在工作台直接阅读，不必跳转

## P2：代码结构（已完成）

- `app.py` 只负责路由与登录
- 各 Tab 迁入 `src/ui/pages/watch.py` 等
- 单元测试：`tests/test_readable_report.py`、`tests/test_score_stock.py`

## P3：快速分析（已完成）

- 按钮「**一键分析**」：并行拉 K 线 + 评分 + 简报 +（A 股）财务对比摘要 + 行动路线
- 自选股列表显示：最新涨跌幅、评分、一句话摘要（「刷新全部摘要」）

## P4：公网与迭代（已完成）

- `DEPLOY_STREAMLIT.md`：Secrets、Reboot 流程、分享文案模板
- `scripts/cloud_preflight.py`：云端依赖与编译自检（启动脚本 / CI 自动跑）
- 侧边栏 **「📤 分享给同事」**：配置 `STOCK_APP_PUBLIC_URL` 后一键复制说明
- GitHub Actions：push 到 `stock-assistant/` 时跑 preflight + 单元测试
- 迭代：`git push` → Streamlit Cloud **Reboot app**

## P5：智能持久化（已完成）

- **摘要 / 简报落盘**：`watch_snapshots` 与 `brief_md_*` 写入 `data/user_history.json`（v3）
- **今日自选股速览**：工作台一键下载合并 Markdown
- **批量深度分析**：「深度分析前 3 只」并行完整一键分析
- **新手引导**：首页空状态三步提示
- **数据源健康**：侧边栏东财 / Yahoo 连通性检测

## P6：体验极限（已完成）

- **移动端 CSS**：窄屏 Tab/按钮/表格更易点、少横向滚动
- **自动刷新摘要**：工作台可设 5～30 分钟间隔（页面打开时生效，设置会保存）
- **分析合集导出**：合并所有「一键分析」简报 → `.md` 或 `.html`（浏览器打印即 PDF）
- **深色主题**：`.streamlit/config.toml` 统一观感

## P7：智能增强（已完成）

- **板块联动扫描**：多只 A 股自选是否共用行业/概念（工作台 expandable）
- **🔊 朗读摘要**：浏览器 TTS 朗读「一句话」摘要（无需安装插件）
- **只读 snapshot.json**：侧边栏导出，schema `stock-assistant-readonly-v1`（见 [docs/API_READONLY.md](docs/API_READONLY.md)）

## P8：生态扩展（已完成）

（见上文表格与 `docs/PUSH.md`）

## P9–P12：百步进化（已完成）

详见 **[docs/EVOLUTION_100.md](docs/EVOLUTION_100.md)**（120 步全部 ✅）

要点：
- **P9**：`push_log.jsonl`、Webhook/邮件退避重试、重试队列、`STOCK_HEALTH_ALERT_WEBHOOK_URL`
- **P10**：自选股 CSV、筛选/排序、 `scripts/backup_data.py`
- **P11**：页脚 v1.8.0、侧边栏进化日志、snapshot v2
- **P12**：测试 30+、累计进化 step 120

## P16–P18：对比、提醒推送、v2.0（已完成）

- **P16 双股对比**：工作台「📊 双股对比」expander，并排涨跌幅/评分/一句话/财务摘要，可下载 `.md`
- **P17 提醒推送**：`push_webhook_on_alerts` 偏好；有触发项时「推送到 Webhook」；自动刷新后可选自动推送（去重）
- **P18 体验**：`?tab=watch|search|…|1-7` 自动选中主导航；`src/ui/tab_router.py`

## P19–P21：分组、趋势、备份（已完成）

- **P19 自选分组**：`user_prefs.watch_groups`；工作台按分组筛选、分组管理 expander
- **P20 历史趋势**：`src/analysis/trend_summary.py`；最近 N 次分析的评分/涨跌幅走势
- **P21 备份导入**：工作台 JSON 备份下载与合并导入（不覆盖历史 query_log）

## P22–P24：快捷筛选、定时摘要、体验抛光（已完成）

- **P22 快捷筛选**：`src/ui/quick_actions.py`；搜索页预设筛选（涨幅/评分/有摘要）+ 可复制代码列表
- **P23 定时摘要**：`push_digest_cron.py` 摘要嵌入提醒段落；`--alerts-only` 仅在有触发项时推送
- **P24 体验抛光**：`user_prefs.dark_mode` 侧边栏切换；v2.2.0 step 240

## P25–P27：板块分布、批量操作、v2.3（已完成）

- **P25 板块热力图 lite**：`src/analysis/sector_heatmap.py`；工作台「🗺 板块分布」按 fin_summary/简报聚合
- **P26 批量操作**：多选标的 → 批量移出自选 / 批量加入分组；`src/util/batch_watch_ops.py`
- **P27 文档与 v2.3**：EVOLUTION_100 步 241–270；v2.3.0 step 270；README cron `--alerts-only` 说明

## P28–P30：笔记、缓存、v2.4（已完成）

- **P28 笔记/标注**：`user_prefs.watch_notes`；工作台单标的「📝 笔记/标注」expander，持久化到 `user_history.json`
- **P29 性能/缓存**：`src/util/fetch_cache.py`；同一批 ticker 60 秒内重复「刷新全部摘要」/自动刷新跳过网络拉取
- **P30 文档与 v2.4**：EVOLUTION_100 步 271–300；v2.4.0 step 300；`evolve_verify.sh` 覆盖 P28–P30 测试

## P31–P33：笔记导出、健康面板、v2.5（已完成）

- **P31 笔记导出**：`format_notes_digest_section`；速览 Markdown、CSV「笔记」列、JSON 备份 `watch_notes`；cron/推送摘要同步
- **P32 健康面板**：`cache_stats`、上次摘要刷新时间、推送日志尾部 5 条；`test_p32_health_panel` 逻辑测试
- **P33 文档与 v2.5**：EVOLUTION_100 步 301–330；v2.5.0 step 330；`evolve_verify.sh` 覆盖 P31–P33 测试

## P34–P36：搜索历史、提醒模板、v2.6（已完成）

- **P34 搜索历史**：`user_prefs.search_history`（最近 20 条）；搜索页 chips 一键重搜；`test_p34_search_history`
- **P35 提醒模板**：`src/util/alert_profiles.py`；保守/均衡/激进 pct/score 阈值；alert_panel 一键套用
- **P36 文档与 v2.6**：EVOLUTION_100 步 331–360；v2.6.0 step 360；`evolve_verify.sh` 覆盖 P34–P36 测试

## P37–P39：工作台仪表盘、只读分享、v2.7（已完成）

- **P37 工作台仪表盘**：`src/analysis/dashboard_stats.py`；工作台顶部均分/上涨/下跌/今日提醒 metrics；`test_p37_dashboard_stats`
- **P38 只读分享**：`?readonly=1` 隐藏加入自选、刷新、批量操作、分析写入；snapshot meta 含 `readonly_mode`；`test_p38_readonly_param`
- **P39 文档与 v2.7**：EVOLUTION_100 步 361–390；v2.7.0 step 390；`evolve_verify.sh` 覆盖 P37–P39 测试

## P40–P42：多语言、快捷键提示、v2.8（已完成）

- **P40 多语言文案**：`src/util/i18n_strings.py`；`user_prefs.locale` zh/en；Tab 名与工作台 metrics；侧边栏语言切换；`test_p40_i18n`
- **P41 快捷键提示**：页脚 `?tab=` / `?readonly=1` 链接提示；`test_p41_hints`
- **P42 文档与 v2.8**：EVOLUTION_100 步 391–420；v2.8.0 step 420；`evolve_verify.sh` 覆盖 P40–P42 测试

## P43–P45：自选排序、分析周报、v2.9（已完成）

- **P43 自选排序**：`src/util/watch_sort.py`；`user_prefs.watch_sort` by score/pct/name + asc/desc；工作台排序下拉持久化；`test_p43_watch_sort`
- **P44 分析周报**：`src/analysis/weekly_report.py`；近 7 日 query_log + 自选统计 Markdown；历史页「下载周报」；`test_p44_weekly_report`
- **P45 文档与 v2.9**：EVOLUTION_100 步 421–450；v2.9.0 step 450；`evolve_verify.sh` 覆盖 P43–P45 测试

## P46–P48：价格目标、新鲜度徽章、v3.0（已完成）

- **P46 价格目标提醒**：`src/util/price_targets.py`；`user_prefs.price_targets` ticker→{above,below}；`watch_alerts` 现价对比；alert_panel + 工作台 🎯 expander；`test_p46_price_targets`
- **P47 数据新鲜度徽章**：`src/util/freshness_badge.py`；`user_prefs.stale_hours` 默认 24h；摘要超期显示 ⏳ stale；`test_p47_freshness`
- **P48 文档与 v3.0**：EVOLUTION_100 步 451–480；v3.0.0 step 480；`evolve_verify.sh` 覆盖 P46–P48 测试

## P49–P51：组合权重、周报 cron、v3.1（已完成）

- **P49 组合权重视图**：`src/util/watch_weights.py`；`user_prefs.watch_weights` ticker→weight%；工作台「⚖ 权重」expander 饼图（等权或归一化）；`test_p49_weights`
- **P50 cron 周报**：`scripts/weekly_report_cron.py`；`STOCK_USER` 读 history；写入 `data/weekly_report_YYYYMMDD.md` 或 `--stdout`；`test_p50_weekly_cron`
- **P51 文档与 v3.1**：EVOLUTION_100 步 481–510；v3.1.0 step 510；`evolve_verify.sh` 覆盖 P49–P51 测试

## P52–P54：相似股、会话欢迎、v3.2（已完成）

- **P52 相似股推荐 lite**：`src/analysis/similar_pick.py`；按自选板块与快照评分推荐 1–3 只同板块标的（无外部 API）；工作台「🔗 相似股推荐」expander；`test_p52_similar`
- **P53 会话恢复提示**：`src/ui/welcome_banner.py`；历史含自选时启动展示数量与上次刷新；`history_store._restored_watchlist`；`test_p53_welcome`
- **P54 文档与 v3.2**：EVOLUTION_100 步 511–540；v3.2.0 step 540；`evolve_verify.sh` 覆盖 P52–P54 测试

## P55–P57：分析置顶、失败重试、v3.3（已完成）

- **P55 分析结果置顶**：`src/util/pinned_tickers.py`；`user_prefs.pinned_tickers` 列表；排序后仍置顶；工作台「📌 置顶」expander；`test_p55_pinned`
- **P56 错误重试 UI**：`src/util/retry_fetch_ui.py`；摘要拉取失败时逐行 🔄 重试；`test_p56_retry_ui`
- **P57 文档与 v3.3**：EVOLUTION_100 步 541–570；v3.3.0 step 570；`evolve_verify.sh` 覆盖 P55–P57 测试

## P58–P60：快捷加自选、邮件主题、v3.4（已完成）

- **P58 快捷添加自选**：`src/util/watchlist_add.py`；搜索页每行「加入自选」按钮（非只读）；`test_p58_quick_add`
- **P59 汇总邮件主题行**：`digest_push.format_digest_email_subject`；日期 + 提醒条数；`test_p59_email_subject`
- **P60 文档与 v3.4**：EVOLUTION_100 步 571–600；v3.4.0 step 600；`evolve_verify.sh` 覆盖 P58–P60 测试

## P61–P63：600步庆祝、失败汇总、v3.5（已完成）

- **P61 600步庆祝横幅**：`src/ui/milestone_banner.py`；step≥600 时会话内一次性 confetti 风格 info 条；侧边栏链接 `docs/EVOLUTION_100.md`；`test_p61_milestone`
- **P62 批量刷新失败汇总**：`src/util/fetch_failures_summary.py`；刷新后可折叠「失败 N 只」+ 代码复制；`test_p62_failures_summary`
- **P63 文档与 v3.5**：EVOLUTION_100 步 601–630；v3.5.0 step 630；`evolve_verify.sh` 覆盖 P61–P63 测试

## P64–P66：CSV 导入、静默时段、v3.6（已完成）

- **P64 自选 CSV 导入**：`src/util/watchlist_csv_import.py`；工作台上传 CSV 代码列合并进自选（去重）；`test_p64_csv_import`
- **P65 提醒静默时段**：`user_prefs.quiet_hours` {start,end} 本地小时；`alert_push` 自动推送路径跳过静默窗口；`test_p65_quiet_hours`
- **P66 文档与 v3.6**：EVOLUTION_100 步 631–660；v3.6.0 step 660；`evolve_verify.sh` 覆盖 P64–P66 测试

## P67–P69：CSV 导出、最近查看、v3.7（已完成）

- **P67 自选 CSV 导出**：`src/util/watchlist_csv_export.py`；导出 code/name/score/pct/note/group；工作台 📊 导出 CSV；`test_p67_csv_export`
- **P68 最近查看**：`user_prefs.recent_viewed`（最近 10 只）；分析工作台 chips 切换标的；`test_p68_recent_viewed`
- **P69 文档与 v3.7**：EVOLUTION_100 步 661–690；v3.7.0 step 690；`evolve_verify.sh` 覆盖 P67–P69 测试

## P70–P72：涨跌贡献、侧边栏折叠、v3.8（已完成）

- **P70 组合涨跌贡献**：`src/analysis/contribution.py`；各标的加权贡献组合涨跌幅（watch_weights 或等权）；工作台「📈 涨跌贡献」expander；`test_p70_contribution`
- **P71 侧边栏折叠状态**：`src/util/sidebar_state.py`；`user_prefs.sidebar_collapsed`；快速上手 expander + 折叠偏好；`test_p71_sidebar_state`
- **P72 文档与 v3.8**：EVOLUTION_100 步 691–720；v3.8.0 step 720；`evolve_verify.sh` 覆盖 P70–P72 测试

## P73–P75：相对板块、机构一页纸、v3.9（已完成）

- **P73 相对板块强弱**：`src/analysis/sector_relative.py`；自选内同板块均涨跌幅/均评分对比；工作台「🏆 相对板块」expander；`test_p73_sector_relative`
- **P74 机构式一页纸**：`src/analysis/institutional_onepager.py`；结论/相对板块/风险/下一步 Markdown；工作台「📄 下载机构式一页纸」；`test_p74_onepager`
- **P75 文档与 v3.9**：EVOLUTION_100 步 721–750；v3.9.0 step 750；公开数据拼装定位；`evolve_verify.sh` 覆盖 P73–P75 测试

## P76–P78：板块龙头、一页纸推送、v4.0（已完成）

- **P76 板块龙头对标**：`src/analysis/sector_leader.py`；自选同板块内标龙头（评分/涨跌幅）；展示距龙头差距；工作台「👑 板块龙头对标」expander；`test_p76_sector_leader`
- **P77 一页纸 cron 推送**：`build_onepager_push_summary`；`push_digest_cron.py --with-onepager` / `STOCK_PUSH_ONEPAGER=1`；重点提醒标的一页纸摘要；`test_p77_onepager_push`
- **P78 文档与 v4.0**：EVOLUTION_100 步 751–780；v4.0.0 step 780；公开数据边缘对标；`evolve_verify.sh` 覆盖 P76–P78 测试

## P79–P81：风险雷达、作战清单、v4.1（已完成）

- **P79 风险雷达**：`src/analysis/risk_radar.py`；从快照评分分解或默认值输出 3 条风险旗标（波动/评分偏低/stale/跑输板块）；工作台「⚠️ 风险雷达」expander；`test_p79_risk_radar`
- **P80 每日作战清单**：`src/analysis/battle_plan.py`；dashboard stats + alerts + Top 3 行动 Markdown；工作台/历史页「📋 今日作战清单」；`test_p80_battle_plan`
- **P81 文档与 v4.1**：EVOLUTION_100 步 781–810；v4.1.0 step 810；开盘前决策定位；`evolve_verify.sh` 覆盖 P79–P81 测试

## P82–P84：作战 cron、风险推送、v4.2（已完成）

- **P82 作战清单 cron**：`scripts/battle_plan_cron.py`；`STOCK_USER` 读 history；写入 `data/battle_plan_YYYYMMDD.md` 或 `--stdout`；`test_p82_battle_cron`
- **P83 风险汇总推送**：`format_risk_digest_section`；提醒存在时在 digest 附带 risk_radar 计数与 Top 旗标；`test_p83_risk_digest`
- **P84 文档与 v4.2**：EVOLUTION_100 步 811–840；v4.2.0 step 840；傻瓜式运维闭环；`evolve_verify.sh` 覆盖 P82–P84 测试

## P85–P87：作战优先级、合并导出、v4.3（已完成）

- **P85 多标的作战优先级**：`src/analysis/priority_queue.py`；提醒 + 风险旗标 + 跑输板块综合排序 Top 5；工作台「🎯 今日优先关注」expander；`test_p85_priority`
- **P86 合并导出包**：`src/export/priority_bundle.py`；作战清单 + 速览 + 优先标的一页纸；`.md` / `.zip` 下载；`test_p86_export_bundle`
- **P87 文档与 v4.3**：EVOLUTION_100 步 841–870；v4.3.0 step 870；多标的注意力分配；`evolve_verify.sh` 覆盖 P85–P87 测试

## P88–P90：优先级推送、首页入口、v4.4（已完成）

- **P88 优先级 Webhook 推送**：`format_priority_digest_section`；`push_digest_cron.py --with-priority` / `STOCK_PUSH_PRIORITY=1`；digest/webhook 附带 Top 3 优先标的；`test_p88_priority_push`
- **P89 首页作战入口**：`src/ui/priority_home.py`；首页「🎯 今日先看这3只」Top 3 按钮直达工作台；`test_p89_priority_home`
- **P90 文档与 v4.4**：EVOLUTION_100 步 871–900；v4.4.0 step 900；开盘前注意力聚焦；`evolve_verify.sh` 覆盖 P88–P90 测试

## P91–P93：900步庆祝、能力地图、一键全开、v4.5（已完成）

- **P91 900步庆祝 + 能力地图**：`milestone_banner` step≥900；侧边栏「公开数据能力地图」列出相对板块/一页纸/作战清单/优先关注；`test_p91_capability_map`
- **P92 一键全开推送**：`push_digest_cron.py --push-all` / `STOCK_PUSH_ALL=1`；cron 同时附带提醒+一页纸+优先关注；`test_p92_push_all`
- **P93 文档与 v4.5**：EVOLUTION_100 步 901–930；v4.5.0 step 930；公开数据能力串联；`evolve_verify.sh` 覆盖 P91–P93 测试

## P94–P96：能力地图跳转、公开数据手册、v4.6（已完成）

- **P94 能力地图快捷跳转**：`src/util/watch_expander_nav.py`；能力地图条目 `?tab=watch&expand=` 一次性展开工作台 expander；`test_p94_capability_links`
- **P95 公开数据作战手册**：`docs/PUBLIC_DATA_PLAYBOOK.md`；散户用公开数据建立每日流程；功能对照能力地图；侧边栏链接
- **P96 文档与 v4.6**：EVOLUTION_100 步 931–960；v4.6.0 step 960；深链接 + 作战手册；`evolve_verify.sh` 覆盖 P94–P96 测试

## P97–P99：手册预览、千步预热、v5.0（已完成）

- **P97 作战手册内置预览**：`src/ui/playbook_preview.py`；侧边栏 expander 展示 `PUBLIC_DATA_PLAYBOOK.md` 前 80 行关键章节；`test_p97_playbook_preview`
- **P98 千步预热**：`milestone_banner` step 960–999 预热条；页脚 `build_footer_warmup_note` 千步倒计时；`test_p98_milestone_warmup`
- **P99 文档与 v5.0**：EVOLUTION_100 步 961–1000；v5.0.0 step 1000；千步里程碑庆祝；`evolve_verify.sh` 覆盖 P97–P99 测试

## P100–P102：v5庆祝、自选健康分、v5.1（已完成）

- **P100 v5 千步庆祝横幅**：`src/ui/v5_celebration_banner.py`；step≥1000 时会话内一次性 info 条，与 `milestone_banner` 独立旗标；`test_p100_celebration`
- **P101 自选健康分**：`src/analysis/portfolio_health.py`；均分 40% + 低提醒 25% + 数据新鲜 20% + 板块分散 15% → 0–100；标签 健康/一般/需关注；仪表盘 metric + 工作台 expander；`test_p101_portfolio_health`
- **P102 文档与 v5.1**：EVOLUTION_100 步 1001–1030；v5.1.0 step 1030；`evolve_verify.sh` 覆盖 P100–P102 测试

## 进化原则

1. **先可读，再炫功能** — 每轮至少产出一种「能发给同事看的资料」
2. **先本地稳，再公网** — 本地 `启动网页.command` 通过后再部署
3. **小步提交** — 每个 Phase 独立 commit，便于任意终端 `git pull` 回滚

## 本地验证清单

```bash
cd stock-assistant
source .venv/bin/activate
python3 -m py_compile app.py
streamlit run app.py
```

- [x] 登录正常
- [x] 工作台 → 选标的 → 生成可读简报 → 下载 .md
- [x] 全球搜索 → 加入自选股
- [x] 板块/榜单可刷新
- [x] 自选股「刷新全部摘要」显示涨跌幅/评分/一句话
- [x] 「一键分析」生成简报 + 行动路线 + A 股财务摘要
- [x] `python3 scripts/cloud_preflight.py` 通过后可 push / Reboot Cloud
- [x] 侧边栏分享文案（配置 `STOCK_APP_PUBLIC_URL`）
- [x] 关闭浏览器后再开，自选股摘要/简报仍保留（`data/user_history.json`）
- [x] 下载「今日自选股速览」合并 Markdown
- [x] 自动刷新自选股摘要（⏱ 可设间隔）
- [x] 下载「分析合集」HTML / Markdown（可打印 PDF）
- [x] 板块联动扫描（A 股多自选）
- [x] 朗读一句话摘要 · 导出 snapshot.json
- [x] Webhook / 邮件推送速览 · 多用户密码隔离
- [x] 推送日志 + 重试队列 + 健康告警 Webhook
- [x] 自选股 CSV / 筛选 / 排序
- [x] **120 步进化完成**（见 docs/EVOLUTION_100.md）
- [x] 智能提醒阈值（🔔 涨跌幅/评分）
- [x] 历史记录导出 CSV · `scripts/evolve_verify.sh`
- [x] v1.9.0 · 进化 step 150
- [x] 双股对比 expander · 下载对比 Markdown
- [x] 提醒 Webhook 推送 · push_webhook_on_alerts
- [x] ?tab= 深链接自动打开对应页 · v2.0.0 step 180
- [x] 自选股分组筛选与管理 · watch_groups
- [x] 分析历史趋势 expander · trend_summary
- [x] JSON 备份下载/合并导入 · v2.1.0 step 210
- [x] 搜索页快捷筛选 · 代码列表复制 · P22
- [x] cron 摘要含提醒 · --alerts-only · P23
- [x] 深色模式偏好 · v2.2.0 step 240 · P24
- [x] 板块分布热力图 lite · 批量自选操作 · P25–P26
- [x] v2.3.0 · 进化 step 270 · P27
- [x] 自选笔记/标注 · watch_notes · P28
- [x] 摘要刷新 in-session 缓存 · fetch_cache · P29
- [x] v2.4.0 · 进化 step 300 · P30
- [x] 笔记导出到速览/CSV/JSON · watch_notes · P31
- [x] 健康面板缓存/刷新/推送尾 · P32
- [x] v2.5.0 · 进化 step 330 · P33
- [x] 搜索历史 chips · search_history · P34
- [x] 提醒模板 保守/均衡/激进 · alert_profiles · P35
- [x] v2.6.0 · 进化 step 360 · P36
- [x] 工作台仪表盘 · dashboard_stats · P37
- [x] 只读分享 ?readonly=1 · P38
- [x] v2.7.0 · 进化 step 390 · P39
- [x] 多语言 Tab/仪表盘 · locale zh/en · P40
- [x] 页脚链接提示 ?tab= ?readonly=1 · P41
- [x] v2.8.0 · 进化 step 420 · P42
- [x] 自选排序偏好 watch_sort · P43
- [x] 历史页周报下载 weekly_report · P44
- [x] v2.9.0 · 进化 step 450 · P45
- [x] 价格目标提醒 price_targets · P46
- [x] 摘要 stale 徽章 stale_hours · P47
- [x] v3.0.0 · 进化 step 480 · P48
- [x] 组合权重饼图 watch_weights · P49
- [x] cron 周报 weekly_report_cron · P50
- [x] v3.1.0 · 进化 step 510 · P51
- [x] 相似股推荐 similar_pick · 工作台同板块 · P52
- [x] 会话恢复欢迎条 welcome_banner · P53
- [x] v3.2.0 · 进化 step 540 · P54
- [x] 分析置顶 pinned_tickers · 工作台 📌 · P55
- [x] 摘要失败逐行重试 retry_fetch_ui · P56
- [x] v3.3.0 · 进化 step 570 · P57
- [x] 搜索页逐行加入自选 watchlist_add · P58
- [x] 汇总邮件主题 日期+提醒数 · P59
- [x] v3.4.0 · 进化 step 600 · P60
- [x] 600步庆祝横幅 milestone_banner · P61
- [x] 刷新失败汇总 fetch_failures_summary · P62
- [x] v3.5.0 · 进化 step 630 · P63
- [x] 自选 CSV 导出 code/name/score/pct/note/group · P67
- [x] 最近查看 chips recent_viewed · P68
- [x] v3.7.0 · 进化 step 690 · P69
- [x] 组合涨跌贡献 contribution · P70
- [x] 侧边栏折叠 sidebar_collapsed · P71
- [x] v3.8.0 · 进化 step 720 · P72
- [x] 相对板块强弱 sector_relative · P73
- [x] 机构式一页纸 institutional_onepager · P74
- [x] v3.9.0 · 进化 step 750 · P75
- [x] 板块龙头对标 sector_leader · P76
- [x] 一页纸 cron 推送 --with-onepager · P77
- [x] v4.0.0 · 进化 step 780 · P78
- [x] 风险雷达 risk_radar · 工作台 ⚠️ · P79
- [x] 每日作战清单 battle_plan · 📋 下载 · P80
- [x] v4.1.0 · 进化 step 810 · P81
- [x] 作战清单 cron battle_plan_cron · P82
- [x] 风险汇总推送 risk_digest · P83
- [x] v4.2.0 · 进化 step 840 · P84
- [x] 多标的作战优先级 priority_queue · 🎯 · P85
- [x] 合并导出包 priority_bundle · 📦 · P86
- [x] v4.3.0 · 进化 step 870 · P87
- [x] 优先级 digest 推送 --with-priority · P88
- [x] 首页今日先看这3只 priority_home · P89
- [x] v4.4.0 · 进化 step 900 · P90
- [x] 900步庆祝横幅 + 能力地图 capability_map · P91
- [x] cron 一键全开推送 STOCK_PUSH_ALL · P92
- [x] v4.5.0 · 进化 step 930 · P93
- [x] 能力地图深链接 watch_expander_nav · ?tab=watch&expand= · P94
- [x] 公开数据作战手册 PUBLIC_DATA_PLAYBOOK · P95
- [x] v4.6.0 · 进化 step 960 · P96
- [x] 作战手册内置预览 playbook_preview · P97
- [x] 千步预热横幅 + 页脚提示 · P98
- [x] v5.0.0 · 进化 step 1000 · P99
- [x] v5 庆祝横幅 v5_celebration_banner · P100
- [x] 自选健康分 portfolio_health · 仪表盘 + expander · P101
- [x] v5.1.0 · 进化 step 1030 · P102
