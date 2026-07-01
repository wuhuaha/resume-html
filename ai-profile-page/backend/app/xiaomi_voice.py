from __future__ import annotations

import base64
import json
from typing import Any

import httpx

from .config import settings
from .voice_clone import voice_clone_reference_data_url


SUPPORTED_AUDIO_TYPES = {
    "audio/webm": "webm",
    "audio/wav": "wav",
    "audio/wave": "wav",
    "audio/x-wav": "wav",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/ogg": "ogg",
    "audio/mp4": "mp4",
}


def voice_configured() -> bool:
    return bool(settings.xiaomi_mimo_api_key.strip())


def voice_clone_enabled() -> bool:
    return bool(voice_clone_reference_data_url())


async def transcribe_audio(audio: bytes, content_type: str) -> str:
    if not voice_configured():
        raise ValueError("未配置小米 MiMo API Key。")
    if not audio:
        raise ValueError("音频内容为空。")

    payload = build_asr_payload(audio, content_type, stream=False)
    result = await post_mimo(payload)
    text = extract_text(result)
    if not text:
        raise ValueError("小米 ASR 未返回识别文本。")
    return text.strip()


async def stream_transcribe_audio(audio: bytes, content_type: str):
    if not voice_configured():
        raise ValueError("未配置小米 MiMo API Key。")
    if not audio:
        raise ValueError("音频内容为空。")

    payload = build_asr_payload(audio, content_type, stream=True)
    headers = mimo_headers()
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", settings.xiaomi_mimo_base_url, headers=headers, json=payload) as response:
            if response.status_code >= 400:
                error_text = (await response.aread()).decode("utf-8", errors="replace")
                raise ValueError(f"小米 MiMo 接口返回 {response.status_code}：{error_text[:300]}")

            async for line in response.aiter_lines():
                item = parse_stream_line(line)
                if item is None:
                    continue
                text = extract_delta_text(item)
                if text:
                    yield text.encode("utf-8")


def build_asr_payload(audio: bytes, content_type: str, stream: bool) -> dict[str, Any]:
    normalized_type = normalize_content_type(content_type)
    encoded = base64.b64encode(audio).decode("ascii")
    payload: dict[str, Any] = {
        "model": settings.xiaomi_mimo_asr_model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": f"data:{normalized_type};base64,{encoded}",
                        },
                    }
                ],
            }
        ],
        "asr_options": {
            "language": "auto",
        },
    }
    if stream:
        payload["stream"] = True
    return payload


async def synthesize_speech(text: str, reference_audio_data_url: str = "") -> tuple[bytes, str]:
    if not voice_configured():
        raise ValueError("未配置小米 MiMo API Key。")
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("待合成文本为空。")

    payload = build_tts_payload(cleaned, "wav", stream=False, reference_audio_data_url=reference_audio_data_url)
    result = await post_mimo(payload)
    audio_data = extract_audio(result)
    if not audio_data:
        raise ValueError("小米 TTS 未返回音频。")
    return base64.b64decode(audio_data), "audio/wav"


async def stream_synthesize_speech(text: str, reference_audio_data_url: str = ""):
    if not voice_configured():
        raise ValueError("未配置小米 MiMo API Key。")
    cleaned = text.strip()
    if not cleaned:
        raise ValueError("待合成文本为空。")
    if active_reference_voice(reference_audio_data_url):
        audio, _ = await synthesize_speech(cleaned, reference_audio_data_url)
        yield audio
        return

    payload = build_tts_payload(cleaned, "pcm16", stream=True, reference_audio_data_url=reference_audio_data_url)
    headers = mimo_headers()
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", settings.xiaomi_mimo_base_url, headers=headers, json=payload) as response:
            if response.status_code >= 400:
                error_text = (await response.aread()).decode("utf-8", errors="replace")
                raise ValueError(f"小米 MiMo 接口返回 {response.status_code}：{error_text[:300]}")

            async for line in response.aiter_lines():
                item = parse_stream_line(line)
                if item is None:
                    continue
                audio_data = extract_delta_audio(item)
                if audio_data:
                    yield base64.b64decode(audio_data)


