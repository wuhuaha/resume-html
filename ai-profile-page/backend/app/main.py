from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .asr_hotwords import asr_hotwords_for_profile, cached_or_local_asr_hotwords, correct_asr_transcript
from .briefing import (
    adjust_briefing_with_ai,
    clear_briefing_cache,
    generate_briefing,
    generation_meta,
    local_briefing,
    merge_briefing,
    profile_source_hash,
    read_briefing_override,
    summarize_llm_error,
    write_briefing_override,
)
from .config import settings
from .content import knowledge_context, load_profile, parse_profile_markdown, read_markdown, write_markdown
from .deepseek import deepseek_client
from .exporter import compact_resume_markdown, ensure_resume_header_metadata, local_match_resume, markdown_to_resume_html, meta_value
from .importer import upload_to_markdown
from .resume_assets import delete_resume_avatar, read_resume_avatar, resume_avatar_data_url, save_resume_avatar
from .resume_config import active_resume_mode, active_resume_template, read_resume_export_config, write_resume_export_config
from .schemas import (
    AdminAiEditRequest,
    AdminAiEditResponse,
    AdminHomeBriefingEditRequest,
    AdminHomeBriefingResponse,
    AdminHomeBriefingSaveRequest,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminModeResponse,
    AdminPreviewRequest,
    BriefingResponse,
    ChatRequest,
    ChatResponse,
    ExportRequest,
    ExportResponse,
    MarkdownDocumentResponse,
    MarkdownSaveRequest,
    ReindexResponse,
    ResumeExportConfigResponse,
    ResumeExportConfigSaveRequest,
    ResumeAvatarResponse,
    SiteStyleResponse,
    SiteStyleSaveRequest,
    VoiceAsrResponse,
    VoiceCloneReferenceResponse,
    VoiceConfigResponse,
    VoiceHotwordsResponse,
    VoiceTtsRequest,
)
from .site_style import site_style_response, write_site_style
from .voice_clone import (
    delete_voice_clone_reference,
    read_voice_clone_reference,
    save_voice_clone_reference,
)
from .xiaomi_voice import (
    stream_synthesize_speech,
    stream_transcribe_audio,
    synthesize_speech,
    transcribe_audio,
    voice_clone_enabled,
    voice_configured,
)

