from __future__ import annotations

import json
import re
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any

from .content import knowledge_context
from .deepseek import deepseek_client
from .config import settings

_briefing_cache: dict[str, dict[str, Any]] = {}


def read_briefing_override(path: Path, profile: dict[str, Any]) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    current_source_hash = profile_source_hash(profile)
    saved_source_hash = raw.get("sourceHash") or raw.get("generationMeta", {}).get("sourceHash")
    if saved_source_hash and saved_source_hash != current_source_hash:
        return None
    if not saved_source_hash and is_legacy_briefing(raw, profile):
        return None
    fallback = local_briefing(profile)
    merged = merge_briefing(fallback, raw)
    merged["generated"] = bool(raw.get("generated", True))
    merged["aiConfigured"] = deepseek_client.configured
    merged["aiProvider"] = raw.get("aiProvider") or deepseek_client.provider_label
    merged["generationMeta"] = raw.get("generationMeta") or generation_meta(
        status="saved",
        generated=merged["generated"],
        provider=merged["aiProvider"],
        model=raw.get("aiModel", ""),
    )
    merged["sourceHash"] = current_source_hash
    merged["generationMeta"]["sourceHash"] = current_source_hash
    return merged


def write_briefing_override(path: Path, briefing: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(briefing, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )


def local_briefing(profile: dict[str, Any]) -> dict[str, Any]:
    meta = profile["meta"]
    highlights = profile["highlights"]
    experience = profile["experience"]
    projects = profile["projects"]
    return {
        "meta": meta,
        "page": {
            "nav": {
                "capabilities": "能力地图",
                "timeline": "经历证据",
                "projects": "项目",
                "export": "导出简历",
                "admin": "作者后台",
            },
            "assistant": {
                "eyebrow": "AI 助手",
                "title": f"向{meta.get('name', '王涛')}提问",
                "context": "我是授权 AI 助手，可代替本人向招聘方简短回答经历、项目和岗位匹配问题。",
                "placeholder": "问：语音 Agent 难点？",
                "voiceHint": "语音输入为辅助入口；浏览器不支持时可直接使用文字。",
            },
            "sections": {
                "capabilities": {
                    "eyebrow": "Capability map",
                    "title": "招聘方最需要先判断的能力面",
                    "intro": "把技能栈重新组织为岗位评估维度：语音链路、AI 工程、系统能力和真实交付。",
                },
                "evidence": {
                    "eyebrow": "Evidence trail",
                    "title": "经历与项目证据",
                    "intro": "用时间线和代表项目交叉验证职责、成果和工程可信度。",
                },
                "timeline": {
                    "title": "经历时间线",
                    "intro": "按阶段展示职责边界、关键结果和技术深度。",
                },
                "projects": {
                    "title": "代表项目",
                    "intro": "AI 问答会优先引用这些可核查资料，避免脱离事实包装。",
                },
                "export": {
                    "eyebrow": "Resume export",
                    "title": "需要投递版简历时，再按 JD 生成",
                    "intro": "导出模块会基于同一份事实资料调整重点、排序和表达，但不会新增资料中没有的经历。",
                    "button": "选择模板导出",
                },
            },
        },
        "hero": {
            "eyebrow": "AI career briefing for recruiters",
            "headline": meta.get("name", "王涛"),
            "statement": "把语音 AI、Agent 编排和后端系统落到真实产品里的工程师。",
            "subtitle": f"{meta.get('title', '')} · {meta.get('tagline', '')}",
            "summary": "面向招聘方的个人能力介绍页。你可以快速浏览关键证据，也可以直接向 AI 询问岗位匹配、项目细节和可量化成果。",
        },
        "fitSignals": [
            {
                "label": "主线方向",
                "value": "语音 AI / Agent",
                "detail": "从智能语音客服到智能家居语音 Agent，经历主线连续。",
            },
            {
                "label": "工程底座",
                "value": "Linux 后端 / 分布式",
                "detail": "有分布式内存数据库、构建、性能和可靠性经验支撑。",
            },
            {
                "label": "可验证结果",
                "value": "延迟与成本优化",
                "detail": "资料中包含端到端首帧语音延迟、模型链路和 ASR/TTS 成本优化结果。",
            },
        ],
        "metrics": [
            {"value": "10s→1s", "label": "P95 端到端首帧语音延迟", "note": "上下文裁剪、模型路由、流式响应、缓存和并行链路优化"},
            {"value": "95%", "label": "Token 成本降低", "note": "模型分层路由、上下文治理与缓存协同"},
            {"value": "60%", "label": "ASR/TTS 成本降低", "note": "服务评测、替换与调优"},
        ],
        "capabilities": [
            {"title": item["title"], "body": item["body"], "evidence": "profile.md"}
            for item in highlights[:5]
        ],
        "timeline": [
            {"title": item["title"], "body": item["body"], "focus": summarize_body(item["body"])}
            for item in experience
        ],
        "projects": [
            {"title": item["title"], "body": item["body"], "focus": summarize_body(item["body"])}
            for item in projects[:3]
        ],
        "suggestedQuestions": [
            "他适合语音 AI 岗位吗？",
            "他的后端系统能力体现在哪里？",
            "有哪些可量化成果？",
            "如果我是智能硬件团队，应该重点看什么？",
        ],
        "generated": False,
        "aiConfigured": deepseek_client.configured,
        "aiProvider": deepseek_client.provider_label,
        "sourceHash": profile_source_hash(profile),
        "generationMeta": generation_meta(status="local", generated=False, source_hash=profile_source_hash(profile)),
    }


async def generate_briefing(profile: dict[str, Any], *, use_override: bool = True) -> dict[str, Any]:
    if use_override:
        override = read_briefing_override(settings.resolved_home_briefing_path, profile)
        if override:
            return deepcopy(override)

    cache_key = briefing_cache_key(profile)
    if cache_key in _briefing_cache:
        cached = deepcopy(_briefing_cache[cache_key])
        cached["generationMeta"] = {
            **cached.get("generationMeta", generation_meta(status="cached", generated=cached.get("generated", False))),
            "status": "cached",
            "cached": True,
        }
        return cached

    fallback = local_briefing(profile)
    if not deepseek_client.configured:
        _briefing_cache[cache_key] = fallback
        return deepcopy(fallback)

    context = knowledge_context(profile)
    prompt = f"""
你是个人介绍页的信息架构设计师。请基于候选人 Markdown 资料，生成适合招聘方浏览的结构化 JSON。

严格要求：
- 只能基于资料事实，不要虚构经历、公司、数字或能力。
- 内容要专业、克制、简洁，避免营销腔。
- 页面文案直接使用姓名，不要使用“候选人”这类泛称。
- assistant 是代替候选人回答访客的授权 AI 助手，访客通常是招聘方或面试官；对话说明不要写成面向候选人本人。
- assistant 的 context 要说明“可简短回答经历、项目、岗位匹配”，不要承诺无依据内容。
- suggestedQuestions 要适合招聘方连续追问，短问题为主。
- 指标必须使用资料中的最新术语，例如“P95 端到端首帧语音延迟”“Token 成本降低”“ASR/TTS 成本降低”；不要改写成旧的“P95 首 token”。
- 输出必须是 JSON，不要 Markdown，不要解释。
- JSON schema:
{{
  "page": {{
    "nav": {{"capabilities": "导航文案", "timeline": "导航文案", "projects": "导航文案", "export": "导航文案", "admin": "导航文案"}},
    "assistant": {{"eyebrow": "短标签", "title": "对话框标题", "context": "对话框说明，70字以内", "placeholder": "输入框占位文案", "voiceHint": "语音提示"}},
    "sections": {{
      "capabilities": {{"eyebrow": "短标签", "title": "分区标题", "intro": "分区说明，70字以内"}},
      "evidence": {{"eyebrow": "短标签", "title": "分区标题", "intro": "分区说明，70字以内"}},
      "timeline": {{"title": "分区标题", "intro": "分区说明，70字以内"}},
      "projects": {{"title": "分区标题", "intro": "分区说明，70字以内"}},
      "export": {{"eyebrow": "短标签", "title": "分区标题", "intro": "分区说明，70字以内", "button": "按钮文案"}}
    }}
  }},
  "hero": {{
    "eyebrow": "短英文或中文标签",
    "headline": "姓名，不能为空",
    "statement": "一句定位，30字以内",
    "subtitle": "职位和方向",
    "summary": "首屏摘要，80字以内"
  }},
  "fitSignals": [
    {{"label": "判断维度", "value": "短结论", "detail": "事实依据，45字以内"}}
  ],
  "metrics": [
    {{"value": "数字或结果", "label": "指标名", "note": "事实说明"}}
  ],
  "capabilities": [
    {{"title": "能力维度", "body": "80字以内说明", "evidence": "来自哪个经历或项目"}}
  ],
  "timeline": [
    {{"title": "公司 | 职位 | 时间", "body": "保留资料要点，允许换行项目符号", "focus": "该段经历的评估重点"}}
  ],
  "projects": [
    {{"title": "项目名", "body": "保留资料要点，允许换行项目符号", "focus": "项目证明什么能力"}}
  ],
  "suggestedQuestions": ["给招聘方点击的预设问题，4条"]
}}

资料：
{context}
"""
    try:
        raw = await deepseek_client.chat(
            [
                {"role": "system", "content": f"你只输出合法 JSON。候选人姓名是 {fallback['meta'].get('name', fallback['hero']['headline'])}，不得使用任何其他人名。"},
                {"role": "user", "content": prompt},
            ]
        )
        parsed = parse_json_object(raw)
        merged = merge_briefing(fallback, parsed)
        merged["generated"] = True
        merged["aiConfigured"] = True
        merged["aiProvider"] = deepseek_client.last_provider_label
        merged["generationMeta"] = generation_meta(
            status="generated",
            generated=True,
            provider=deepseek_client.last_provider_label,
            model=deepseek_client.last_model,
            source_hash=profile_source_hash(profile),
        )
        merged["sourceHash"] = profile_source_hash(profile)
        _briefing_cache[cache_key] = merged
        return deepcopy(merged)
    except Exception:
        fallback["generationMeta"] = generation_meta(
            status="fallback",
            generated=False,
            source_hash=profile_source_hash(profile),
        )
        _briefing_cache[cache_key] = fallback
        return deepcopy(fallback)


async def adjust_briefing_with_ai(
    profile: dict[str, Any],
    current_briefing: dict[str, Any],
    instruction: str,
) -> dict[str, Any]:
    fallback = local_briefing(profile)
    if not deepseek_client.configured:
        return deepcopy(current_briefing)

    prompt = f"""
你是个人介绍页首页编排助手。请基于当前首页 JSON 和候选人 Markdown 资料，按指令调整首页展示文案与排序。

严格要求：
- 只能调整首页展示结构和文案，不要修改候选人的事实资料。
- 不得新增资料中没有的经历、公司、时间、数字或成果。
- headline 必须保持为候选人姓名。
- assistant 是代替候选人回答访客的授权 AI 助手，访客通常是招聘方或面试官。
- assistant 文案要支持多轮短问短答，不要写成面向候选人本人。
- 指标必须跟随候选人 Markdown 的当前表述，例如“P95 端到端首帧语音延迟”“Token 成本降低”“ASR/TTS 成本降低”；不要沿用旧首页 JSON 里的“P95 首 token”。
- 输出必须是完整 JSON，不要 Markdown，不要解释。

修改指令：
{instruction}

候选人资料：
{knowledge_context(profile)}

当前首页 JSON：
{json.dumps(current_briefing, ensure_ascii=False)}
"""
    raw = await deepseek_client.chat(
        [
            {"role": "system", "content": "你只输出合法 JSON，且不得编造事实。"},
            {"role": "user", "content": prompt},
        ]
    )
    parsed = parse_json_object(raw)
    merged = merge_briefing(fallback, parsed)
    merged["generated"] = True
    merged["aiConfigured"] = True
    merged["aiProvider"] = deepseek_client.last_provider_label
    merged["generationMeta"] = generation_meta(
        status="generated",
        generated=True,
        provider=deepseek_client.last_provider_label,
        model=deepseek_client.last_model,
        source_hash=profile_source_hash(profile),
    )
    merged["sourceHash"] = profile_source_hash(profile)
    polish_generated_copy(merged, fallback)
    return merged


def clear_briefing_cache() -> None:
    _briefing_cache.clear()


def generation_meta(
    *,
    status: str,
    generated: bool,
    provider: str = "",
    model: str = "",
    source_hash: str = "",
) -> dict[str, Any]:
    return {
        "status": status,
        "generated": generated,
        "provider": provider or deepseek_client.provider_label,
        "model": model or deepseek_client.model_for("chat"),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "cached": False,
        "sourceHash": source_hash,
    }


def profile_source_hash(profile: dict[str, Any]) -> str:
    raw = profile.get("rawMarkdown", "")
    return sha256(raw.encode("utf-8")).hexdigest()


def is_legacy_briefing(raw: dict[str, Any], profile: dict[str, Any]) -> bool:
    raw_text = json.dumps(raw, ensure_ascii=False)
    source_text = profile.get("rawMarkdown", "")
    legacy_terms = ["P95首token", "P95 首 token", "首token耗时", "讯飞NLP大赛", "讯飞 NLP 大赛"]
    if any(term in raw_text for term in legacy_terms):
        return True
    return "P95 端到端首帧语音延迟" in source_text and "P95 端到端首帧语音延迟" not in raw_text


def parse_json_object(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("No JSON object found.")
    return json.loads(cleaned[start : end + 1])


def merge_briefing(fallback: dict[str, Any], generated: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(fallback)
    result["page"] = merge_nested_dict(fallback["page"], generated.get("page"))
    result["hero"] = merge_nested_dict(fallback["hero"], generated.get("hero"), limit=220)
    result["hero"]["headline"] = fallback["hero"]["headline"]
    result["fitSignals"] = merge_dict_list(
        fallback["fitSignals"],
        generated.get("fitSignals"),
        ["label", "value", "detail"],
        max_items=4,
        min_items=3,
        limit=120,
    )
    result["metrics"] = merge_dict_list(
        fallback["metrics"],
        generated.get("metrics"),
        ["value", "label", "note"],
        max_items=4,
        min_items=3,
        limit=120,
    )
    result["capabilities"] = merge_dict_list(
        fallback["capabilities"],
        generated.get("capabilities"),
        ["title", "body", "evidence"],
        max_items=6,
        min_items=3,
        limit=520,
    )
    result["timeline"] = merge_dict_list(
        fallback["timeline"],
        generated.get("timeline"),
        ["title", "body", "focus"],
        max_items=6,
        min_items=1,
        limit=1400,
    )
    result["projects"] = merge_dict_list(
        fallback["projects"],
        generated.get("projects"),
        ["title", "body", "focus"],
        max_items=4,
        min_items=1,
        limit=1400,
    )
    result["suggestedQuestions"] = merge_question_list(
        fallback["suggestedQuestions"],
        generated.get("suggestedQuestions"),
    )
    result["meta"] = fallback["meta"]
    polish_generated_copy(result, fallback)
    return result


def briefing_cache_key(profile: dict[str, Any]) -> str:
    raw = profile.get("rawMarkdown", "")
    payload = f"{deepseek_client.active_provider}:{deepseek_client.chat_model}:{raw}"
    return sha256(payload.encode("utf-8")).hexdigest()


def merge_nested_dict(fallback: dict[str, Any], generated: Any, limit: int = 260) -> dict[str, Any]:
    if not isinstance(generated, dict):
        return deepcopy(fallback)

    merged = deepcopy(fallback)
    for key, fallback_value in fallback.items():
        generated_value = generated.get(key)
        if isinstance(fallback_value, dict):
            merged[key] = merge_nested_dict(fallback_value, generated_value, limit)
        else:
            merged[key] = clean_text(generated_value, fallback_value, limit)
    return merged


def merge_dict_list(
    fallback: list[dict[str, Any]],
    generated: Any,
    fields: list[str],
    max_items: int,
    min_items: int,
    limit: int,
) -> list[dict[str, str]]:
    if not isinstance(generated, list):
        return deepcopy(fallback[:max_items])

    items: list[dict[str, str]] = []
    for index, raw_item in enumerate(generated[:max_items]):
        if not isinstance(raw_item, dict):
            continue
        fallback_item = fallback[index] if index < len(fallback) else {}
        item = {
            field: clean_text(raw_item.get(field), fallback_item.get(field, ""), limit)
            for field in fields
        }
        if item.get(fields[0]):
            items.append(item)

    if len(items) < min_items:
        return deepcopy(fallback[:max_items])
    return items


def merge_question_list(fallback: list[str], generated: Any) -> list[str]:
    if not isinstance(generated, list):
        return deepcopy(fallback)
    questions = []
    for item in generated:
        text = normalize_question(clean_text(item, "", 80))
        if text and text not in questions:
            questions.append(text)
    return questions[:5] if len(questions) >= 3 else deepcopy(fallback)


def clean_text(value: Any, fallback: Any = "", limit: int = 260) -> str:
    if value is None:
        return str(fallback or "")
    text = str(value).strip()
    if not text:
        return str(fallback or "")
    return text[:limit]


def polish_generated_copy(result: dict[str, Any], fallback: dict[str, Any]) -> None:
    name = fallback["meta"].get("name") or fallback["hero"]["headline"]
    replace_candidate_label(result, name)
    normalize_current_metric_terms(result, fallback)

    assistant = result.get("page", {}).get("assistant", {})
    title = assistant.get("title", "")
    if "任何问题" in title or "咨询" in title or len(title) > 18:
        assistant["title"] = f"向{name}提问"
    context = assistant.get("context", "")
    if not context or "AI助手" in context or "AI 助手" in context or "提问" in context or len(context) > 80:
        assistant["context"] = "我是授权 AI 助手，可代替本人向招聘方简短回答经历、项目和岗位匹配问题。"
    placeholder = assistant.get("placeholder", "")
    if not placeholder or "您的" in placeholder or len(placeholder) > 32:
        assistant["placeholder"] = "问：语音 Agent 难点？"
    normalized_questions = [
        normalize_question(question)
        for question in result.get("suggestedQuestions", fallback["suggestedQuestions"])
    ][:5]
    if len(normalized_questions) < 4 or any("成？" in item for item in normalized_questions):
        normalized_questions = deepcopy(fallback["suggestedQuestions"])
    result["suggestedQuestions"] = normalized_questions


def normalize_question(text: str) -> str:
    replacements = {
        "你在欧瑞博如何两个月内完成 Agent 架构从规则引擎到多 Agent 的迁移？": "语音 Agent 项目难点是什么？",
        "分布式内存数据库中如何保证数据一致性与高可用？": "数据库经历证明了什么？",
        "请具体描述你在华为 2012 实验室推进代码质量与测试体系的方法。": "他的工程质量经验如何？",
        "在蜂言智能语音客服项目中，如何处理复杂场景下的多轮对话与错误纠正？": "语音客服经验有什么价值？",
    }
    if text in replacements:
        return replacements[text]
    if "欧瑞博" in text or "Agent" in text:
        return "语音 Agent 项目难点是什么？"
    if "分布式" in text or "数据库" in text:
        return "数据库经历证明了什么？"
    if "华为" in text or "代码质量" in text or "测试" in text:
        return "他的工程质量经验如何？"
    if "语音识别" in text or "纠错" in text:
        return "语音纠错经验是什么？"
    if "KWS" in text or "在线学习" in text:
        return "KWS 在线学习怎么做？"
    if "首 token" in text or "延迟" in text or "性能优化" in text:
        return "延迟优化结果如何做到？"
    if "AI工程" in text or "AI 工程" in text or "落地" in text:
        return "AI 工程落地经验有哪些？"
    if "成本" in text and "性能" in text:
        return "如何平衡成本和性能？"
    if "ASR" in text or "TTS" in text:
        return "ASR/TTS 成本怎么降低？"
    if "语音客服" in text or "蜂言" in text:
        return "语音客服经验有什么价值？"
    if len(text) <= 24:
        return text
    return ""


def replace_candidate_label(value: Any, name: str) -> None:
    if isinstance(value, dict):
        for key, item in list(value.items()):
            if isinstance(item, str):
                value[key] = replace_wrong_person_refs(item, name)
            else:
                replace_candidate_label(item, name)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            if isinstance(item, str):
                value[index] = replace_wrong_person_refs(item, name)
            else:
                replace_candidate_label(item, name)


def replace_wrong_person_refs(text: str, name: str) -> str:
    cleaned = text.replace("候选人", name)
    for wrong_name in {"郭佳"}:
        cleaned = cleaned.replace(wrong_name, name)
    return cleaned


def normalize_current_metric_terms(result: dict[str, Any], fallback: dict[str, Any]) -> None:
    source_text = json.dumps(fallback, ensure_ascii=False)
    if "P95 端到端首帧语音延迟" not in source_text:
        return

    for item in result.get("metrics", []):
        label = item.get("label", "")
        note = item.get("note", "")
        if "首token" in label or "首 token" in label:
            item["label"] = "P95 端到端首帧语音延迟"
            if not note or "首 token" in note or "首token" in note:
                item["note"] = "上下文裁剪、模型路由、流式响应、缓存和并行链路优化"
        if label in {"成本降低", "语义链路成本降低"}:
            item["label"] = "Token 成本降低"
            if not note or "架构重构" in note or "语义链路" in note:
                item["note"] = "模型分层路由、上下文治理与缓存协同"

    for item in result.get("fitSignals", []):
        detail = item.get("detail", "")
        detail = detail.replace("首 token", "端到端首帧语音延迟").replace("首token", "端到端首帧语音延迟")
        item["detail"] = detail


def summarize_body(body: str) -> str:
    clean = re.sub(r"[-•]\s*", "", body)
    lines = [line.strip() for line in clean.splitlines() if line.strip()]
    return "；".join(lines[:2])[:120]
