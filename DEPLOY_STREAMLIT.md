# 股票助手 · Streamlit Cloud 公网部署（给朋友用）

让朋友**只打开浏览器**即可使用，无需安装 Python。

---

## 1. 登录并创建 App

1. 打开 https://share.streamlit.io ，用 **GitHub** 登录  
2. 点 **Create app** / **New app**  
3. 填写：

| 项 | 值 |
|----|-----|
| Repository | `jushuolot/jinshouzhi` |
| Branch | `main` |
| Main file path | `stock-assistant/app.py` |
| Python version | **3.10** 或 **3.11**（Advanced settings） |

> 依赖文件自动使用同目录下的 `stock-assistant/requirements.txt`。

---

## 2. 设置 Secrets（必填 + 可选）

在 **Secrets** 中粘贴（密码请自行修改）：

```toml
STOCK_ASSISTANT_PASSWORD = "给同事用的强密码"

# 可选：填好后应用内侧边栏可一键复制分享文案
STOCK_APP_PUBLIC_URL = "https://你的应用名.streamlit.app"
```

`STOCK_APP_PUBLIC_URL` 部署成功后在 App 页面顶部复制，填回 Secrets 并 **Save** → **Reboot app**。

---

## 3. 部署前自检（可选 · 低配置电脑可跳过）

> **零本地方案：** 直接 Deploy，改由 [GitHub Actions](https://github.com/jushuolot/jinshouzhi/actions) 跑测试、每晚 `garden-daily-cloud` 扫盘。详见 [docs/CLOUD_ONLY.md](docs/CLOUD_ONLY.md)。

若仍想在本地验证（需要 Python 环境）：

```bash
source .venv/bin/activate
pip install -r requirements.txt
python3 scripts/cloud_preflight.py
python3 -m unittest discover -s tests -q
```

通过后会显示：`[cloud_preflight] 通过 ✓`

macOS 双击 `启动网页.command` 也会在启动前自动跑自检。

---

## 4. 部署

1. 点 **Deploy**，等待 2～5 分钟，状态变为 **Running**  
2. 复制 `https://xxx.streamlit.app`  
3. 若配置了 `STOCK_APP_PUBLIC_URL`，登录后在左侧 **「📤 分享给同事」** 复制或下载说明

### 发给同事的文案模板

```
Stock Assistant · 股票助手（内部分享）

🔗 打开链接：https://xxx.streamlit.app
🔐 访问密码：（请单独私发）

📌 怎么用
1. 浏览器打开链接，输入密码登录
2. 「② 搜索添加」找股票 → 加入自选股
3. 「① 分析工作台」→ 点 一键分析 → 下载 .md 简报

⚠️ 公开行情数据，非投资建议。
```

---

## 5. 每次进化后更新云端

```bash
git add … && git commit -m "…" && git push origin main
```

然后在 Streamlit Cloud：**Manage app** → **Reboot app**（拉最新代码并重装依赖）。

GitHub Actions 会在 push 到 `stock-assistant/` 时自动跑 `cloud_preflight` + 单元测试（见 `.github/workflows/stock-assistant.yml`）。

---

## 6. 常见问题

| 现象 | 处理 |
|------|------|
| **Error installing requirements** | Reboot app；Python 选 3.10/3.11；确认路径 `stock-assistant/app.py` |
| **访问验证 / 尚未配置密码** | Secrets 添加 `STOCK_ASSISTANT_PASSWORD` 后 Save → Reboot |
| **numpy / pandas 崩溃** | 勿升级 numpy≥2；`requirements.txt` 已限制 `numpy<2` |
| **港美股无数据** | 云端用 `yfinance 0.2.x`；稍后重试 |
| **分享文案为空** | Secrets 配置 `STOCK_APP_PUBLIC_URL` 为你的 `.streamlit.app` 链接 |

当前依赖已去掉 `curl_cffi`（云端常编译失败），港股/美股走 `yfinance 0.2.x`。

---

## 7. 相关文档

- 操作步骤：[docs/USER_GUIDE.md §5](docs/USER_GUIDE.md#5-部署到-streamlit-cloud给同事公网访问)  
- 产品说明：[docs/PRODUCT.md](docs/PRODUCT.md)  
- 进化路线：[EVOLUTION.md](EVOLUTION.md)