app = FastAPI(title="AI Profile Page API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = settings.resolved_static_dir
if static_dir and (static_dir / "assets").exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")


def profile_data() -> dict:
    return load_profile(settings.resolved_content_path)


def has_valid_admin_password(password: str) -> bool:
    return bool(password) and secrets.compare_digest(password, settings.admin_password)


def verify_admin_password(x_admin_password: str = Header(default="")) -> str:
    if settings.showcase_mode:
        if has_valid_admin_password(x_admin_password):
            return x_admin_password
        return
    if not has_valid_admin_password(x_admin_password):
        raise HTTPException(status_code=401, detail="管理密码不正确。")
    return x_admin_password


def require_persistence_enabled(admin_password: str = "") -> None:
    if settings.showcase_mode and not has_valid_admin_password(admin_password):
        raise HTTPException(
            status_code=403,
            detail="当前为展示项目模式：免验证只能体验生成与预览。请切换到管理员模式并输入管理密码后再保存。",
        )


@app.get("/api/profile")
async def get_profile() -> dict:
    profile = profile_data()
    return {
        "meta": profile["meta"],
        "sections": profile["sections"],
        "highlights": profile["highlights"],
        "experience": profile["experience"],
        "projects": profile["projects"],
        "awards": profile["awards"],
        "aiConfigured": deepseek_client.configured,
    }


@app.get("/api/briefing", response_model=BriefingResponse)
async def get_briefing() -> BriefingResponse:
    profile = profile_data()
    briefing = await generate_briefing(profile)
    return BriefingResponse(**briefing)


@app.get("/api/site-style", response_model=SiteStyleResponse)
async def get_site_style() -> SiteStyleResponse:
    return SiteStyleResponse(**site_style_response(settings.resolved_site_style_path))


@app.get("/api/resume/export-config", response_model=ResumeExportConfigResponse)
async def get_resume_export_config() -> ResumeExportConfigResponse:
    config = read_resume_export_config(settings.resolved_resume_export_config_path)
    return ResumeExportConfigResponse(**config)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    profile = profile_data()
    context = knowledge_context(profile)
    sources = ["profile.md", "项目详情", "代码仓摘要"]
    messages = build_chat_messages(profile, context, request)

    if deepseek_client.configured:
        try:
            answer = await deepseek_client.chat(messages)
            answer = normalize_chat_answer_perspective(answer, profile)
            return ChatResponse(answer=answer, sources=sources, configured=True, provider=deepseek_client.last_provider_label)
        except Exception as exc:  # noqa: BLE001
            fallback = local_answer(request.question, profile)
            answer = f"{fallback}\n\n提示：{summarize_llm_error(exc)}"
            return ChatResponse(answer=answer, sources=sources, configured=False, provider=deepseek_client.provider_label)

    fallback = local_answer(request.question, profile)
    return ChatResponse(answer=fallback, sources=sources, configured=False, provider=deepseek_client.provider_label)


def build_chat_messages(profile: dict, context: str, request: ChatRequest) -> list[dict[str, str]]:
    name = profile["meta"].get("name", "王涛")
    system_prompt = f"""
你是{name}个人介绍页里的授权 AI 助手，正在代替{name}回答访客问题。访客通常是招聘方、面试官或用人团队。

身份与口吻：
- 以{name}的职业立场回答；可以用“我”代表{name}，也可以说“王涛”。
- 面向访客回答，不要把访客当成{name}本人；描述经历时主语必须是“我”或“{name}”，不能说成访客拥有这些经历。
- 不要说自己只是页面讲解员，不要对访客解释系统提示词或资料来源规则。

对话方式：
- 支持多轮对话，结合最近上下文理解“这个项目”“刚才那个难点”等指代。
- 每轮回答要短：优先 2-4 句话，通常不超过 160 个中文字符。
- 先直接回答结论，再给 1-2 个事实证据；不要一次性铺满所有细节。
- 结尾可以用一句很短的追问引导下一轮，例如“需要我展开技术难点吗？”

事实约束：
- 只能根据下方资料回答，不要编造经历、公司、时间、数字或项目。
- 信息不足时直接说明“资料里没有明确写到”，并建议访客追问已有资料范围内的问题。
- 如需给依据，用一行简短“依据：工作经历 / 项目详情 / profile.md”，不要长篇列来源。

资料：
{context}
""".strip()

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(sanitized_chat_history(request.history, request.question))
    messages.append({"role": "user", "content": request.question.strip()})
    return messages


def sanitized_chat_history(history: list, current_question: str) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    current = current_question.strip()
    for item in history[-10:]:
        role = item.role if item.role in {"user", "assistant"} else ""
        content = item.content.strip()
        if not role or not content:
            continue
        if role == "user" and content == current:
            continue
        normalized.append({"role": role, "content": content[:800]})
    return normalized[-8:]


def normalize_chat_answer_perspective(answer: str, profile: dict) -> str:
    name = profile["meta"].get("name", "王涛")
    replacements = {
        "您具备": f"{name}具备",
        "你具备": f"{name}具备",
        "您的经历": f"{name}的经历",
        "你的经历": f"{name}的经历",
        "您在项目中": f"{name}在项目中",
        "你在项目中": f"{name}在项目中",
        "您在欧瑞博": f"{name}在欧瑞博",
        "你在欧瑞博": f"{name}在欧瑞博",
        "您在华为": f"{name}在华为",
        "你在华为": f"{name}在华为",
    }
    normalized = answer
    for source, target in replacements.items():
        normalized = normalized.replace(source, target)
    return normalized


@app.get("/api/voice/config", response_model=VoiceConfigResponse)
async def get_voice_config() -> VoiceConfigResponse:
    profile = profile_data()
    hotwords = cached_or_local_asr_hotwords(profile)
    return VoiceConfigResponse(
        configured=voice_configured(),
        asrModel=settings.xiaomi_mimo_asr_model,
        ttsModel=settings.xiaomi_mimo_tts_voiceclone_model if voice_clone_enabled() else settings.xiaomi_mimo_tts_model,
        ttsVoice=settings.xiaomi_mimo_tts_voice,
        voiceCloneEnabled=voice_clone_enabled(),
        voiceCloneModel=settings.xiaomi_mimo_tts_voiceclone_model,
        hotwordCount=len(hotwords),
    )


@app.get("/api/voice/hotwords", response_model=VoiceHotwordsResponse)
async def get_voice_hotwords() -> VoiceHotwordsResponse:
    profile = profile_data()
    hotwords = await asr_hotwords_for_profile(profile)
    return VoiceHotwordsResponse(hotwords=hotwords, count=len(hotwords), generated=deepseek_client.configured)


@app.post("/api/voice/asr", response_model=VoiceAsrResponse)
async def voice_asr(file: UploadFile = File(...)) -> VoiceAsrResponse:
    try:
        audio = await file.read()
        profile = profile_data()
        hotwords = await asr_hotwords_for_profile(profile)
        text = await transcribe_audio(audio, file.content_type or "audio/webm")
        text = await correct_asr_transcript(text, hotwords)
        return VoiceAsrResponse(text=text, configured=True)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/voice/asr/stream")
async def voice_asr_stream(file: UploadFile = File(...)) -> StreamingResponse:
    try:
        audio = await file.read()
        profile = profile_data()
        hotwords = await asr_hotwords_for_profile(profile)
        text = await collect_text_stream(stream_transcribe_audio(audio, file.content_type or "audio/wav"))
        text = await correct_asr_transcript(text, hotwords)
        return StreamingResponse(iter_text_once(text), media_type="text/plain; charset=utf-8")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


async def collect_text_stream(stream) -> str:
    parts = []
    async for chunk in stream:
        if isinstance(chunk, bytes):
            parts.append(chunk.decode("utf-8", errors="replace"))
        else:
            parts.append(str(chunk))
    return "".join(parts)


async def iter_text_once(text: str):
    yield text.encode("utf-8")


@app.post("/api/voice/tts")
async def voice_tts(request: VoiceTtsRequest) -> Response:
    try:
        audio, media_type = await synthesize_speech(request.text, request.referenceAudioDataUrl)
        return Response(content=audio, media_type=media_type)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/voice/tts/stream")
async def voice_tts_stream(request: VoiceTtsRequest) -> StreamingResponse:
    try:
        has_reference_voice = bool(request.referenceAudioDataUrl.strip()) or voice_clone_enabled()
        audio_stream = stream_synthesize_speech(request.text, request.referenceAudioDataUrl)
        media_type = "audio/wav" if has_reference_voice else "audio/pcm;rate=24000"
        return StreamingResponse(audio_stream, media_type=media_type)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/resume/export", response_model=ExportResponse)
async def export_resume(request: ExportRequest) -> ExportResponse:
    profile = profile_data()
    export_config = read_resume_export_config(settings.resolved_resume_export_config_path)
    mode = active_resume_mode(export_config, request.mode)
    template = active_resume_template(export_config, request.template)
    base_markdown = local_match_resume(profile, request.jd, request.direction, mode)
    configured = deepseek_client.configured
    metadata_note = resume_metadata_note(profile, mode)
    note = f"未配置 LLM API Key，已按“{mode['label']} / {template['label']}”生成本地保守匹配版本。{metadata_note}"

    if configured and request.jd.strip():
        system_prompt = (
            "你是严谨的简历生成助手。只能基于候选人资料优化表达、排序和重点，"
            "不得新增未经资料支持的经历、成果、数字、技能、公司或时间。"
            "必须输出 Markdown 简历，不要代码围栏。"
            "基础信息必须完整保留：姓名、职位、电话、邮箱、所在地、学历；资料中有出生日期时必须保留出生日期。"
            "联系方式和出生日期只能来自候选人资料，不能猜测。"
            "所有内容要适合招聘方阅读，优先保留与 JD 高相关的量化成果和技术证据。"
        )
        context = knowledge_context(profile)
        birth = meta_value(profile["meta"], "birth") or "资料未写明"
        prompt = (
            f"候选人资料：\n{context}\n\n"
            f"岗位 JD：\n{request.jd}\n\n"
            f"目标方向：{request.direction}\n"
            f"篇幅策略：{mode['label']}；目标页数：{mode['targetPages'] or '不限'}；"
            f"核心能力最多 {mode['skillCount']} 条；每段经历最多 {mode['experienceBullets']} 条；"
            f"项目最多 {mode['projectCount']} 个，每项目最多 {mode['projectBullets']} 条。\n"
            f"模板策略：{template['label']}；{template.get('llmInstruction', '')}\n"
            f"必须保留的基础信息：姓名={profile['meta'].get('name', '')}；电话={meta_value(profile['meta'], 'phone')}；"
            f"邮箱={meta_value(profile['meta'], 'email')}；所在地={meta_value(profile['meta'], 'location')}；"
            f"学历={meta_value(profile['meta'], 'education')}；出生日期={birth}；"
            f"出生日期导出开关={'开启' if mode.get('includeBirth', True) else '关闭'}。\n"
            f"基础简历草稿：\n{base_markdown}"
        )
        try:
            base_markdown = await deepseek_client.chat(
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                purpose="export",
            )
            base_markdown = compact_resume_markdown(base_markdown, mode)
            note = f"已基于 {deepseek_client.last_provider_label} 和资料约束生成匹配简历，并按“{mode['label']} / {template['label']}”策略控制篇幅与版式。{metadata_note}"
        except Exception as exc:  # noqa: BLE001
            configured = False
            note = f"{summarize_llm_error(exc)} 已按“{mode['label']} / {template['label']}”生成本地保守匹配版本。{metadata_note}"

    base_markdown = ensure_resume_header_metadata(base_markdown, profile, mode)
    avatar_data = resume_avatar_data_url() if mode.get("includeAvatar") and template.get("showAvatar") else ""
    html = markdown_to_resume_html(
        base_markdown,
        template=template,
        mode=mode,
        avatar_data_url=avatar_data,
        branding=export_config.get("branding", {}),
    )
    return ExportResponse(
        html=html,
        markdown=base_markdown,
        filename=f"wangtao-{template['key']}-{mode['key']}.html",
        configured=configured,
        note=note,
        provider=deepseek_client.last_provider_label if configured else deepseek_client.provider_label,
    )


@app.post("/api/resume/export/html", response_class=HTMLResponse)
async def export_resume_html(request: ExportRequest) -> str:
    result = await export_resume(request)
    return result.html


@app.post("/api/admin/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest) -> AdminLoginResponse:
    if settings.showcase_mode:
        if has_valid_admin_password(request.password):
            return AdminLoginResponse(
                ok=True,
                message="已切换到管理员模式：当前保存会真实写入线上内容。",
                showcaseMode=True,
                adminMode=True,
            )
        return AdminLoginResponse(
            ok=True,
            message="当前为展示项目模式：已免验证进入后台，可体验生成与预览；如需保存，请切换到管理员模式并输入管理密码。",
            showcaseMode=True,
            adminMode=False,
        )
    if not secrets.compare_digest(request.password, settings.admin_password):
        raise HTTPException(status_code=401, detail="管理密码不正确。")
    return AdminLoginResponse(ok=True, message="已进入作者后台。", showcaseMode=False, adminMode=True)


@app.get("/api/admin/mode", response_model=AdminModeResponse)
async def get_admin_mode() -> AdminModeResponse:
    message = ""
    if settings.showcase_mode:
        message = "当前为展示项目模式：后台免验证，可体验生成与预览；输入管理密码后可切换到管理员模式进行保存。"
    return AdminModeResponse(showcaseMode=settings.showcase_mode, message=message)


@app.get("/api/admin/markdown", response_model=MarkdownDocumentResponse)
async def get_markdown(_: None = Depends(verify_admin_password)) -> MarkdownDocumentResponse:
    path = settings.resolved_content_path
    profile = profile_data()
    return MarkdownDocumentResponse(
        path=str(path),
        markdown=read_markdown(path),
        sections=len(profile["sections"]),
    )


@app.put("/api/admin/markdown", response_model=ReindexResponse)
async def save_markdown(
    request: MarkdownSaveRequest,
    admin_password: str = Depends(verify_admin_password),
) -> ReindexResponse:
    require_persistence_enabled(admin_password)
    write_markdown(settings.resolved_content_path, request.markdown)
    clear_briefing_cache()
    profile = profile_data()
    return ReindexResponse(sections=len(profile["sections"]), message="Markdown 已保存，资料索引已刷新。")


@app.post("/api/admin/ai/edit", response_model=AdminAiEditResponse)
async def ai_edit_markdown(
    request: AdminAiEditRequest,
    _: None = Depends(verify_admin_password),
) -> AdminAiEditResponse:
    if not deepseek_client.configured:
        return AdminAiEditResponse(
            markdown=request.markdown,
            note="后端未配置 LLM API Key，无法执行 AI 修改。",
            configured=False,
            provider=deepseek_client.provider_label,
        )

    system_prompt = (
        "你是作者后台的 Markdown 内容编辑助手。只能编辑用户提供的 Markdown，"
        "不得新增没有事实依据的经历、公司、时间、数字、奖项或成果。"
        "必须保留 YAML frontmatter 的 --- 边界和已有事实。"
        "如果用户要求美化表达，只能重排、精简、补充基于原文可直接推断的表达。"
        "只输出完整 Markdown，不要解释，不要代码围栏。"
    )
    prompt = f"修改指令：\n{request.instruction}\n\n当前 Markdown：\n{request.markdown}"
    try:
        edited = await deepseek_client.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]
        )
    except Exception as exc:  # noqa: BLE001
        return AdminAiEditResponse(
            markdown=request.markdown,
            note=f"{summarize_llm_error(exc)} 已保留当前 Markdown，未应用 AI 修改。",
            configured=False,
            provider=deepseek_client.provider_label,
        )
    return AdminAiEditResponse(
        markdown=strip_markdown_fence(edited),
        note=f"已通过 {deepseek_client.last_provider_label} 生成 Markdown 草稿。请预览确认后再保存。",
        configured=True,
        provider=deepseek_client.last_provider_label,
    )


