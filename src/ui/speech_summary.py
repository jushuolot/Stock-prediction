"""简报摘要浏览器朗读（P7，Web Speech API）。"""

from __future__ import annotations

import html
import json

import streamlit.components.v1 as components


def render_speech_button(*, text: str, label: str = "🔊 朗读摘要", key: str = "speech") -> None:
    content = (text or "").strip()
    if not content:
        return
    safe = json.dumps(content, ensure_ascii=False)
    btn_id = html.escape(key)
    components.html(
        f"""
<!DOCTYPE html>
<html><head><meta charset="utf-8"/>
<style>
  body {{ margin: 0; font-family: sans-serif; background: transparent; }}
  button {{
    width: 100%; padding: 0.55rem 1rem; font-size: 14px; cursor: pointer;
    background: #262730; color: #fafafa; border: 1px solid #464855; border-radius: 6px;
  }}
  button:hover {{ background: #31333f; }}
  .hint {{ font-size: 11px; color: #9ca3af; margin-top: 6px; }}
</style>
</head>
<body>
  <button id="{btn_id}">{html.escape(label)}</button>
  <div class="hint">使用浏览器语音（zh-CN），需允许页面发声。</div>
  <script>
    const text = {safe};
    document.getElementById("{btn_id}").onclick = function() {{
      if (!window.speechSynthesis) {{
        alert("当前浏览器不支持语音朗读");
        return;
      }}
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = "zh-CN";
      u.rate = 1.0;
      window.speechSynthesis.speak(u);
    }};
  </script>
</body></html>
""",
        height=72,
    )
