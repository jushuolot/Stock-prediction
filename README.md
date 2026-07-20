# Stock prediction · Stock Assistant（Streamlit 股票助手）

仓库：https://github.com/jushuolot/Stock-prediction

在浏览器里完成：**一键筛 A 股 · 看买/观望 · 核对涨没涨**。默认 **🌱 私人选股花园**（单页极简）；侧边栏可进专家七页。  
**v5.2.0 · 1060 步** — 自动推荐 + 命中率成绩单 · 私密部署 [docs/PRIVATE_GARDEN.md](docs/PRIVATE_GARDEN.md)

---

## 文档索引

| 文档 | 说明 | 适合谁 |
|------|------|--------|
| [docs/CLOUD_ONLY.md](docs/CLOUD_ONLY.md) | **零本地**：全靠 GitHub + Streamlit Cloud，电脑只打开浏览器 | 机器配置低、不想本地跑 |
| [docs/PRIVATE_GARDEN.md](docs/PRIVATE_GARDEN.md) | **私人花园**：免费密码门、每晚查岗、A 股自动推荐 | 只想简单选股的人 |
| [docs/PUBLIC_DATA_PLAYBOOK.md](docs/PUBLIC_DATA_PLAYBOOK.md) | 散户公开数据作战手册（能力地图功能对照） | 想用免费数据建立每日流程 |
| [docs/PRODUCT.md](docs/PRODUCT.md) | 产品定位、功能地图、使用场景、数据来源、局限、公网访问 | 想先了解「这是什么」 |
| [docs/USER_GUIDE.md](docs/USER_GUIDE.md) | 编号步骤：本地启动、登录、自选股、生成简报、Streamlit Cloud | 第一次上手操作 |
| [EVOLUTION.md](EVOLUTION.md) | P1～P8 进化路线与验证清单 | 关心后续规划 |
| [docs/PUSH.md](docs/PUSH.md) | Webhook / 邮件 / 多用户 / cron | 自动推送同事 |
| [docs/API_READONLY.md](docs/API_READONLY.md) | 只读 JSON 快照 schema | 脚本对接 / 自动化 |
| [DEPLOY_STREAMLIT.md](DEPLOY_STREAMLIT.md) | Streamlit Cloud 公网部署专篇 | 要给同事发链接 |

---

## 本地运行（简版）

完整步骤见 [docs/USER_GUIDE.md](docs/USER_GUIDE.md#1-本地启动在你自己的电脑上)。

```bash
cd stock-assistant
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # 修改密码
streamlit run app.py
```

浏览器打开 http://localhost:8501 ，使用 `secrets.toml` 中的密码登录。

或双击 `启动网页.command`（macOS）。

**定时推送（cron）**：仅在有涨跌幅/评分提醒触发时推送摘要，可加 `--alerts-only`：

```bash
python3 scripts/push_digest_cron.py --alerts-only
```

---

## 公网部署（同事测试）

推荐 **Streamlit Community Cloud**，详见 [DEPLOY_STREAMLIT.md](DEPLOY_STREAMLIT.md) 与 [docs/USER_GUIDE.md §5](docs/USER_GUIDE.md#5-部署到-streamlit-cloud给同事公网访问)。

| 配置项 | 值 |
|--------|-----|
| Main file path | `stock-assistant/app.py` |
| Secrets | `STOCK_ASSISTANT_PASSWORD = "强密码"` |
| 可选 | `STOCK_APP_PUBLIC_URL = "https://xxx.streamlit.app"`（侧边栏生成分享文案） |

部署前自检：`python3 scripts/cloud_preflight.py`（详见 [DEPLOY_STREAMLIT.md](DEPLOY_STREAMLIT.md)）

其他方式（Railway / Render、临时隧道）见 [docs/PRODUCT.md §6](docs/PRODUCT.md#6-公网访问)。

---

## 配置说明

| 文件 | 说明 |
|------|------|
| `.streamlit/secrets.toml.example` | 密码模板，复制为 `secrets.toml`（勿提交） |
| `.streamlit/config.toml` | Streamlit 主题与端口 |
| `requirements.txt` | Python 依赖 |

---

## 勿提交

- `.streamlit/secrets.toml`
- `.venv/`、`data/`、`__pycache__/`
