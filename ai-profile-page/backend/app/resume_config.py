from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


DEFAULT_RESUME_EXPORT_CONFIG: dict[str, Any] = {
    "activeMode": "one-page",
    "activeTemplate": "ats-classic",
    "modes": {
        "one-page": {
            "label": "ATS 一页纸",
            "description": "投递筛选优先，强制控制内容预算。",
            "targetPages": 1,
            "summaryLines": 2,
            "skillCount": 5,
            "experienceCount": 3,
            "experienceBullets": 3,
            "projectCount": 2,
            "projectBullets": 2,
            "includeAwards": False,
            "includeCertificates": False,
            "includeBirth": True,
            "includeAvatar": False,
            "fontSize": 12.4,
            "lineHeight": 1.34,
            "pageMarginMm": 10,
            "sectionSpacing": 9,
        },
        "two-page": {
            "label": "ATS 精简两页",
            "description": "保留更多项目细节，适合有明确岗位 JD 的投递。",
            "targetPages": 2,
            "summaryLines": 3,
            "skillCount": 6,
            "experienceCount": 3,
            "experienceBullets": 5,
            "projectCount": 3,
            "projectBullets": 4,
            "includeAwards": True,
            "includeCertificates": False,
            "includeBirth": True,
            "includeAvatar": False,
            "fontSize": 13,
            "lineHeight": 1.42,
            "pageMarginMm": 12,
            "sectionSpacing": 12,
        },
        "complete": {
            "label": "完整匹配版",
            "description": "面试前阅读优先，不强制页数。",
            "targetPages": 0,
            "summaryLines": 4,
            "skillCount": 8,
            "experienceCount": 6,
            "experienceBullets": 8,
            "projectCount": 5,
            "projectBullets": 6,
            "includeAwards": True,
            "includeCertificates": True,
            "includeBirth": True,
            "includeAvatar": True,
            "fontSize": 14,
            "lineHeight": 1.52,
            "pageMarginMm": 14,
            "sectionSpacing": 18,
        },
    },
    "templates": {
        "ats-classic": {
            "label": "ATS 经典单栏",
            "description": "参考 OpenResume/JSON Resume 的 ATS 优先思路，结构朴素、解析稳定，适合投递系统。",
            "inspiration": "OpenResume / JSON Resume",
            "layout": "single",
            "accent": "#174ea6",
            "fontFamily": "Microsoft YaHei, Arial, sans-serif",
            "headerStyle": "plain",
            "showAvatar": False,
            "footerEnabled": True,
            "llmInstruction": "输出 ATS 友好的单栏 Markdown，少用装饰性表达，联系方式和基础信息必须完整。",
        },
        "modern-sidebar": {
            "label": "现代侧栏版",
            "description": "参考 Reactive Resume 的分区配置思路，头像与基础信息放入侧栏，主体突出经历和项目。",
            "inspiration": "Reactive Resume",
            "layout": "sidebar",
            "accent": "#0f766e",
            "fontFamily": "Inter, Microsoft YaHei, Arial, sans-serif",
            "headerStyle": "profile",
            "showAvatar": True,
            "footerEnabled": True,
            "llmInstruction": "输出适合双栏视觉模板的 Markdown，摘要短、经历证据强，避免过长段落。",
        },
        "timeline-evidence": {
            "label": "经历证据时间线",
            "description": "突出时间线、职责边界和量化结果，适合面试前阅读。",
            "inspiration": "RenderCV",
            "layout": "timeline",
            "accent": "#7c3aed",
            "fontFamily": "Microsoft YaHei, Arial, sans-serif",
            "headerStyle": "compact",
            "showAvatar": False,
            "footerEnabled": True,
            "llmInstruction": "按时间线组织经历，每段保留角色、技术栈、量化结果和可验证证据。",
        },
        "technical-brief": {
            "label": "技术档案版",
            "description": "更像技术能力 brief，适合 AI/后端/架构岗位沟通。",
            "inspiration": "JSON Resume themes",
            "layout": "brief",
            "accent": "#334155",
            "fontFamily": "Inter, Microsoft YaHei, Arial, sans-serif",
            "headerStyle": "band",
            "showAvatar": False,
            "footerEnabled": True,
            "llmInstruction": "优先提炼技术栈、系统职责、性能优化和工程交付，不写泛泛软技能。",
        },
        "compact-executive": {
            "label": "紧凑高管摘要",
            "description": "高密度摘要版，适合快速转发或一页纸初筛。",
            "inspiration": "RenderCV compact layout",
            "layout": "compact",
            "accent": "#111827",
            "fontFamily": "Arial, Microsoft YaHei, sans-serif",
            "headerStyle": "plain",
            "showAvatar": False,
            "footerEnabled": True,
            "llmInstruction": "极度精简，所有 bullet 优先使用动词开头和结果导向表达，避免重复。",
        },
    },
    "sectionOrder": ["summary", "skills", "experience", "projects", "awards"],
    "branding": {
        "enabled": True,
        "githubUrl": "https://github.com/wuhuaha/resume-html",
        "author": "王涛",
        "text": "本简历由开源项目 AI Profile Page 生成",
    },
}