@app.post("/api/admin/preview", response_model=BriefingResponse)
async def preview_briefing(
    request: AdminPreviewRequest,
    _: None = Depends(verify_admin_password),
) -> BriefingResponse:
    profile = parse_profile_markdown(request.markdown)
    briefing = await generate_briefing(profile, use_override=False)
    return BriefingResponse(**briefing)


@app.get("/api/admin/home-briefing", response_model=AdminHomeBriefingResponse)
async def get_home_briefing(_: None = Depends(verify_admin_password)) -> AdminHomeBriefingResponse:
    profile = profile_data()
    saved = read_briefing_override(settings.resolved_home_briefing_path, profile)
    briefing = saved or await generate_briefing(profile)
    return AdminHomeBriefingResponse(
        briefing=briefing,
        saved=saved is not None,
        aiConfigured=deepseek_client.configured,
        aiProvider=deepseek_client.provider_label,
        aiModel=briefing.get("generationMeta", {}).get("model") or deepseek_client.model_for("chat"),
    )


@app.post("/api/admin/home-briefing/ai", response_model=AdminHomeBriefingResponse)
async def ai_edit_home_briefing(
    request: AdminHomeBriefingEditRequest,
    _: None = Depends(verify_admin_password),
) -> AdminHomeBriefingResponse:
    profile = profile_data()
    if not deepseek_client.configured:
        return AdminHomeBriefingResponse(
            briefing=request.briefing,
            saved=False,
            aiConfigured=False,
            aiProvider=deepseek_client.provider_label,
            aiModel=deepseek_client.model_for("chat"),
        )

    briefing = await adjust_briefing_with_ai(profile, request.briefing, request.instruction)
    return AdminHomeBriefingResponse(
        briefing=briefing,
        saved=False,
        aiConfigured=True,
        aiProvider=deepseek_client.last_provider_label,
        aiModel=deepseek_client.last_model or deepseek_client.model_for("chat"),
    )


