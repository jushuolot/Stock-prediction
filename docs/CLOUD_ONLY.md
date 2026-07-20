# 零本地 · 全公网进化指南

> **你的电脑只用来打开浏览器。** 扫盘、测试、进化全在 **GitHub + Streamlit Cloud** 上完成。

## 三件事记住就够

| 谁 | 在哪跑 | 干什么 |
|----|--------|--------|
| **你** | 手机/任意浏览器 | 打开 `.streamlit.app` → 看推荐 → 核对成绩单 |
| **GitHub Actions** | 微软云端服务器 | 每晚 20:00 自动扫 A 股，结果写进仓库 |
| **我（助手）** | 推代码到 GitHub | 功能进化；你点 Streamlit **Reboot** 即升级 |

**不需要** 本地 `streamlit run`、不需要高配电脑。

---

## 第一次：5 分钟建好私人花园（只做一次）

1. 打开 https://share.streamlit.io → GitHub 登录  
2. **Create app**  
   - Repository: `jushuolot/jinshouzhi`  
   - Main file: `stock-assistant/app.py`  
   - Python: **3.11**  
3. **Secrets** 粘贴：

```toml
STOCK_ASSISTANT_PASSWORD = "只有你知道的密码"
STOCK_CLOUD_HOST = "streamlit"
STOCK_APP_PUBLIC_URL = "https://你的应用.streamlit.app"
```

4. **Deploy** → 复制链接，收藏到手机桌面  

详细图文：[DEPLOY_STREAMLIT.md](../DEPLOY_STREAMLIT.md)

---

## 每晚「佛祖查岗」（30 秒）

1. 打开 Streamlit 链接，输入密码  
2. 若见 **「云端昨夜已扫盘」** → 直接看表格  
3. 或点 **刷新今日 A 股推荐**（算力在 **Streamlit 服务器**，不占你电脑）  
4. 点 **核对推荐成绩单**  

可选：在 GitHub 仓库 **Settings → Secrets** 配置 `STOCK_WEBHOOK_URL`，每晚 Actions 会把推荐推到你的微信/钉钉机器人。

---

## 进化怎么发生（你不用本地跑）

```
助手改代码 → git push → GitHub Actions 跑测试
                      → 每晚 garden-daily-cloud 扫盘
                      → Streamlit Cloud Reboot（或等自动更新）
                      → 你打开网页就是新版
```

手动触发扫盘：GitHub 仓库 **Actions** → **garden-daily-cloud** → **Run workflow**

---

## 常见问题

**Q：我电脑很卡，能行吗？**  
A：能。重活都在 GitHub / Streamlit 云上。

**Q：数据存在哪？**  
A：推荐摘要 nightly 存在仓库 `cloud_state/`；你的自选/笔记在 Streamlit 云端实例（重启可能清空，重要请下载 md）。

**Q：还要装 Python 吗？**  
A：不用。除非你想改代码。

**Q：一直免费吗？**  
A：Streamlit 免费档 + GitHub 免费 Actions 额度 + 公开行情源，个人够用。

---

*非投资建议 · 见 [PRIVATE_GARDEN.md](PRIVATE_GARDEN.md)*
