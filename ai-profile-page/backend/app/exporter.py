from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any


TEMPLATE_NAMES = {
    "ats": "ATS 一页纸",
    "voice-ai": "AI / 语音方向",
    "backend": "后端 / 系统方向",
}


def local_match_resume(profile: dict[str, Any], jd: str, direction: str) -> str:
    meta = profile["meta"]
    highlights = profile["highlights"][:5]
    experiences = profile["experience"]
    projects = profile["projects"]

    jd_keywords = extract_keywords(jd)
    intro = (
        f"{meta.get('name', '候选人')}，{meta.get('title', '')}，重点匹配 {direction}。"
        "具备语音智能、AI Agent、Linux 后端、分布式系统与工程交付经验。"
    )
    if jd_keywords:
        intro += f" 针对 JD 重点关注：{'、'.join(jd_keywords[:8])}。"

    lines = [
        f"# {meta.get('name', '个人简历')}",
        "",
        f"{meta.get('title', '')} | {meta.get('tagline', '')}",
        f"电话：{meta.get('phone', '')} | 邮箱：{meta.get('email', '')} | {meta.get('education', '')}",
        "",
        "## 匹配摘要",
        intro,
        "",
        "## 核心能力",
    ]
    lines.extend(f"- {item['title']}：{item['body']}" if item["body"] else f"- {item['title']}" for item in highlights)

    lines.append("")
    lines.append("## 工作经历")
    for item in experiences:
        lines.append(f"### {item['title']}")
        lines.extend(line for line in item["body"].splitlines() if line.strip())
        lines.append("")

    lines.append("## 代表项目")
    for item in projects[:3]:
        lines.append(f"### {item['title']}")
        lines.extend(line for line in item["body"].splitlines() if line.strip())
        lines.append("")

    return "\n".join(lines).strip()


def extract_keywords(text: str) -> list[str]:
    if not text:
        return []
    candidates = re.findall(r"[A-Za-z][A-Za-z0-9+#./-]{1,}|[\u4e00-\u9fff]{2,8}", text)
    stopwords = {"负责", "熟悉", "具备", "相关", "优先", "经验", "能力", "开发", "岗位", "工作"}
    seen: set[str] = set()
    result = []
    for item in candidates:
        normalized = item.strip()
        if normalized.lower() in seen or normalized in stopwords:
            continue
        seen.add(normalized.lower())
        result.append(normalized)
    return result[:16]


def markdown_to_resume_html(markdown_text: str, template: str) -> str:
    body = []
    for raw in markdown_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            body.append(f"<h1>{html.escape(line[2:])}</h1>")
        elif line.startswith("## "):
            body.append(f"<h2>{html.escape(line[3:])}</h2>")
        elif line.startswith("### "):
            body.append(f"<h3>{html.escape(line[4:])}</h3>")
        elif line.startswith("- "):
            body.append(f"<p class='bullet'>• {html.escape(line[2:])}</p>")
        else:
            body.append(f"<p>{html.escape(line)}</p>")

    template_name = TEMPLATE_NAMES.get(template, TEMPLATE_NAMES["ats"])
    accent = {"ats": "#174ea6", "voice-ai": "#0f766e", "backend": "#4b5563"}.get(template, "#174ea6")
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{html.escape(template_name)} - 王涛</title>
  <style>
    @page {{ size: A4; margin: 14mm; }}
    body {{ margin: 0; color: #17202a; font-family: "Microsoft YaHei", Arial, sans-serif; line-height: 1.58; }}
    .sheet {{ max-width: 820px; margin: 0 auto; padding: 30px 36px; }}
    h1 {{ font-size: 34px; margin: 0 0 6px; }}
    h2 {{ color: {accent}; font-size: 18px; border-bottom: 1px solid #d8dee6; padding-bottom: 4px; margin: 22px 0 8px; }}
    h3 {{ font-size: 16px; margin: 14px 0 4px; }}
    p {{ margin: 4px 0; font-size: 14px; }}
    .bullet {{ padding-left: 1em; text-indent: -1em; }}
    .stamp {{ color: #6b7280; font-size: 12px; margin-top: 24px; }}
  </style>
</head>
<body>
  <main class="sheet">
    {''.join(body)}
    <p class="stamp">Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · {html.escape(template_name)}</p>
  </main>
</body>
</html>"""

