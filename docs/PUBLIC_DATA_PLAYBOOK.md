# 公开数据作战手册（散户如何用免费数据跑赢信息差）

> **定位**：用东方财富等**公开行情** + 本 App 的**规则整理**，把机构研究员的「看板习惯」搬到个人电脑。**不是**内幕、**不是**投资建议。

**App 入口**：侧边栏「公开数据能力地图」→ 点条目直达 `① 分析工作台` 对应区块。

---

## 1. 机构 vs 散户：差在哪？

| 维度 | 机构常见做法 | 散户可用替代（本 App） |
|------|-------------|------------------------|
| 晨会清单 | 研究员汇总 overnight + 自选股 | **作战清单** `battle_plan` · [?tab=watch&expand=battle_plan](?tab=watch&expand=battle_plan) |
| 相对强弱 | 行业指数 vs 个股 | **相对板块** `sector_relative` · 自选内同板块均值对比 |
| 一页结论 | 内部 memo 给 PM | **机构一页纸** `institutional_onepager` · 可下载 / cron 推送 |
| 注意力分配 | 交易员盯 Top 3 | **优先关注** `priority_queue` · 首页「今日先看这 3 只」 |
| 风险旗标 | 风控系统 | **风险雷达** `risk_radar` · 波动/评分/stale/跑输板块 |
| 定时推送 | 邮件 digest | `scripts/push_digest_cron.py` · `--push-all` 一键全开 |

**核心思路**：机构优势在**流程与注意力**，不是魔法公式。公开数据 + 固定流程，足以消除「不知道先看哪只」的摩擦。

---

## 2. 每日 15 分钟流程（傻瓜版）

### 08:30 开盘前 — 定顺序

1. 打开 App 首页 → **🎯 今日先看这 3 只**（`priority_home`）
2. 或侧边栏能力地图 → **[🎯 优先关注](?tab=watch&expand=priority_queue)**
3. 有 cron 时：`python3 scripts/push_digest_cron.py --push-all` 把提醒 + 一页纸 + 优先关注推到 Webhook/邮件

### 09:35 开盘后 — 看相对强弱

1. `① 分析工作台` → **刷新全部摘要**
2. 展开 **[🏆 相对板块](?tab=watch&expand=sector_relative)**：谁跑赢/跑输自选内同板块均值
3. 展开 **👑 板块龙头对标**：自选内谁是板块龙头、你离龙头差多少

### 午间 / 收盘前 — 留痕给未来的自己

1. 对重点标的 **一键分析** → **生成可读简报**
2. 展开 **[📄 机构一页纸](?tab=watch&expand=institutional_onepager)** → 下载 `.md` 或等 cron `--with-onepager`
3. 展开 **[📋 作战清单](?tab=watch&expand=battle_plan)** → 下载今日行动列表

### 收盘后 — 归档

- **历史记录** Tab：趋势、周报
- **合并导出包**（有优先标的时）：作战清单 + 速览 + 一页纸 `.zip`

---

## 3. 能力地图 → App 功能对照

| 能力地图条目 | 模块 ID | 工作台位置 | 深链接 |
|-------------|---------|-----------|--------|
| 🏆 相对板块 | `sector_relative` | 🏆 相对板块 expander | `?tab=watch&expand=sector_relative` |
| 📄 机构一页纸 | `institutional_onepager` | 单标的 📄 机构一页纸 expander | `?tab=watch&expand=institutional_onepager` |
| 📋 作战清单 | `battle_plan` | 📋 作战清单 expander + 顶部下载 | `?tab=watch&expand=battle_plan` |
| 🎯 优先关注 | `priority_queue` | 🎯 今日优先关注 expander | `?tab=watch&expand=priority_queue` |

**相关能力（未列入地图但同属公开数据链）**：

- **风险雷达** — 单标的 ⚠️ expander（有旗标时自动展开）
- **板块分布** — 🗺 expander（热力图式计数）
- **智能提醒** — 🔔 涨跌幅/评分/价格目标
- **双股对比** — 📊 并排两只自选

---

## 4. 推送与自动化（不输机构 digest）

```bash
# 仅提醒触发时推送摘要
python3 scripts/push_digest_cron.py --alerts-only

# 附带 Top 3 优先关注
python3 scripts/push_digest_cron.py --with-priority

# 附带重点提醒的一页纸摘要
python3 scripts/push_digest_cron.py --with-onepager

# P92：提醒 + 一页纸 + 优先关注全开（或 STOCK_PUSH_ALL=1）
python3 scripts/push_digest_cron.py --push-all
```

作战清单独立 cron：`python3 scripts/battle_plan_cron.py`

---

## 5. 常见误区

| 误区 | 事实 |
|------|------|
| 「公开数据没用」 | 相对板块、龙头对标、优先级排序都**不依赖** Level-2 或持仓 |
| 「要像机构一样看 50 只」 | App 设计为 **Top 3–5 注意力**；其余放自选备查 |
| 「评分 = 买卖信号」 | 评分为规则型快照整理；一页纸末尾有免责声明 |
| 「推送 = 自动交易」 | 推送仅为 Markdown 摘要；**无**下单接口 |

---

## 6. 验证清单（本地）

```bash
cd stock-assistant
source .venv/bin/activate
bash scripts/evolve_verify.sh
streamlit run app.py
```

- [ ] 侧边栏能力地图四条链接均能打开工作台并展开对应区块
- [ ] 首页 Top 3 按钮跳转工作台并选中标的
- [ ] 刷新摘要后相对板块 / 优先关注有数据
- [ ] 下载一页纸 / 作战清单 `.md` 可发给同事

---

## 7. 进一步阅读

| 文档 | 内容 |
|------|------|
| [EVOLUTION.md](../EVOLUTION.md) | P1–P99 进化路线 |
| [docs/EVOLUTION_100.md](EVOLUTION_100.md) | 1000 步功能清单 |
| [docs/USER_GUIDE.md](USER_GUIDE.md) | 本地启动与登录 |
| [docs/PUSH.md](PUSH.md) | Webhook / 邮件 / cron |
| [docs/PRODUCT.md](PRODUCT.md) | 产品定位与数据来源 |

*公开数据作战手册 · Stock Assistant v5.0.0 · 非投资建议*
