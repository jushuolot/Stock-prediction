"""生成发给同事的公网访问说明（P4）。"""

from __future__ import annotations

DEFAULT_SHARE_BODY = """Stock Assistant · 股票助手（内部分享）

🔗 打开链接：{app_url}
🔐 访问密码：{password_line}

📌 怎么用
1. 浏览器打开上面链接，输入密码登录
2. 「② 搜索添加」找股票 → 加入自选股
3. 「① 分析工作台」→ 点 **一键分析** → 下载 `.md` 简报

⚠️ 数据来自公开行情/新闻，规则整理，非投资建议。密码请私发，勿贴在公开群。
"""


def build_share_message(*, app_url: str, password: str = "", include_password: bool = False) -> str:
    url = (app_url or "").strip()
    if not url:
        raise ValueError("app_url 不能为空")
    if include_password and password.strip():
        password_line = password.strip()
    else:
        password_line = "（请单独私发，勿写在公开群）"
    return DEFAULT_SHARE_BODY.format(app_url=url, password_line=password_line)
