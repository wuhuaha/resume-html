from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any

from .config import settings


SECTION_TITLES = {
    "summary": "匹配摘要",
    "skills": "核心能力",
    "experience": "工作经历",
    "projects": "代表项目",
    "awards": "奖项荣誉",
}


def local_match_resume(profile: dict[str, Any], jd: str, direction: str, mode: dict[str, Any] | None = None) -> str:
    mode = mode or {}
    if mode.get("targetPages") == 1 or mode.get("key") in {"one-page", "two-page"}:
        return local_ats_resume(profile, jd, direction, mode)
    return local_full_resume(profile, jd, direction, mode)


def local_full_resume(profile: dict[str, Any], jd: str, direction: str, mode: dict[str, Any]) -> str:
    meta = profile["meta"]
    highlights = profile["highlights"][: mode_count(mode, "skillCount", 8)]
    experiences = profile["experience"][: mode_count(mode, "experienceCount", len(profile["experience"]))]
    projects = profile["projects"][: mode_count(mode, "projectCount", len(profile["projects"]))]
    jd_keywords = extract_keywords(jd)

    intro = (
        f"{meta.get('name', '候选人')}，{meta.get('title', '')}，重点匹配 {direction}。"
        f"{meta.get('tagline', '')}。"
    )
    if jd_keywords:
        intro += f" 针对 JD 重点关注：{'、'.join(jd_keywords[:8])}。"

    lines = resume_header_lines(meta, mode)
    lines.extend(["", "## 匹配摘要", intro, "", "## 核心能力"])
    lines.extend(format_skill(item, 120) for item in highlights)

    lines.extend(["", "## 工作经历"])
    for item in experiences:
        lines.append(f"### {item['title']}")
        lines.extend(limit_lines(item["body"].splitlines(), mode_count(mode, "experienceBullets", 8)))
        lines.append("")

    lines.append("## 代表项目")
    for item in projects:
        lines.append(f"### {item['title']}")
        lines.extend(limit_lines(item["body"].splitlines(), mode_count(mode, "projectBullets", 6)))
        lines.append("")

    append_awards(lines, profile, mode)
    return "\n".join(lines).strip()


def local_ats_resume(profile: dict[str, Any], jd: str, direction: str, mode: dict[str, Any]) -> str:
    meta = profile["meta"]
    jd_keywords = extract_keywords(jd)
    highlights = rank_items(profile["highlights"], jd_keywords)[: mode_count(mode, "skillCount", 5)]
    experiences = profile["experience"][: mode_count(mode, "experienceCount", 3)]
    projects = rank_items(profile["projects"], jd_keywords)[: mode_count(mode, "projectCount", 2)]

    intro = (
        f"{meta.get('title', '')}，匹配 {direction}。"
        "主线覆盖语音 AI、Agent 编排、ASR/TTS/KWS、Linux 后端与分布式系统。"
    )
    if jd_keywords:
        intro += f" JD 关键词：{'、'.join(jd_keywords[:6])}。"

    lines = resume_header_lines(meta, mode)
    lines.extend(
        [
            "",
            "## 匹配摘要",
            truncate_sentence(intro, 150 if mode_count(mode, "summaryLines", 2) <= 2 else 220),
            "",
            "## 核心能力",
        ]
    )
    lines.extend(format_skill(item, 88) for item in highlights)

    lines.extend(["", "## 工作经历"])
    for item in experiences:
        lines.append(f"### {item['title']}")
        lines.extend(rank_lines(item["body"].splitlines(), jd_keywords, mode_count(mode, "experienceBullets", 3)))
        lines.append("")

    if projects:
        lines.append("## 代表项目")
        for item in projects:
            lines.append(f"### {item['title']}")
            lines.extend(rank_lines(item["body"].splitlines(), jd_keywords, mode_count(mode, "projectBullets", 2)))
            lines.append("")

    append_awards(lines, profile, mode)
    return "\n".join(lines).strip()