LIMITS = {
    "summaryLines": (1, 5),
    "skillCount": (3, 10),
    "experienceCount": (1, 6),
    "experienceBullets": (1, 8),
    "projectCount": (0, 5),
    "projectBullets": (1, 6),
    "fontSize": (10.5, 15),
    "lineHeight": (1.18, 1.7),
    "pageMarginMm": (6, 18),
    "sectionSpacing": (4, 24),
}

TEMPLATE_FIELDS = {
    "label": 80,
    "description": 180,
    "inspiration": 80,
    "layout": 32,
    "accent": 32,
    "fontFamily": 160,
    "headerStyle": 32,
    "llmInstruction": 300,
}


def read_resume_export_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return default_resume_export_config()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default_resume_export_config()
    return normalize_resume_export_config(raw)


def write_resume_export_config(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_resume_export_config(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    return normalized


def default_resume_export_config() -> dict[str, Any]:
    return deepcopy(DEFAULT_RESUME_EXPORT_CONFIG)


def normalize_resume_export_config(raw: Any) -> dict[str, Any]:
    fallback = default_resume_export_config()
    if not isinstance(raw, dict):
        return fallback

    result = fallback
    active_mode = str(raw.get("activeMode") or fallback["activeMode"])
    if active_mode in result["modes"]:
        result["activeMode"] = active_mode

    active_template = str(raw.get("activeTemplate") or fallback["activeTemplate"])
    if active_template in result["templates"]:
        result["activeTemplate"] = active_template

    raw_modes = raw.get("modes")
    if isinstance(raw_modes, dict):
        for key, fallback_mode in result["modes"].items():
            raw_mode = raw_modes.get(key)
            if isinstance(raw_mode, dict):
                result["modes"][key] = normalize_mode(fallback_mode, raw_mode)

    raw_order = raw.get("sectionOrder")
    if isinstance(raw_order, list):
        allowed = {"summary", "skills", "experience", "projects", "awards"}
        ordered = [str(item) for item in raw_order if str(item) in allowed]
        for item in fallback["sectionOrder"]:
            if item not in ordered:
                ordered.append(item)
        result["sectionOrder"] = ordered

    raw_templates = raw.get("templates")
    if isinstance(raw_templates, dict):
        for key, fallback_template in result["templates"].items():
            raw_template = raw_templates.get(key)
            if isinstance(raw_template, dict):
                result["templates"][key] = normalize_template(fallback_template, raw_template)

    raw_branding = raw.get("branding")
    if isinstance(raw_branding, dict):
        result["branding"] = normalize_branding(fallback["branding"], raw_branding)

    return result


def normalize_mode(fallback: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(fallback)
    for field in ["label", "description"]:
        if isinstance(raw.get(field), str) and raw[field].strip():
            result[field] = raw[field].strip()[:80 if field == "label" else 160]

    target_pages = to_int(raw.get("targetPages"), fallback["targetPages"])
    result["targetPages"] = max(0, min(target_pages, 3))

    for field, (minimum, maximum) in LIMITS.items():
        value = raw.get(field, fallback[field])
        if isinstance(minimum, float) or isinstance(maximum, float):
            result[field] = clamp_float(value, fallback[field], minimum, maximum)
        else:
            result[field] = clamp_int(value, fallback[field], minimum, maximum)

    for field in ["includeAwards", "includeCertificates", "includeBirth", "includeAvatar"]:
        result[field] = bool(raw.get(field, fallback[field]))

    return result


def normalize_template(fallback: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(fallback)
    for field, max_length in TEMPLATE_FIELDS.items():
        value = raw.get(field)
        if isinstance(value, str) and value.strip():
            result[field] = value.strip()[:max_length]
    result["showAvatar"] = bool(raw.get("showAvatar", fallback.get("showAvatar", False)))
    result["footerEnabled"] = bool(raw.get("footerEnabled", fallback.get("footerEnabled", True)))
    return result


def normalize_branding(fallback: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(fallback)
    result["enabled"] = bool(raw.get("enabled", fallback["enabled"]))
    for field, max_length in {"githubUrl": 240, "author": 80, "text": 120}.items():
        value = raw.get(field)
        if isinstance(value, str) and value.strip():
            result[field] = value.strip()[:max_length]
    return result


def active_resume_mode(config: dict[str, Any], requested_mode: str | None = None) -> dict[str, Any]:
    normalized = normalize_resume_export_config(config)
    mode_key = requested_mode if requested_mode in normalized["modes"] else normalized["activeMode"]
    mode = deepcopy(normalized["modes"].get(mode_key) or normalized["modes"][normalized["activeMode"]])
    mode["key"] = mode_key
    return mode


def active_resume_template(config: dict[str, Any], requested_template: str | None = None) -> dict[str, Any]:
    normalized = normalize_resume_export_config(config)
    template_key = requested_template if requested_template in normalized["templates"] else normalized["activeTemplate"]
    template = deepcopy(normalized["templates"].get(template_key) or normalized["templates"][normalized["activeTemplate"]])
    template["key"] = template_key
    return template


def to_int(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def clamp_int(value: Any, fallback: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(to_int(value, fallback), maximum))


def clamp_float(value: Any, fallback: float, minimum: float, maximum: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = float(fallback)
    return round(max(minimum, min(number, maximum)), 2)
