from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .config import settings
from .deepseek import deepseek_client


BASE_HOTWORDS = [
    "语音 Agent",
    "AI Agent",
    "Agent",
    "ASR",
    "TTS",
    "KWS",
    "RTOS",
    "LLM",
    "RAG",
    "vLLM",
    "DeepSeek",
    "MiMo",
    "FastAPI",
    "LangChain",
    "Pandas",
    "FreeSWITCH",
    "Linux",
    "C++",
    "Python",
    "智能家居",
    "语音客服",
    "语音识别",
    "语音合成",
    "关键词识别",
    "语义理解",
    "多 Agent",
    "多模态",
    "声学前端",
    "降噪",
    "回声消除",
    "波束成型",
    "首 token",
    "P95",
    "分布式内存数据库",
    "欧瑞博",
    "华为 2012 实验室",
    "恒生电子",
    "蜂言智能",
]

_HOTWORD_CACHE: dict[str, list[str]] = {}
_CORRECTION_CACHE: dict[str, str] = {}


async def asr_hotwords_for_profile(profile: dict[str, Any]) -> list[str]:
    cache_key = profile_cache_key(profile)
    if cache_key in _HOTWORD_CACHE:
        return _HOTWORD_CACHE[cache_key]

    local_words = local_asr_hotwords(profile)
    generated_words: list[str] = []
    if deepseek_client.configured:
        try:
            generated_words = await extract_hotwords_with_llm(profile, local_words)
        except Exception:  # noqa: BLE001
            generated_words = []

    hotwords = merge_hotwords(generated_words, local_words, BASE_HOTWORDS)
    _HOTWORD_CACHE[cache_key] = hotwords
    return hotwords


async def correct_asr_transcript(text: str, hotwords: list[str]) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return ""

    local_corrected = correct_asr_transcript_locally(cleaned, hotwords)
    if not deepseek_client.configured or not hotwords:
        return local_corrected

    cache_key = correction_cache_key(cleaned, hotwords)
    if cache_key in _CORRECTION_CACHE:
        return _CORRECTION_CACHE[cache_key]

    try:
        corrected = await correct_asr_transcript_with_llm(cleaned, hotwords)
        corrected = correct_asr_transcript_locally(corrected, hotwords)
    except Exception:  # noqa: BLE001
        corrected = local_corrected

    _CORRECTION_CACHE[cache_key] = corrected
    return corrected


def local_asr_hotwords(profile: dict[str, Any]) -> list[str]:
    words: list[str] = []
    meta = profile.get("meta") or {}
    for key in ("name", "title", "tagline", "education"):
        words.extend(split_hotword_text(str(meta.get(key, ""))))

    for group in ("highlights", "experience", "projects", "awards"):
        for item in profile.get(group, []):
            words.extend(split_hotword_text(str(item.get("title", ""))))
            words.extend(extract_terms(str(item.get("body", ""))))
            words.extend(extract_terms(str(item.get("focus", ""))))

    words.extend(extract_terms(str(profile.get("plainText", ""))))
    return merge_hotwords(words, BASE_HOTWORDS)


def cached_or_local_asr_hotwords(profile: dict[str, Any]) -> list[str]:
    cache_key = profile_cache_key(profile)
    if cache_key in _HOTWORD_CACHE:
        return _HOTWORD_CACHE[cache_key]
    return local_asr_hotwords(profile)


async def extract_hotwords_with_llm(profile: dict[str, Any], local_words: list[str]) -> list[str]:
    context = str(profile.get("plainText", ""))[:9000]
    prompt = f"""
你是语音识别 ASR 热词抽取器。请从候选人资料中抽取访客或面试官口述时高概率会用到、且容易被识别错的热词。

重点抽取：
- 中英文混合词，例如“语音 Agent”“AI Agent”“首 token”
- 英文缩写和技术名，例如 ASR、TTS、KWS、RTOS、RAG、vLLM
- 公司名、项目名、产品名、人名、专业术语
- 面试官可能围绕岗位匹配、项目难点、技术栈、量化结果追问的词

要求：
- 输出 JSON 字符串数组，最多 80 个。
- 保留推荐展示写法和大小写，例如 "语音 Agent"、"ASR/TTS/KWS"。
- 不要解释，不要 Markdown，不要输出资料里没有根据的词。

本地已抽取候选词：
{json.dumps(local_words[:80], ensure_ascii=False)}

候选人资料：
{context}
""".strip()
    raw = await deepseek_client.chat(
        [
            {"role": "system", "content": "你只输出 JSON 字符串数组。"},
            {"role": "user", "content": prompt},
        ]
    )
    parsed = parse_json_array(raw)
    return [str(item) for item in parsed if isinstance(item, str)]


