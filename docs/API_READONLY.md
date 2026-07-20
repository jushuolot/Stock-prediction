# 只读快照 API（P7）

Stock Assistant 不提供在线写接口；可通过 **snapshot.json** 只读导出当前会话数据。

## 如何导出

1. 登录应用  
2. 左侧边栏 → **📦 只读数据快照** → **下载 snapshot.json**

## Schema

`stock-assistant-readonly-v1`

```json
{
  "schema": "stock-assistant-readonly-v1",
  "generated_at": "2026-06-06 12:00:00",
  "disclaimer": "…",
  "watchlist": [{ "名称": "…", "代码": "…", "类型": "A", "货币": "CNY" }],
  "snapshots": {
    "600519": {
      "code": "600519",
      "pct": 1.2,
      "score": 55.0,
      "one_line": "…",
      "fin_summary": "…"
    }
  },
  "briefs": {
    "600519": "# 股票分析简报 …"
  },
  "counts": { "watchlist": 1, "snapshots": 1, "briefs": 1 },
  "meta": { "auto_refresh_enabled": false, "auto_refresh_minutes": 5 }
}
```

## 脚本读取示例

```python
import json
from pathlib import Path

data = json.loads(Path("snapshot.json").read_text(encoding="utf-8"))
assert data["schema"] == "stock-assistant-readonly-v1"
for item in data["watchlist"]:
    code = item["代码"]
    snap = data["snapshots"].get(code, {})
    print(item["名称"], snap.get("涨跌幅"), snap.get("one_line"))
```

## 说明

- 快照为**导出时刻**的副本，不会自动更新  
- 不含密码与服务器写权限  
- 公网 Streamlit 实例同样可在 UI 内下载