def resume_header_lines(meta: dict[str, Any], mode: dict[str, Any]) -> list[str]:
    lines = [
        f"# {meta.get('name', '个人简历')}",
        "",
        f"{meta.get('title', '')} | {meta.get('tagline', '')}".strip(" |"),
    ]
    contact_parts = [
        labeled("电话", meta.get("phone", "")),
        labeled("邮箱", meta.get("email", "")),
        meta.get("location", ""),
        meta.get("education", ""),
    ]
    if mode.get("includeBirth", True):
        contact_parts.append(labeled("出生", meta.get("birth", "") or meta.get("birthday", "")))
    lines.append(" | ".join(part for part in contact_parts if part))
    return lines


def append_awards(lines: list[str], profile: dict[str, Any], mode: dict[str, Any]) -> None:
    awards = profile.get("awards", [])
    if not mode.get("includeAwards") or not awards:
        return
    lines.append("## 奖项荣誉")
    lines.extend(f"- {item['title']}：{item['body']}" if item.get("body") else f"- {item['title']}" for item in awards[:4])


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


def compact_resume_markdown(markdown_text: str, mode: dict[str, Any]) -> str:
    if not mode:
        return markdown_text

    limits = {
        "核心能力": mode_count(mode, "skillCount", 5),
        "工作经历": mode_count(mode, "experienceBullets", 3),
        "代表项目": mode_count(mode, "projectBullets", 2),
        "奖项荣誉": 4,
    }
    project_limit = mode_count(mode, "projectCount", 2)
    experience_limit = mode_count(mode, "experienceCount", 3)
    output: list[str] = []
    section = ""
    subsection_counts = {"工作经历": 0, "代表项目": 0}
    bullets_in_block = 0
    bullets_in_section = 0
    skip_block = False

    for raw in markdown_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            output.append(line)
            continue
        if line.startswith("## "):
            section = line[3:].strip()
            bullets_in_section = 0
            bullets_in_block = 0
            skip_block = False
            if section == "奖项荣誉" and not mode.get("includeAwards"):
                skip_block = True
                continue
            output.append(line)
            continue
        if line.startswith("### "):
            bullets_in_block = 0
            skip_block = False
            if section == "工作经历":
                subsection_counts[section] += 1
                skip_block = subsection_counts[section] > experience_limit
            elif section == "代表项目":
                subsection_counts[section] += 1
                skip_block = subsection_counts[section] > project_limit
            if not skip_block:
                output.append(line)
            continue
        if skip_block:
            continue
        if line.startswith("- "):
            if section == "核心能力":
                bullets_in_section += 1
                if bullets_in_section > limits["核心能力"]:
                    continue
            elif section in {"工作经历", "代表项目"}:
                bullets_in_block += 1
                if bullets_in_block > limits[section]:
                    continue
            output.append(truncate_bullet(line, 112 if mode.get("targetPages") == 1 else 150))
            continue
        output.append(truncate_sentence(line, 160 if mode.get("targetPages") == 1 else 220))

    return "\n".join(output).strip()


def ensure_resume_header_metadata(markdown_text: str, profile: dict[str, Any], mode: dict[str, Any]) -> str:
    meta = profile.get("meta", {})
    lines = [line.rstrip() for line in markdown_text.splitlines()]
    if not lines:
        return "\n".join(resume_header_lines(meta, mode)).strip()

    if not any(line.startswith("# ") for line in lines[:4]):
        lines.insert(0, f"# {meta.get('name', '个人简历')}")

    required = [
        labeled("电话", meta.get("phone", "")),
        labeled("邮箱", meta.get("email", "")),
        str(meta.get("location", "") or "").strip(),
        str(meta.get("education", "") or "").strip(),
    ]
    if mode.get("includeBirth", True):
        required.append(labeled("出生", meta.get("birth", "") or meta.get("birthday", "")))
    required = [item for item in required if item]

    contact_index = next((index for index, line in enumerate(lines[:8]) if "电话" in line or "邮箱" in line), -1)
    contact_line = " | ".join(required)
    if contact_index >= 0:
        existing_parts = [part.strip() for part in lines[contact_index].split("|") if part.strip()]
        merged = existing_parts[:]
        for item in required:
            label = item.split("：", 1)[0] if "：" in item else item
            if not any(part.startswith(f"{label}：") or part == item for part in merged):
                merged.append(item)
        lines[contact_index] = " | ".join(merged)
    elif required:
        insert_at = 3 if len(lines) >= 3 else len(lines)
        lines.insert(insert_at, contact_line)
    return "\n".join(lines).strip()


