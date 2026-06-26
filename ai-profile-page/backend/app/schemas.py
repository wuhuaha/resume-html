from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    configured: bool


class BriefingResponse(BaseModel):
    meta: dict
    page: dict
    hero: dict
    fitSignals: list[dict]
    metrics: list[dict]
    capabilities: list[dict]
    timeline: list[dict]
    projects: list[dict]
    suggestedQuestions: list[str]
    generated: bool
    aiConfigured: bool


class ExportRequest(BaseModel):
    jd: str = ""
    template: str = "ats"
    direction: str = "语音 AI / 后端系统"


class ExportResponse(BaseModel):
    html: str
    markdown: str
    filename: str
    configured: bool
    note: str


class AdminLoginRequest(BaseModel):
    password: str = ""


class AdminLoginResponse(BaseModel):
    ok: bool
    message: str


class MarkdownDocumentResponse(BaseModel):
    path: str
    markdown: str
    sections: int


class MarkdownSaveRequest(BaseModel):
    markdown: str = Field(min_length=1)


class AdminAiEditRequest(BaseModel):
    markdown: str = Field(min_length=1)
    instruction: str = Field(min_length=1)


class AdminAiEditResponse(BaseModel):
    markdown: str
    note: str
    configured: bool


class AdminPreviewRequest(BaseModel):
    markdown: str = Field(min_length=1)


class AdminHomeBriefingResponse(BaseModel):
    briefing: dict
    saved: bool
    aiConfigured: bool


class AdminHomeBriefingSaveRequest(BaseModel):
    briefing: dict


class AdminHomeBriefingEditRequest(BaseModel):
    briefing: dict
    instruction: str = Field(min_length=1)


class ReindexResponse(BaseModel):
    sections: int
    message: str
