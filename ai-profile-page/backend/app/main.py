from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .briefing import clear_briefing_cache, generate_briefing
from .config import settings
from .content import knowledge_context, load_profile
from .deepseek import deepseek_client
from .exporter import local_match_resume, markdown_to_resume_html
from .importer import upload_to_markdown
from .schemas import BriefingResponse, ChatRequest, ChatResponse, ExportRequest, ExportResponse, ReindexResponse

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


@app.post("/api/admin/import")
async def import_document(file: UploadFile = File(...)) -> dict:
    try:
        markdown = await upload_to_markdown(file)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"filename": file.filename, "markdown": markdown}


@app.post("/api/admin/reindex", response_model=ReindexResponse)
async def reindex() -> ReindexResponse:
    clear_briefing_cache()
    profile = profile_data()
    return ReindexResponse(sections=len(profile["sections"]), message="资料索引已重建。")


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