def markdown_to_resume_html(
    markdown_text: str,
    template: dict[str, Any],
    mode: dict[str, Any] | None = None,
    avatar_data_url: str = "",
    branding: dict[str, Any] | None = None,
) -> str:
    mode = mode or {}
    branding = branding or {}
    doc = parse_resume_markdown(markdown_text)
    template_key = template.get("key", "ats-classic")
    layout = template.get("layout", "single")
    accent = sanitize_css_color(template.get("accent", "#174ea6"))
    page_margin = mode.get("pageMarginMm", 14)
    font_size = mode.get("fontSize", 14)
    line_height = mode.get("lineHeight", 1.58)
    section_spacing = mode.get("sectionSpacing", 18)
    show_avatar = bool(mode.get("includeAvatar") and template.get("showAvatar") and avatar_data_url)
    avatar_placement = template.get("avatarPlacement") or ("sidebar-top" if layout == "sidebar" else "header-right")
    template_name = template.get("label", "简历模板")
    title = f"{template_name} - {doc['name']}"

    body_html = render_resume_body(doc, layout, show_avatar, avatar_data_url, mode, avatar_placement)
    footer_html = render_branding_footer(branding, template) if branding.get("enabled", True) else ""

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>
    @page {{ size: A4; margin: {page_margin}mm; }}
    :root {{ --accent: {accent}; --ink: #17202a; --muted: #64748b; --line: #d8dee6; --soft: #f4f7fb; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; color: var(--ink); background: #eef2f6; font-family: {safe_font_family(template.get("fontFamily"))}; line-height: {line_height}; }}
    .sheet {{ width: min(920px, 100%); min-height: 100vh; margin: 0 auto; padding: {0 if mode.get("targetPages") == 1 else 18}px; background: #fff; }}
    .resume {{ display: block; }}
    .resume.sidebar {{ display: grid; grid-template-columns: 238px minmax(0, 1fr); gap: 26px; align-items: start; }}
    .resume.timeline .section.experience h3 {{ position: relative; padding-left: 18px; }}
    .resume.timeline .section.experience h3::before {{ content: ""; position: absolute; left: 0; top: 0.72em; width: 7px; height: 7px; border-radius: 999px; background: var(--accent); }}
    .header {{ padding-bottom: 12px; border-bottom: 2px solid var(--accent); }}
    .header.band {{ margin: -2px -2px 16px; padding: 22px 24px; color: #fff; background: linear-gradient(135deg, var(--accent), #111827); border: 0; }}
    .header.profile {{ display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 18px; align-items: center; }}
    .header-main {{ min-width: 0; }}
    .avatar {{ width: 78px; height: 96px; object-fit: cover; border-radius: 8px; border: 1px solid rgba(255,255,255,0.7); }}
    .header.profile .avatar {{ justify-self: end; }}
    .header:not(.band) .avatar {{ border-color: var(--line); }}
    h1 {{ margin: 0 0 6px; font-size: {28 if mode.get("targetPages") == 1 else 34}px; line-height: 1.06; letter-spacing: 0; }}
    .headline {{ margin: 0; color: inherit; font-size: {font_size}px; font-weight: 700; }}
    .contact {{ margin-top: 7px; color: var(--muted); font-size: {max(10.5, font_size - 1)}px; }}
    .band .contact {{ color: rgba(255,255,255,0.86); }}
    .sidebar-info {{ padding: 18px; background: var(--soft); border-radius: 8px; }}
    .sidebar-info .avatar {{ width: 108px; height: 108px; margin-bottom: 14px; }}
    .sidebar-info h1 {{ font-size: 25px; }}
    .sidebar-info .contact span {{ display: block; margin-top: 5px; }}
    .content {{ min-width: 0; }}
    .section {{ margin-top: {section_spacing}px; break-inside: avoid; }}
    .section:first-child {{ margin-top: {max(8, section_spacing - 6)}px; }}
    h2 {{ margin: 0 0 7px; padding-bottom: 3px; color: var(--accent); border-bottom: 1px solid var(--line); font-size: {15 if mode.get("targetPages") == 1 else 18}px; line-height: 1.2; }}
    h3 {{ margin: 8px 0 3px; font-size: {13.2 if mode.get("targetPages") == 1 else 16}px; line-height: 1.3; }}
    p {{ margin: {2 if mode.get("targetPages") == 1 else 4}px 0; font-size: {font_size}px; }}
    .bullet {{ padding-left: 1em; text-indent: -1em; }}
    .brief-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 16px; }}
    .compact .section {{ margin-top: {max(6, section_spacing - 4)}px; }}
    .compact p {{ margin: 1px 0; }}
    .stamp {{ margin-top: 14px; padding-top: 8px; border-top: 1px solid var(--line); color: #7b8491; font-size: 10.5px; line-height: 1.45; }}
    .stamp a {{ color: inherit; text-decoration: none; }}
    @media print {{ body {{ background: #fff; }} .sheet {{ padding: 0; }} .section {{ break-inside: avoid; }} }}
  </style>
</head>
<body>
  <main class="sheet template-{html.escape(template_key)}">
    {body_html}
    {footer_html}
  </main>
</body>
</html>"""


def render_resume_body(
    doc: dict[str, Any],
    layout: str,
    show_avatar: bool,
    avatar_data_url: str,
    mode: dict[str, Any],
    avatar_placement: str,
) -> str:
    header_class = "header"
    if layout == "sidebar":
        sidebar = render_sidebar(doc, show_avatar and avatar_placement == "sidebar-top", avatar_data_url)
        content = render_sections(doc, layout, mode)
        header = ""
        if show_avatar and avatar_placement == "header-right":
            header = render_header(doc, "header profile", show_avatar, avatar_data_url)
        return f"<article class='resume sidebar'>{sidebar}<div class='content'>{header}{content}</div></article>"
    if layout == "brief":
        header_class += " band"
    if show_avatar:
        header_class += " profile"

    header = render_header(doc, header_class, show_avatar and avatar_placement == "header-right", avatar_data_url)
    sections = render_sections(doc, layout, mode)
    return f"<article class='resume {html.escape(layout)}'>{header}<div class='content'>{sections}</div></article>"


def render_header(doc: dict[str, Any], class_name: str, show_avatar: bool, avatar_data_url: str) -> str:
    avatar = f"<img class='avatar' src='{html.escape(avatar_data_url)}' alt='简历头像'>" if show_avatar else ""
    inner = (
        f"<div class='header-main'><h1>{html.escape(doc['name'])}</h1>"
        f"<p class='headline'>{html.escape(doc['headline'])}</p>"
        f"<p class='contact'>{html.escape(doc['contact'])}</p></div>{avatar}"
    )
    return f"<header class='{html.escape(class_name)}'>{inner}</header>"


def render_sidebar(doc: dict[str, Any], show_avatar: bool, avatar_data_url: str) -> str:
    avatar = f"<img class='avatar' src='{html.escape(avatar_data_url)}' alt='简历头像'>" if show_avatar else ""
    contact = "".join(f"<span>{html.escape(part.strip())}</span>" for part in doc["contact"].split("|") if part.strip())
    return (
        "<aside class='sidebar-info'>"
        f"{avatar}<h1>{html.escape(doc['name'])}</h1>"
        f"<p class='headline'>{html.escape(doc['headline'])}</p>"
        f"<p class='contact'>{contact}</p>"
        "</aside>"
    )


def render_sections(doc: dict[str, Any], layout: str, mode: dict[str, Any]) -> str:
    sections = []
    for section in doc["sections"]:
        classes = ["section", section["key"]]
        body_class = "brief-grid" if layout == "brief" and section["key"] == "skills" else ""
        body = "".join(render_block(block) for block in section["blocks"])
        sections.append(
            f"<section class='{' '.join(classes)}'><h2>{html.escape(section['title'])}</h2>"
            f"<div class='{body_class}'>{body}</div></section>"
        )
    compact_class = " compact" if layout == "compact" or mode.get("targetPages") == 1 else ""
    return f"<div class='sections{compact_class}'>{''.join(sections)}</div>"


def render_block(block: dict[str, str]) -> str:
    kind = block["kind"]
    text = html.escape(block["text"])
    if kind == "h3":
        return f"<h3>{text}</h3>"
    if kind == "bullet":
        return f"<p class='bullet'>• {text}</p>"
    return f"<p>{text}</p>"


def render_branding_footer(branding: dict[str, Any], template: dict[str, Any]) -> str:
    if not template.get("footerEnabled", True):
        return ""
    github_url = branding.get("githubUrl") or settings.project_github_url
    author = branding.get("author") or "王涛"
    text = branding.get("text") or "本简历由开源项目 Resume HTML 生成"
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        "<footer class='stamp'>"
        f"{html.escape(text)}；开源项目作者：{html.escape(author)}；"
        f"GitHub：<a href='{html.escape(github_url)}'>{html.escape(github_url)}</a>；"
        f"生成时间：{generated_at}。"
        "</footer>"
    )


def parse_resume_markdown(markdown_text: str) -> dict[str, Any]:
    lines = [line.strip() for line in markdown_text.splitlines() if line.strip()]
    name = "个人简历"
    headline = ""
    contact = ""
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for line in lines:
        if line.startswith("# "):
            name = line[2:].strip()
            continue
        if not sections and not current and not headline:
            headline = line
            continue
        if not sections and not current and not contact and ("电话" in line or "邮箱" in line or "|" in line):
            contact = line
            continue
        if line.startswith("## "):
            title = line[3:].strip()
            current = {"title": title, "key": section_key(title), "blocks": []}
            sections.append(current)
            continue
        if current is None:
            if not headline:
                headline = line
            elif not contact:
                contact = line
            continue
        if line.startswith("### "):
            current["blocks"].append({"kind": "h3", "text": line[4:].strip()})
        elif line.startswith("- "):
            current["blocks"].append({"kind": "bullet", "text": line[2:].strip()})
        else:
            current["blocks"].append({"kind": "p", "text": line})

    return {"name": name, "headline": headline, "contact": contact, "sections": sections}


def section_key(title: str) -> str:
    for key, value in SECTION_TITLES.items():
        if title == value:
            return key
    return "custom"


def mode_count(mode: dict[str, Any], field: str, fallback: int) -> int:
    try:
        return int(mode.get(field, fallback))
    except (TypeError, ValueError):
        return fallback


def format_skill(item: dict[str, Any], limit: int) -> str:
    body = str(item.get("body", "")).strip()
    title = str(item.get("title", "")).strip()
    if body:
        return f"- {title}：{truncate_sentence(body, limit)}"
    return f"- {title}"


def limit_lines(lines: list[str], limit: int) -> list[str]:
    return [line for line in lines if line.strip()][:limit]


def rank_items(items: list[dict[str, Any]], keywords: list[str]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda item: score_text(f"{item.get('title', '')} {item.get('body', '')}", keywords), reverse=True)


def rank_lines(lines: list[str], keywords: list[str], limit: int) -> list[str]:
    cleaned = [line.strip() for line in lines if line.strip()]
    return sorted(cleaned, key=lambda line: score_text(line, keywords), reverse=True)[:limit]


def score_text(text: str, keywords: list[str]) -> int:
    lower = text.lower()
    score = 0
    for keyword in keywords:
        if keyword and keyword.lower() in lower:
            score += 3
    for token in ["agent", "语音", "asr", "tts", "kws", "llm", "rag", "分布式", "性能", "成本", "延迟"]:
        if token in lower:
            score += 1
    return score


def truncate_bullet(line: str, limit: int) -> str:
    if not line.startswith("- "):
        return truncate_sentence(line, limit)
    return f"- {truncate_sentence(line[2:], limit)}"


def truncate_sentence(text: str, limit: int) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip("，,；;。 ") + "…"


def labeled(label: str, value: Any) -> str:
    text = str(value or "").strip()
    return f"{label}：{text}" if text else ""


def safe_font_family(value: Any) -> str:
    text = str(value or "Microsoft YaHei, Arial, sans-serif")
    return re.sub(r"[^A-Za-z0-9 ,\"'._-]", "", text)[:160] or "Microsoft YaHei, Arial, sans-serif"


def sanitize_css_color(value: Any) -> str:
    text = str(value or "#174ea6").strip()
    if re.fullmatch(r"#[0-9a-fA-F]{3,8}", text):
        return text
    if re.fullmatch(r"[a-zA-Z]+", text):
        return text
    return "#174ea6"