@app.put("/api/admin/home-briefing", response_model=AdminHomeBriefingResponse)
async def save_home_briefing(
    request: AdminHomeBriefingSaveRequest,
    admin_password: str = Depends(verify_admin_password),
) -> AdminHomeBriefingResponse:
    require_persistence_enabled(admin_password)
    profile = profile_data()
    normalized = await normalize_home_briefing(profile, request.briefing)
    write_briefing_override(settings.resolved_home_briefing_path, normalized)
    clear_briefing_cache()
    return AdminHomeBriefingResponse(
        briefing=normalized,
        saved=True,
        aiConfigured=deepseek_client.configured,
        aiProvider=deepseek_client.provider_label,
        aiModel=normalized.get("generationMeta", {}).get("model") or deepseek_client.model_for("chat"),
    )


@app.get("/api/admin/site-style", response_model=SiteStyleResponse)
async def get_admin_site_style(_: None = Depends(verify_admin_password)) -> SiteStyleResponse:
    return SiteStyleResponse(**site_style_response(settings.resolved_site_style_path))


@app.put("/api/admin/site-style", response_model=SiteStyleResponse)
async def save_admin_site_style(
    request: SiteStyleSaveRequest,
    admin_password: str = Depends(verify_admin_password),
) -> SiteStyleResponse:
    require_persistence_enabled(admin_password)
    write_site_style(settings.resolved_site_style_path, {"activeKey": request.activeKey})
    return SiteStyleResponse(**site_style_response(settings.resolved_site_style_path))


