from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import settings


ALLOWED_AVATAR_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
MAX_AVATAR_BYTES = 2 * 1024 * 1024


def read_resume_avatar() -> dict:
    meta = read_avatar_meta()
    avatar_path = avatar_image_path(meta)
    if not meta or not avatar_path or not avatar_path.exists():
        return empty_avatar("尚未上传简历头像。")
    return {
        "enabled": True,
        "filename": meta.get("filename", avatar_path.name),
        "contentType": meta.get("contentType", guess_content_type(avatar_path)),
        "size": int(meta.get("size", avatar_path.stat().st_size)),
        "updatedAt": meta.get("updatedAt", ""),
        "dataUrl": avatar_data_url_from_path(avatar_path, meta.get("contentType") or guess_content_type(avatar_path)),
        "message": "已配置简历头像，导出模板可按配置显示。",
    }


def save_resume_avatar(image: bytes, content_type: str, filename: str = "") -> dict:
    normalized_type = normalize_content_type(content_type)
    suffix = ALLOWED_AVATAR_TYPES.get(normalized_type)
    if not suffix:
        raise ValueError("简历头像只支持 JPG、PNG 或 WebP。")
    if not image:
        raise ValueError("头像文件为空。")
    if len(image) > MAX_AVATAR_BYTES:
        raise ValueError("头像文件不能超过 2 MB。")

    base_path = settings.resolved_resume_avatar_path
    base_path.parent.mkdir(parents=True, exist_ok=True)
    for old_path in base_path.parent.glob(f"{base_path.name}.*"):
        if old_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".json"}:
            old_path.unlink(missing_ok=True)

    image_path = base_path.with_suffix(suffix)
    image_path.write_bytes(image)
    meta = {
        "filename": sanitize_filename(filename) or f"resume-avatar{suffix}",
        "contentType": normalized_type,
        "size": len(image),
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "path": image_path.name,
    }
    avatar_meta_path().write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return read_resume_avatar()


def delete_resume_avatar() -> dict:
    base_path = settings.resolved_resume_avatar_path
    base_path.parent.mkdir(parents=True, exist_ok=True)
    for old_path in base_path.parent.glob(f"{base_path.name}.*"):
        if old_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".json"}:
            old_path.unlink(missing_ok=True)
    return empty_avatar("已删除简历头像。")


def resume_avatar_data_url() -> str:
    meta = read_avatar_meta()
    avatar_path = avatar_image_path(meta)
    if not meta or not avatar_path or not avatar_path.exists():
        return ""
    content_type = meta.get("contentType") or guess_content_type(avatar_path)
    return avatar_data_url_from_path(avatar_path, content_type)


def avatar_data_url_from_path(path: Path, content_type: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def normalize_content_type(content_type: str) -> str:
    return (content_type or "").split(";", 1)[0].strip().lower()


def sanitize_filename(filename: str) -> str:
    cleaned = Path(filename or "").name.strip()
    return cleaned[:120]


def read_avatar_meta() -> dict:
    path = avatar_meta_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def avatar_image_path(meta: dict) -> Path | None:
    base_path = settings.resolved_resume_avatar_path
    name = meta.get("path") if isinstance(meta, dict) else ""
    if isinstance(name, str) and name:
        return (base_path.parent / Path(name).name).resolve()
    for suffix in (".jpg", ".png", ".webp"):
        path = base_path.with_suffix(suffix)
        if path.exists():
            return path
    return None


def avatar_meta_path() -> Path:
    return settings.resolved_resume_avatar_path.with_suffix(".json")


def guess_content_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".webp":
        return "image/webp"
    return "image/png"


def empty_avatar(message: str = "") -> dict:
    return {
        "enabled": False,
        "filename": "",
        "contentType": "",
        "size": 0,
        "updatedAt": "",
        "dataUrl": "",
        "message": message,
    }
