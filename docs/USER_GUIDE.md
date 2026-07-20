# Stock Assistant · 使用手册

本手册面向**第一次使用**的同学，按步骤说明：如何在电脑上打开应用、登录、管理自选股、生成简报，以及如何部署到公网给同事用。

> 产品背景与功能一览见 [PRODUCT.md](./PRODUCT.md)。

---

## 1. 本地启动（在你自己的电脑上）

### 1.1 准备环境

1. 确认已安装 **Python 3.10 或 3.11**（推荐；3.8 较旧可能遇到依赖问题）。  
   - 终端输入 `python3 --version` 可查看版本。  
2. 打开终端（macOS 可用「终端」App；Windows 可用 PowerShell）。  
3. 进入项目目录：

```bash
cd stock-assistant
```

（若从 GitHub 克隆整个仓库，路径可能是 `jinshouzhi/stock-assistant`。）

### 1.2 创建虚拟环境并安装依赖

4. 创建并激活虚拟环境（只需做一次；以后启动可跳过创建步骤）：

```bash
python3 -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
```

5. 安装依赖：

```bash
pip install -r requirements.txt
```

### 1.3 配置访问密码

6. 复制密码模板并修改：

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

7. 用文本编辑器打开 `.streamlit/secrets.toml`，把 `STOCK_ASSISTANT_PASSWORD` 改成**只有你知道的强密码**，保存。  
   - 此文件**不要**提交到 Git（已在 `.gitignore` 中）。

**另一种方式**（不写文件）：在启动前于终端执行：

```bash
export STOCK_ASSISTANT_PASSWORD='你的强密码'
```

### 1.4 启动网页

8. 在 `stock-assistant` 目录、且虚拟环境已激活时运行：

```bash
streamlit run app.py
```

9. 终端会显示本地地址，一般为 **http://localhost:8501** 。用浏览器打开即可。

**macOS 快捷方式**：双击项目里的 `启动网页.command`，脚本会自动创建虚拟环境、安装依赖并启动（首次可能稍慢）。

---

## 2. 登录

10. 浏览器打开应用后，若尚未登录，会看到 **「访问验证」** 页面。  
11. 在 **访问密码** 输入框填入你在 `secrets.toml` 或环境变量里设置的密码。  
12. 点击 **登录**。  
    - 密码正确 → 进入主界面 **「Stock Assistant · 快速分析」**。  
    - 密码错误 → 页面提示「密码错误」，请检查后重试。  
13. 若页面提示「尚未配置访问密码」，说明第 1.3 步未完成，请先配置再启动。

> **说明**：这是简单的共享密码，不是多用户账号系统；知道密码的人都能进入。

---

## 3. 管理自选股

自选股是你重点关注的股票列表，在 **① 分析工作台** 里使用。

### 3.1 添加自选股

**方式一：搜索添加（推荐）**

14. 点击顶部标签 **「② 搜索添加」**。  
15. 在 **关键词** 框输入，例如：`茅台`、`300755`、`0700.HK`、`AAPL`、`synnex`。  
16. 点击 **全球搜索**，等待结果（同时查 A 股东财与 Yahoo）。  
17. 在 **选择证券** 下拉框里选中目标。  
18. 点击 **加入自选股**，看到「已加入自选股」即可。

**方式二：从榜单添加**

19. 在 **「③ 板块行情」** 或 **「④ 全球股市」** 浏览榜单。  
20. 对感兴趣的股票点击 **加入自选股**。

### 3.2 查看与删除

21. 打开 **「① 分析工作台」**，顶部表格会列出当前自选股（名称、代码、货币、市场等）。  
22. 在 **选择标的** 下拉框选一只，下方展开 K 线、财务、板块等分析。  
23. 若要删除：在 **删除哪些（按代码）** 多选框勾选代码 → 点 **删除所选**。

> 自选股会保存在本机 `data/` 目录；关闭浏览器后再次打开，一般会恢复（见 **⑦ 历史记录**）。

---

## 4. 生成可读简报

简报是一份 **Markdown（.md）** 文档，汇总当前标的的关键信息，适合复制到飞书/微信或发给同事。