async def correct_asr_transcript_with_llm(text: str, hotwords: list[str]) -> str:
    prompt = f"""
你是 ASR 识别结果的术语纠错器。只允许修正专有名词、中英文混排、英文大小写、斜杠和空格，不要改写语义，不要补充原文没有的信息。

可用热词：
{json.dumps(hotwords[:90], ensure_ascii=False)}

原始识别文本：
{text}

请只输出纠错后的文本，不要解释。
""".strip()
    corrected = await deepseek_client.chat(
        [
            {"role": "system", "content": "只做 ASR 术语纠错，输出纯文本。"},
            {"role": "user", "content": prompt},
        ]
    )
    return corrected.strip().strip("`")


def correct_asr_transcript_locally(text: str, hotwords: list[str]) -> str:
    corrected = text.strip()
    aliases = {
        "语音agent": "语音 Agent",
        "语音代理": "语音 Agent",
        "ai agent": "AI Agent",
        "a i agent": "AI Agent",
        "多agent": "多 Agent",
        "as r": "ASR",
        "a s r": "ASR",
        "tt s": "TTS",
        "t t s": "TTS",
        "kw s": "KWS",
        "k w s": "KWS",
        "kws": "KWS",
        "rt os": "RTOS",
        "r t o s": "RTOS",
        "ll m": "LLM",
        "l l m": "LLM",
        "ra g": "RAG",
        "r a g": "RAG",
        "v llm": "vLLM",
        "v l l m": "vLLM",
        "free switch": "FreeSWITCH",
        "首token": "首 token",
        "首token优化": "首 token 优化",
        "p 95": "P95",
        "p九五": "P95",
    }
    for alias, canonical in aliases.items():
        corrected = replace_case_insensitive(corrected, alias, canonical)

    for word in hotwords:
        canonical = normalize_hotword(word)
        if not canonical:
            continue
        compact = re.sub(r"[\s/·\-]+", "", canonical)
        if compact and compact != canonical and contains_mixed_or_ascii(canonical):
            corrected = replace_case_insensitive(corrected, compact, canonical)
        if canonical.lower() != canonical:
            corrected = replace_case_insensitive(corrected, canonical.lower(), canonical)
    corrected = re.sub(r"ASR\s+TTS\s+KWS", "ASR/TTS/KWS", corrected)
    corrected = re.sub(r"ASR\s*/\s*TTS\s*/\s*KWS", "ASR/TTS/KWS", corrected)
    corrected = re.sub(r"([A-Za-z0-9+#./]+)([\u4e00-\u9fff])", r"\1 \2", corrected)
    corrected = re.sub(r"([\u4e00-\u9fff])([A-Za-z0-9+#./]+)", r"\1 \2", corrected)
    return corrected.strip()


def split_hotword_text(text: str) -> list[str]:
    if not text:
        return []
    parts = re.split(r"[|,，、/·\n]+", text)
    return [part.strip() for part in parts if part.strip()]


def extract_terms(text: str) -> list[str]:
    if not text:
        return []
    terms: list[str] = []
    terms.extend(re.findall(r"[\u4e00-\u9fff]{1,10}\s*[A-Za-z][A-Za-z0-9+#.-]*(?:/[A-Za-z0-9+#.-]+)*", text))
    terms.extend(re.findall(r"[A-Za-z][A-Za-z0-9+#.-]*(?:/[A-Za-z0-9+#.-]+)+", text))
    terms.extend(re.findall(r"\b[A-Za-z][A-Za-z0-9+#.-]{1,}\b", text))
    terms.extend(re.findall(r"P\d{2,3}|[A-Z]{2,6}", text))
    for phrase in ("智能家居", "语音客服", "语音识别", "语音合成", "关键词识别", "语义理解", "分布式内存数据库"):
        if phrase in text:
            terms.append(phrase)
    return terms


def merge_hotwords(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for word in group:
            cleaned = normalize_hotword(word)
            if not cleaned:
                continue
            key = re.sub(r"\s+", "", cleaned).lower()
            if key in seen:
                continue
            seen.add(key)
            merged.append(cleaned)
    return merged[:100]


def normalize_hotword(word: str) -> str:
    cleaned = re.sub(r"\s+", " ", str(word or "").strip(" \t\r\n'\"`，。；;:："))
    if len(cleaned) < 2 or len(cleaned) > 40:
        return ""
    if cleaned in {"负责", "开发", "项目", "能力", "经验", "系统", "模型", "服务"}:
        return ""
    return cleaned


def contains_mixed_or_ascii(text: str) -> bool:
    return bool(re.search(r"[A-Za-z]", text))


def replace_case_insensitive(text: str, source: str, target: str) -> str:
    if not source:
        return text
    return re.sub(re.escape(source), target, text, flags=re.IGNORECASE)


def parse_json_array(text: str) -> list[Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    start = cleaned.find("[")
    end = cleaned.rfind("]")
    if start == -1 or end == -1:
        return []
    try:
        parsed = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def profile_cache_key(profile: dict[str, Any]) -> str:
    text = str(profile.get("plainText", ""))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def correction_cache_key(text: str, hotwords: list[str]) -> str:
    payload = text + "\n" + "\n".join(hotwords[:100])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
