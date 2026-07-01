from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any


STYLE_PRESETS: list[dict[str, Any]] = [
    {
        "key": "linear-pro",
        "label": "Linear 专业风",
        "source": "Linear / recruiting console",
        "description": "克制、清晰、信息密度高，适合招聘方快速判断能力证据。",
        "accent": "#126d64",
        "accent2": "#1d4f91",
        "accentSoft": "#e7f3f0",
        "topGlow": "rgba(231, 243, 240, 0.68)",
        "bg": "#f6f7f5",
        "surface": "#ffffff",
        "surfaceSoft": "#f1f4f2",
        "ink": "#141716",
        "muted": "#616966",
        "subtle": "#8d9692",
        "line": "#dce3df",
        "lineStrong": "#c7d0cb",
        "radius": "8px",
        "shadow": "0 16px 44px rgba(31, 40, 36, 0.08)",
        "shadowSoft": "0 10px 28px rgba(31, 40, 36, 0.05)",
        "panelAlpha": "0.88",
        "density": "compact",
        "cardTone": "crisp",
    },
    {
        "key": "mintlify-docs",
        "label": "Mintlify 文档风",
        "source": "Mintlify / technical docs",
        "description": "技术文档感更强，强调结构、可读性和清爽的浅色界面。",
        "accent": "#0f766e",
        "accent2": "#2563eb",
        "accentSoft": "#e6f6f3",
        "topGlow": "rgba(230, 246, 243, 0.76)",
        "bg": "#fbfcfc",
        "surface": "#ffffff",
        "surfaceSoft": "#f3f7f7",
        "ink": "#101828",
        "muted": "#5d6675",
        "subtle": "#98a2b3",
        "line": "#e4e7ec",
        "lineStrong": "#cfd6df",
        "radius": "8px",
        "shadow": "0 18px 48px rgba(16, 24, 40, 0.07)",
        "shadowSoft": "0 8px 24px rgba(16, 24, 40, 0.045)",
        "panelAlpha": "0.9",
        "density": "comfortable",
        "cardTone": "document",
    },
    {
        "key": "notion-editorial",
        "label": "Notion 编辑风",
        "source": "Notion / editorial profile",
        "description": "阅读感更柔和，适合突出履历叙事、项目脉络和长期能力沉淀。",
        "accent": "#7a4f2a",
        "accent2": "#2f6f73",
        "accentSoft": "#f4eee6",
        "topGlow": "rgba(244, 238, 230, 0.72)",
        "bg": "#faf8f4",
        "surface": "#fffdf9",
        "surfaceSoft": "#f3efe7",
        "ink": "#1f1f1d",
        "muted": "#67635d",
        "subtle": "#9a948b",
        "line": "#e5ded2",
        "lineStrong": "#cec4b6",
        "radius": "6px",
        "shadow": "0 14px 38px rgba(63, 51, 38, 0.07)",
        "shadowSoft": "0 8px 20px rgba(63, 51, 38, 0.045)",
        "panelAlpha": "0.86",
        "density": "comfortable",
        "cardTone": "editorial",
    },
    {
        "key": "ibm-enterprise",
        "label": "IBM 企业风",
        "source": "IBM Carbon / enterprise systems",
        "description": "正式、理性、系统工程感强，适合后端、分布式和可靠性方向表达。",
        "accent": "#0f62fe",
        "accent2": "#198038",
        "accentSoft": "#edf5ff",
        "topGlow": "rgba(237, 245, 255, 0.76)",
        "bg": "#f4f4f4",
        "surface": "#ffffff",
        "surfaceSoft": "#f2f4f8",
        "ink": "#161616",
        "muted": "#525252",
        "subtle": "#8d8d8d",
        "line": "#e0e0e0",
        "lineStrong": "#c6c6c6",
        "radius": "2px",
        "shadow": "0 12px 34px rgba(22, 22, 22, 0.075)",
        "shadowSoft": "0 6px 18px rgba(22, 22, 22, 0.045)",
        "panelAlpha": "0.92",
        "density": "compact",
        "cardTone": "enterprise",
    },
]

DEFAULT_STYLE_KEY = STYLE_PRESETS[0]["key"]


def style_preset_keys() -> set[str]:
    return {preset["key"] for preset in STYLE_PRESETS}


def default_style_config() -> dict[str, str]:
    return {"activeKey": DEFAULT_STYLE_KEY}


def get_style_preset(key: str | None) -> dict[str, Any]:
    for preset in STYLE_PRESETS:
        if preset["key"] == key:
            return deepcopy(preset)
    return deepcopy(STYLE_PRESETS[0])


def normalize_style_config(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raw = {}
    active_key = str(raw.get("activeKey") or DEFAULT_STYLE_KEY)
    if active_key not in style_preset_keys():
        active_key = DEFAULT_STYLE_KEY
    return {"activeKey": active_key}


def read_site_style(path: Path) -> dict[str, Any]:
    if not path.exists():
        return normalize_style_config({})
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return normalize_style_config({})
    return normalize_style_config(raw)


def write_site_style(path: Path, config: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_style_config(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    return normalized


def site_style_response(path: Path) -> dict[str, Any]:
    config = read_site_style(path)
    return {
        "activeKey": config["activeKey"],
        "activePreset": get_style_preset(config["activeKey"]),
        "presets": deepcopy(STYLE_PRESETS),
    }
