from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import settings


ALLOWED_REFERENCE_TYPES = {
    "audio/wav": ".wav",
    "audio/wave": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
}
MAX_REFERENCE_BASE64_BYTES = 10 * 1024 * 1024


def read_voice_clone_reference() -> dict:
    meta = read_reference_meta()
    audio_path = reference_audio_path(meta)
    if not meta or not audio_path or not audio_path.exists():
        return empty_reference("尚未上传参考音色。")
    return {
        "enabled": True,
        "filename": meta.get("filename", audio_path.name),
        "contentType": meta.get("contentType", "audio/wav"),
        "size": int(meta.get("size", audio_path.stat().st_size)),
        "updatedAt": meta.get("updatedAt", ""),
        "message": "已配置参考音色，首页 TTS 将使用小米音色复刻。",
    }


def save_voice_clone_reference(audio: bytes, content_type: str, filename: str = "") -> dict:
    normalized_type = normalize_content_type(content_type)
    suffix = ALLOWED_REFERENCE_TYPES.get(normalized_type)
    if not suffix:
        raise ValueError("参考音色只支持 WAV 或 MP3 文件。")
    if not audio:
        raise ValueError("参考音频为空。")
    if len(base64.b64encode(audio)) > MAX_REFERENCE_BASE64_BYTES:
        raise ValueError("参考音频过大：Base64 后不能超过 10 MB。")

    base_path = settings.resolved_voice_clone_reference_path
    base_path.parent.mkdir(parents=True, exist_ok=True)
    for old_path in base_path.parent.glob(f"{base_path.name}.*"):
        if old_path.suffix.lower() in {".wav", ".mp3", ".json"}:
            old_path.unlink(missing_ok=True)

    audio_path = base_path.with_suffix(suffix)
    audio_path.write_bytes(audio)
    meta = {
        "filename": sanitize_filename(filename) or f"voice-reference{suffix}",
        "contentType": normalized_type,
        "size": len(audio),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "path": audio_path.name,
    }
    meta_path().write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return read_voice_clone_reference()


def delete_voice_clone_reference() -> dict:
    base_path = settings.resolved_voice_clone_reference_path
    base_path.parent.mkdir(parents=True, exist_ok=True)
    for old_path in base_path.parent.glob(f"{base_path.name}.*"):
        if old_path.suffix.lower() in {".wav", ".mp3", ".json"}:
            old_path.unlink(missing_ok=True)
    return empty_reference("已删除参考音色，首页 TTS 将恢复默认音色。")


def voice_clone_reference_data_url() -> str:
    meta = read_reference_meta()
    audio_path = reference_audio_path(meta)
    if not meta or not audio_path or not audio_path.exists():
        return ""

    encoded = base64.b64encode(audio_path.read_bytes()).decode("ascii")
    if len(encoded.encode("ascii")) > MAX_REFERENCE_BASE64_BYTES:
        raise ValueError("参考音频过大：Base64 后不能超过 10 MB。")
    content_type = meta.get("contentType") or guess_content_type(audio_path)
    return f"data:{content_type};base64,{encoded}"


def normalize_content_type(content_type: str) -> str:
    return (content_type or "").split(";", 1)[0].strip().lower()


def sanitize_filename(filename: str) -> str:
    cleaned = Path(filename or "").name.strip()
    return cleaned[:120]


def read_reference_meta() -> dict:
    path = meta_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def reference_audio_path(meta: dict) -> Path | None:
    base_path = settings.resolved_voice_clone_reference_path
    name = meta.get("path") if isinstance(meta, dict) else ""
    if isinstance(name, str) and name:
        return (base_path.parent / Path(name).name).resolve()
    for suffix in (".wav", ".mp3"):
        path = base_path.with_suffix(suffix)
        if path.exists():
            return path
    return None


def meta_path() -> Path:
    return settings.resolved_voice_clone_reference_path.with_suffix(".json")


def guess_content_type(path: Path) -> str:
    if path.suffix.lower() == ".mp3":
        return "audio/mpeg"
    return "audio/wav"


def empty_reference(message: str = "") -> dict:
    return {
        "enabled": False,
        "filename": "",
        "contentType": "",
        "size": 0,
        "updatedAt": "",
        "message": message,
    }
