from __future__ import annotations

import secrets

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .briefing import clear_briefing_cache, generate_briefing
from .config import settings
from .content import knowledge_context, load_profile, parse_profile_markdown, read_markdown, write_markdown
from .deepseek import deepseek_client
from .exporter import local_match_resume, markdown_to_resume_html
from .importer import upload_to_markdown
from .schemas import (
    AdminAiEditRequest,
    AdminAiEditResponse,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminPreviewRequest,
    BriefingResponse,
    ChatRequest,
    ChatResponse,
    ExportRequest,
    ExportResponse,
    MarkdownDocumentResponse,
    MarkdownSaveRequest,
    ReindexResponse,
)

app = FastAPI(title="AI Profile Page API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def profile_data() -> dict:
    return load_profile(settings.resolved_content_path)


def verify_admin_password(x_admin_password: str = Header(default="")) -> None:
    if not secrets.compare_digest(x_admin_password, settings.admin_password):
        raise HTTPException(status_code=401, detail="管理密码不正确。")


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


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    profile = profile_data()
    context = knowledge_context(profile)
    sources = ["profile.md", "项目详情", "代码仓摘要"]
    system_prompt = (
        "你是王涛个人介绍页的职业经历讲解员。只能根据给定资料回答，"
        "不要编造经历、成果、公司、时间或数字。回答要面向招聘方，结论清晰，"
        "并在末尾用“依据：”列出资料来源。"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"资料：\n{context}\n\n问题：{request.question}"},
    ]

    if deepseek_client.configured:
        answer = await deepseek_client.chat(messages, settings.deepseek_chat_model)
        return ChatResponse(answer=answer, sources=sources, configured=True)

    fallback = local_answer(request.question, profile)
    return ChatResponse(answer=fallback, sources=sources, configured=False)


@app.post("/api/resume/export", response_model=ExportResponse)
async def export_resume(request: ExportRequest) -> ExportResponse:
    profile = profile_data()
    base_markdown = local_match_resume(profile, request.jd, request.direction)
    configured = deepseek_client.configured
    note = "未配置 DeepSeek API Key，已使用本地资料生成保守匹配版本。"

    if configured and request.jd.strip():
        system_prompt = (
            "你是简历改写助手。只能基于候选人资料优化表达、排序和重点，"
            "不得新增未经资料支持的经历、成果、数字或技能。输出 Markdown 简历。"
        )
        context = knowledge_context(profile)
        prompt = (
            f"候选人资料：\n{context}\n\n"
            f"岗位 JD：\n{request.jd}\n\n"
            f"目标方向：{request.direction}\n"
            f"基础简历草稿：\n{base_markdown}"
        )
        base_markdown = await deepseek_client.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            settings.deepseek_export_model,
        )
        note = "已基于 DeepSeek 和资料约束生成匹配简历。"

    html = markdown_to_resume_html(base_markdown, request.template)
    return ExportResponse(
        html=html,
        markdown=base_markdown,
        filename=f"wangtao-{request.template}.html",
        configured=configured,
        note=note,
    )


@app.post("/api/resume/export/html", response_class=HTMLResponse)
async def export_resume_html(request: ExportRequest) -> str:
    result = await export_resume(request)
    return result.html


@app.post("/api/admin/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest) -> AdminLoginResponse:
    if not secrets.compare_digest(request.password, settings.admin_password):
        raise HTTPException(status_code=401, detail="管理密码不正确。")
    return AdminLoginResponse(ok=True, message="已进入作者后台。")


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
    _: None = Depends(verify_admin_password),
) -> ReindexResponse:
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
            note="后端未配置 DeepSeek API Key，无法执行 AI 修改。",
            configured=False,
        )

    system_prompt = (
        "你是作者后台的 Markdown 内容编辑助手。只能编辑用户提供的 Markdown，"
        "不得新增没有事实依据的经历、公司、时间、数字、奖项或成果。"
        "必须保留 YAML frontmatter 的 --- 边界和已有事实。"
        "如果用户要求美化表达，只能重排、精简、补充基于原文可直接推断的表达。"
        "只输出完整 Markdown，不要解释，不要代码围栏。"
    )
    prompt = f"修改指令：\n{request.instruction}\n\n当前 Markdown：\n{request.markdown}"
    edited = await deepseek_client.chat(
        [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        settings.deepseek_chat_model,
    )
    return AdminAiEditResponse(
        markdown=strip_markdown_fence(edited),
        note="已生成 Markdown 草稿。请预览确认后再保存。",
        configured=True,
    )


@app.post("/api/admin/preview", response_model=BriefingResponse)
async def preview_briefing(
    request: AdminPreviewRequest,
    _: None = Depends(verify_admin_password),
) -> BriefingResponse:
    profile = parse_profile_markdown(request.markdown)
    briefing = await generate_briefing(profile)
    return BriefingResponse(**briefing)


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
            f"适合。{name}的经历集中在语音智能、AI Agent、ASR/TTS/KWS、"
            "LLM 微调、RAG 和工程落地。他在欧瑞博负责语音 Agent 和智能家居中控，"
            "并有 P95 首 token 从 10s 降到 1s、成本降低 95%、ASR/TTS 成本降低 60% 等结果。"
            "\n\n依据：profile.md、工作经历、项目详情。"
        )
    return (
        f"{name}的核心能力包括：{highlights}。"
        "当前后端未配置 DeepSeek API Key，因此这是基于本地资料的保守回答。"
        "\n\n依据：profile.md、核心能力、项目详情。"
    )