@app.get("/api/admin/resume-export-config", response_model=ResumeExportConfigResponse)
async def get_admin_resume_export_config(_: None = Depends(verify_admin_password)) -> ResumeExportConfigResponse:
    config = read_resume_export_config(settings.resolved_resume_export_config_path)
    return ResumeExportConfigResponse(**config)


@app.put("/api/admin/resume-export-config", response_model=ResumeExportConfigResponse)
async def save_admin_resume_export_config(
    request: ResumeExportConfigSaveRequest,
    admin_password: str = Depends(verify_admin_password),
) -> ResumeExportConfigResponse:
    require_persistence_enabled(admin_password)
    config = write_resume_export_config(settings.resolved_resume_export_config_path, request.model_dump())
    return ResumeExportConfigResponse(**config)


@app.get("/api/admin/resume-avatar", response_model=ResumeAvatarResponse)
async def get_admin_resume_avatar(_: None = Depends(verify_admin_password)) -> ResumeAvatarResponse:
    return ResumeAvatarResponse(**read_resume_avatar())


@app.put("/api/admin/resume-avatar", response_model=ResumeAvatarResponse)
async def save_admin_resume_avatar(
    file: UploadFile = File(...),
    admin_password: str = Depends(verify_admin_password),
) -> ResumeAvatarResponse:
    require_persistence_enabled(admin_password)
    try:
        image = await file.read()
        result = save_resume_avatar(image, file.content_type or "", file.filename or "")
        return ResumeAvatarResponse(**result)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/admin/resume-avatar", response_model=ResumeAvatarResponse)