24. 在 **「① 分析工作台」** 选好自选股（第 3 步）。  
25. 根据需要查看 **K 线**、**财务对比**、**所属板块** 等（可选，有助于简报内容更完整）。  
26. 找到 **「生成可读简报」** 按钮并点击。  
27. 等待提示「可读简报已生成」；下方 **「📄 可读分析简报」** 区域会展开预览。  
28. 你可以：  
    - 直接复制预览区文字；或  
    - 点击 **「下载简报 (.md)」** 保存到电脑。  
29. 文件名类似 `贵州茅台_简报.md`，可用任意 Markdown 或文本编辑器打开。

**相关功能（可选）**

- **行动路线**：在工作台内可生成异动解读报告；完整版页面在 **「⑥ 行动路线」**。  
- **历史记录**：在 **「⑦ 历史记录」** 可查看以往查询日志。

---

## 5. 部署到 Streamlit Cloud（给同事公网访问）

让同事**只打开浏览器**就能用，无需安装 Python。详细说明亦见 [DEPLOY_STREAMLIT.md](../DEPLOY_STREAMLIT.md)。

### 5.1 前提

30. 本项目的 `stock-assistant/` 目录已推送到 GitHub 仓库（例如 `jushuolot/jinshouzhi` 的 `main` 分支）。  
31. 你有一个 GitHub 账号，并愿意用 Streamlit 官方免费托管（内测够用）。

### 5.2 创建应用

32. 打开 https://share.streamlit.io ，用 **GitHub** 登录。  
33. 点击 **Create app** / **New app**。  
34. 填写：  
    - **Repository**：选择包含本项目的仓库  
    - **Branch**：`main`  
    - **Main file path**：`stock-assistant/app.py`  
35. 展开 **Advanced settings**（如有），将 **Python version** 设为 **3.10** 或 **3.11**。

### 5.3 设置 Secrets（云端密码）

36. 在 **Secrets** 文本框粘贴（请修改引号内密码）：

```toml
STOCK_ASSISTANT_PASSWORD = "给同事用的强密码"

# 可选：部署成功后填公网链接，应用内可生成分享文案
STOCK_APP_PUBLIC_URL = "https://xxxx.streamlit.app"
```

37. 保存 Secrets 配置。

### 5.4 部署与分享

38. 点击 **Deploy**，等待约 2～5 分钟，状态变为 **Running**。  
39. 复制页面上的 **`https://xxxx.streamlit.app`** 链接。  
40. 把 **链接 + 密码** 发给同事；也可在应用登录后，左侧 **「📤 分享给同事」** 复制自动生成的说明（需先在 Secrets 配置 `STOCK_APP_PUBLIC_URL`）。

### 5.5 更新代码后

41. 本地修改并 `git push` 到 GitHub 后，在 Streamlit Cloud 打开 **Manage app** → **Reboot app**，即可拉取最新代码。

### 5.6 常见问题

| 现象 | 处理 |
|------|------|
| Error installing requirements | Manage app → Reboot；确认主文件为 `stock-assistant/app.py`；Python 选 3.10/3.11；本地跑 `python3 scripts/cloud_preflight.py` |
| 尚未配置访问密码 | Secrets 添加 `STOCK_ASSISTANT_PASSWORD` 后 Save → Reboot |
| 港美股数据异常 | 云端使用 `yfinance`，与本地一致；稍后重试 |
| 同事打不开 | 确认链接、密码正确；检查 Cloud 应用是否为 Running |

---

## 6. 推荐阅读顺序

| 顺序 | 文档 | 适合 |
|------|------|------|
| 1 | 本文 USER_GUIDE | 第一次上手操作 |
| 2 | [PRODUCT.md](./PRODUCT.md) | 了解能做什么、数据从哪来 |
| 3 | [EVOLUTION.md](../EVOLUTION.md) | 关心后续功能规划 |
| 4 | [DEPLOY_STREAMLIT.md](../DEPLOY_STREAMLIT.md) | 只关心云端部署细节 |

---

## 7. 本地快速自检清单

部署或改版后，可在本地逐项确认：

- [ ] 能登录  
- [ ] 全球搜索 → 加入自选股  
- [ ] 分析工作台 → 生成可读简报 → 下载 `.md`  
- [ ] 板块 / 全球榜单能刷新  

```bash
cd stock-assistant
source .venv/bin/activate
streamlit run app.py
```

如有问题，可先查看 [README.md](../README.md) 中的配置说明与「勿提交」列表。