def build_tts_payload(
    text: str,
    audio_format: str,
    stream: bool,
    reference_audio_data_url: str = "",
) -> dict[str, Any]:
    reference_voice = active_reference_voice(reference_audio_data_url)
    payload = {
        "model": settings.xiaomi_mimo_tts_voiceclone_model if reference_voice else settings.xiaomi_mimo_tts_model,
        "messages": [
            {
                "role": "user",
                "content": settings.xiaomi_mimo_tts_style,
            },
            {
                "role": "assistant",
                "content": text[:900],
            }
        ],
        "audio": {
            "format": audio_format,
            "voice": reference_voice or settings.xiaomi_mimo_tts_voice,
        },
    }
    if stream:
        payload["stream"] = True
    return payload


def active_reference_voice(reference_audio_data_url: str = "") -> str:
    cleaned = (reference_audio_data_url or "").strip()
    if cleaned:
        validate_reference_data_url(cleaned)
        return cleaned
    return voice_clone_reference_data_url()


def validate_reference_data_url(data_url: str) -> None:
    if not data_url.startswith(("data:audio/wav;base64,", "data:audio/wave;base64,", "data:audio/x-wav;base64,", "data:audio/mpeg;base64,", "data:audio/mp3;base64,")):
        raise ValueError("临时参考音色只支持 WAV 或 MP3 data URL。")
    if len(data_url.encode("utf-8")) > 11 * 1024 * 1024:
        raise ValueError("临时参考音频过大：Base64 后不能超过 10 MB。")


async def post_mimo(payload: dict[str, Any]) -> dict[str, Any]:
    headers = mimo_headers()
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(settings.xiaomi_mimo_base_url, headers=headers, json=payload)
    if response.status_code >= 400:
        raise ValueError(f"小米 MiMo 接口返回 {response.status_code}：{response.text[:300]}")
    return response.json()


def mimo_headers() -> dict[str, str]:
    headers = {
        "api-key": settings.xiaomi_mimo_api_key,
        "Content-Type": "application/json",
    }
    return headers


def normalize_content_type(content_type: str) -> str:
    return (content_type or "audio/webm").split(";", 1)[0].strip().lower()


def extract_text(result: dict[str, Any]) -> str:
    choices = result.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if isinstance(item.get("text"), str):
                    parts.append(item["text"])
                elif isinstance(item.get("transcript"), str):
                    parts.append(item["transcript"])
            elif isinstance(item, str):
                parts.append(item)
        return "".join(parts)
    return ""


def extract_audio(result: dict[str, Any]) -> str:
    choices = result.get("choices") or []
    for choice in choices:
        message = choice.get("message") or {}
        audio = message.get("audio")
        if isinstance(audio, dict):
            data = audio.get("data") or audio.get("audio")
            if isinstance(data, str):
                return data
        content = message.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    audio_item = item.get("audio") or item.get("output_audio")
                    if isinstance(audio_item, dict):
                        data = audio_item.get("data") or audio_item.get("audio")
                        if isinstance(data, str):
                            return data
                    if isinstance(item.get("data"), str) and item.get("type") in {"audio", "output_audio"}:
                        return item["data"]
    return ""


def parse_stream_line(line: str) -> dict[str, Any] | None:
    cleaned = line.strip()
    if not cleaned or cleaned.startswith(":"):
        return None
    if cleaned.startswith("data:"):
        cleaned = cleaned[5:].strip()
    if not cleaned or cleaned == "[DONE]":
        return None
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def extract_delta_audio(result: dict[str, Any]) -> str:
    choices = result.get("choices") or []
    for choice in choices:
        delta = choice.get("delta") or {}
        audio = delta.get("audio")
        if isinstance(audio, dict):
            data = audio.get("data") or audio.get("audio")
            if isinstance(data, str):
                return data
    return ""


def extract_delta_text(result: dict[str, Any]) -> str:
    choices = result.get("choices") or []
    parts = []
    for choice in choices:
        delta = choice.get("delta") or {}
        content = delta.get("content")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text") or item.get("transcript")
                    if isinstance(text, str):
                        parts.append(text)
                elif isinstance(item, str):
                    parts.append(item)
        message = choice.get("message") or {}
        message_content = message.get("content")
        if isinstance(message_content, str):
            parts.append(message_content)
    return "".join(parts)