async def delete_admin_resume_avatar(admin_password: str = Depends(verify_admin_password)) -> ResumeAvatarResponse:
    require_persistence_enabled(admin_password)
    return ResumeAvatarResponse(**delete_resume_avatar())


@app.get("/api/admin/voice-clone/reference", response_model=VoiceCloneReferenceResponse)
async def get_admin_voice_clone_reference(_: None = Depends(verify_admin_password)) -> VoiceCloneReferenceResponse:
    return VoiceCloneReferenceResponse(**read_voice_clone_reference())


@app.put("/api/admin/voice-clone/reference", response_model=VoiceCloneReferenceResponse)
async def save_admin_voice_clone_reference(
    file: UploadFile = File(...),
    admin_password: str = Depends(verify_admin_password),
) -> VoiceCloneReferenceResponse:
    require_persistence_enabled(admin_password)
    try:
        audio = await file.read()
        result = save_voice_clone_reference(audio, file.content_type or "", file.filename or "")
        return VoiceCloneReferenceResponse(**result)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/admin/voice-clone/reference", response_model=VoiceCloneReferenceResponse)
async def delete_admin_voice_clone_reference(admin_password: str = Depends(verify_admin_password)) -> VoiceCloneReferenceResponse:
    require_persistence_enabled(admin_password)
    return VoiceCloneReferenceResponse(**delete_voice_clone_reference())


