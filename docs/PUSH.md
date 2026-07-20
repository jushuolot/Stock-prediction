# 推送自选股速览（P8）

## Webhook（飞书 / 钉钉 / Slack 等）

在 `.streamlit/secrets.toml` 或环境变量中配置：

```toml
STOCK_WEBHOOK_URL = "https://your-webhook-endpoint"
```

应用内：**左侧 📣 推送速览** → **立即推送当前速览**

Payload schema: `stock-assistant-webhook-v1`（JSON，含 `digest_markdown` 与 `text` 摘要）

勾选 **自动刷新后推送 Webhook** 可在页面打开且自动刷新摘要时同步推送。

## 邮件（SMTP）

```toml
[smtp]
host = "smtp.example.com"
port = 587
user = "your@email.com"
password = "app-password"
to = "colleague@example.com"
from = "Stock Assistant <your@email.com>"
```

或环境变量：`STOCK_SMTP_HOST`、`STOCK_SMTP_PORT`、`STOCK_SMTP_USER`、`STOCK_SMTP_PASSWORD`、`STOCK_SMTP_TO`

## 多用户数据隔离

同一实例可配置多组密码，各自独立自选股与历史：

```toml
STOCK_ASSISTANT_PASSWORD = "主密码"   # 可选，与下方二选一或并存

[passwords]
alice = "密码A"
bob = "密码B"
```

数据目录：`data/users/alice/user_history.json`（默认用户仍兼容 `data/user_history.json`）

## 定时任务（无需开浏览器）

```bash
cd stock-assistant
export STOCK_WEBHOOK_URL='https://...'
python3 scripts/push_digest_cron.py
```

多用户：`export STOCK_USER='alice'`

cron 示例（工作日 9:00）：

```cron
0 9 * * 1-5 cd /path/to/stock-assistant && .venv/bin/python3 scripts/push_digest_cron.py
```

## 说明

- 推送内容为 **自选股速览 Markdown**，非投资建议  
- Streamlit Cloud 请在 Secrets 中配置上述项后 Reboot  
- Webhook 失败时请检查 URL 与防火墙
