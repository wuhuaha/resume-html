from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Section:
    title: str
    level: int
    body: str


def read_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_markdown(path: Path, markdown_text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown_text, encoding="utf-8", newline="\n")


def parse_frontmatter(markdown_text: str) -> tuple[dict[str, str], str]:
    if not markdown_text.startswith("---"):
        return {}, markdown_text

    end = markdown_text.find("\n---", 3)
    if end == -1:
        return {}, markdown_text

    raw = markdown_text[3:end].strip()
    body = markdown_text[end + 4 :].lstrip()
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta, body


def parse_sections(body: str) -> list[Section]:
    matches = list(re.finditer(r"^(#{1,3})\s+(.+)$", body, flags=re.MULTILINE))
    sections: list[Section] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections.append(
            Section(
                title=match.group(2).strip(),
                level=len(match.group(1)),
                body=body[start:end].strip(),
            )
        )
    return sections


def strip_markdown(markdown_text: str) -> str:
    text = re.sub(r"^---.*?---", "", markdown_text, flags=re.DOTALL)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    text = re.sub(r"^#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_`>\[\]()]|!\[[^\]]*]\([^)]*\)", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def section_preview(section: Section) -> str:
    lines = [line.strip(" -") for line in section.body.splitlines() if line.strip()]
    return " ".join(lines[:3])[:220]


def load_profile(path: Path) -> dict[str, Any]:
    raw = read_markdown(path)
    return parse_profile_markdown(raw)


def parse_profile_markdown(markdown_text: str) -> dict[str, Any]:
    raw = markdown_text
    meta, body = parse_frontmatter(raw)
    meta = normalize_profile_meta(meta, body)
    sections = parse_sections(body)

    grouped: dict[str, list[dict[str, str]]] = {
        "highlights": [],
        "experience": [],
        "projects": [],
        "awards": [],
    }

    current_group = ""
    for section in sections:
        if section.level == 2:
            current_group = section.title
        if section.level == 3 and current_group == "工作经历":
            grouped["experience"].append({"title": section.title, "body": section.body})
        elif section.level == 3 and current_group == "项目详情":
            grouped["projects"].append({"title": section.title, "body": section.body})
        elif section.level == 2 and section.title == "核心能力":
            grouped["highlights"] = bullets_from_markdown(section.body)
        elif section.level == 2 and section.title in {"奖项荣誉", "技能证书"}:
            grouped["awards"].extend(bullets_from_markdown(section.body))

    return {
        "meta": meta,
        "rawMarkdown": raw,
        "plainText": strip_markdown(raw),
        "sections": [
            {
                "title": section.title,
                "level": section.level,
                "body": section.body,
                "preview": section_preview(section),
            }
            for section in sections
        ],
        **grouped,
    }


def normalize_profile_meta(meta: dict[str, str], body: str) -> dict[str, str]:
    normalized = {str(key).strip(): str(value).strip() for key, value in meta.items() if str(value).strip()}
    aliases = {
        "birth": ("birth", "birthday", "birthDate", "dateOfBirth", "出生", "出生日期", "生日"),
        "phone": ("phone", "mobile", "tel", "telephone", "电话", "手机号", "手机"),
        "email": ("email", "mail", "邮箱"),
        "location": ("location", "city", "address", "所在地", "城市", "地址"),
        "education": ("education", "degree", "学历", "教育"),
    }
    for canonical, keys in aliases.items():
        value = first_meta_value(normalized, keys)
        if value:
            normalized[canonical] = value

    if not normalized.get("birth"):
        extracted_birth = extract_labeled_value(body, ("出生日期", "出生", "生日"))
        if extracted_birth:
            normalized["birth"] = extracted_birth
    return normalized


def first_meta_value(meta: dict[str, str], keys: tuple[str, ...]) -> str:
    lower_map = {key.lower(): value for key, value in meta.items()}
    for key in keys:
        value = meta.get(key) or lower_map.get(key.lower())
        if value:
            return value.strip()
    return ""


def extract_labeled_value(text: str, labels: tuple[str, ...]) -> str:
    for label in labels:
        pattern = rf"(?:^|\n)\s*(?:[-*]\s*)?{re.escape(label)}\s*[:：]\s*([^\n|，,；;]+)"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ""


def bullets_from_markdown(markdown_text: str) -> list[dict[str, str]]:
    bullets = []
    for line in markdown_text.splitlines():
        clean = line.strip()
        if clean.startswith("- "):
            text = clean[2:].strip()
            if "：" in text:
                title, body = text.split("：", 1)
                bullets.append({"title": title.strip(), "body": body.strip()})
            else:
                bullets.append({"title": text, "body": ""})
    return bullets


def knowledge_context(profile: dict[str, Any], max_chars: int = 12000) -> str:
    text = profile["plainText"]
    return text[:max_chars]