@app.post("/api/admin/import")
async def import_document(
    file: UploadFile = File(...),
    _: None = Depends(verify_admin_password),
) -> dict:
    try:
        markdown = await upload_to_markdown(file)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"filename": file.filename, "markdown": markdown}


@app.post("/api/admin/reindex", response_model=ReindexResponse)
async def reindex(_: None = Depends(verify_admin_password)) -> ReindexResponse:
    clear_briefing_cache()
    profile = profile_data()
    return ReindexResponse(sections=len(profile["sections"]), message="资料索引已重建。")


@app.get("/{path:path}", include_in_schema=False)
async def serve_frontend(path: str) -> FileResponse:
    static_path = settings.resolved_static_dir
    if not static_path:
        raise HTTPException(status_code=404, detail="Not Found")
    index_path = static_path / "index.html"
    requested_path = (static_path / path).resolve()
    if requested_path.is_file() and str(requested_path).startswith(str(static_path)):
        return FileResponse(requested_path)
    if index_path.exists():
        return FileResponse(index_path)
    raise HTTPException(status_code=404, detail="Not Found")


async def normalize_home_briefing(profile: dict, briefing: dict) -> dict:
    normalized = merge_briefing(local_briefing(profile), briefing)
    normalized["generated"] = bool(briefing.get("generated", True))
    normalized["aiConfigured"] = deepseek_client.configured
    normalized["aiProvider"] = briefing.get("aiProvider") or deepseek_client.provider_label
    source_hash = profile_source_hash(profile)
    meta = briefing.get("generationMeta") or generation_meta(
        status="saved",
        generated=normalized["generated"],
        provider=normalized["aiProvider"],
        model=deepseek_client.model_for("chat"),
        source_hash=source_hash,
    )
    meta["status"] = "saved"
    meta["cached"] = False
    meta["savedAt"] = datetime.now(timezone.utc).isoformat()
    meta["sourceHash"] = source_hash
    normalized["generationMeta"] = meta
    normalized["sourceHash"] = source_hash
    return normalized


def strip_markdown_fence(text: str) -> str:
    cleaned = text.strip()
    if not cleaned.startswith("```"):
        return cleaned

    lines = cleaned.splitlines()
    if lines and lines[0].startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


def local_answer(question: str, profile: dict) -> str:
    q = question.lower()
    meta = profile["meta"]
    name = meta.get("name", "候选人")
    highlights = "；".join(
        f"{item['title']}：{item['body']}" if item["body"] else item["title"]
        for item in profile["highlights"][:4]
    )
    if any(token in q for token in ["语音", "ai", "agent", "llm", "智能"]):
        return (
            f"适合。{name}的主线集中在语音智能、AI Agent、ASR/TTS/KWS 和工程落地。"
            "在欧瑞博的语音 Agent 项目里，资料记录了 P95 端到端首帧语音延迟从 10s 降到 1s、"
            "链路成本降低 95%、ASR/TTS 成本降低 60% 等结果。需要我展开技术难点吗？"
            "\n\n依据：工作经历 / 项目详情。"
        )
    return (
        f"{name}的核心能力可以概括为：{highlights}。"
        "这是基于本地资料的保守回答，可以继续追问某段经历或某个项目。"
        "\n\n依据：profile.md / 核心能力 / 项目详情。"
    )


def resume_metadata_note(profile: dict, mode: dict) -> str:
    if not mode.get("includeBirth", True):
        return " 出生日期已按当前篇幅模式配置隐藏。"
    if meta_value(profile.get("meta", {}), "birth"):
        return " 已按资料保留出生日期。"
    return " 资料中未写明出生日期，导出时不会猜测补充。"
