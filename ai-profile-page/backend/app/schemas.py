from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1)
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    configured: bool


class VoiceConfigResponse(BaseModel):
    configured: bool
    provider: str = "xiaomi-mimo"
    asrModel: str = ""
    ttsModel: str = ""
    ttsVoice: str = ""
    voiceCloneEnabled: bool = False
    voiceCloneModel: str = ""
    hotwordCount: int = 0


class VoiceHotwordsResponse(BaseModel):
    hotwords: list[str]
    count: int
    generated: bool


class VoiceAsrResponse(BaseModel):
    text: str
    configured: bool


class VoiceTtsRequest(BaseModel):
    text: str = Field(min_length=1)
    referenceAudioDataUrl: str = ""


class VoiceCloneReferenceResponse(BaseModel):
    enabled: bool
    filename: str = ""
    contentType: str = ""
    size: int = 0
    updatedAt: str = ""
    message: str = ""


class ResumeAvatarResponse(BaseModel):
    enabled: bool
    filename: str = ""
    contentType: str = ""
    size: int = 0
    updatedAt: str = ""
    message: str = ""


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
    template: str = ""
    direction: str = "语音 AI / 后端系统"
    mode: str = ""


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
    showcaseMode: bool = False


class AdminModeResponse(BaseModel):
    showcaseMode: bool = False
    message: str = ""


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


class SiteStyleSaveRequest(BaseModel):
    activeKey: str = Field(min_length=1)


class SiteStyleResponse(BaseModel):
    activeKey: str
    activePreset: dict
    presets: list[dict]


class ResumeExportConfigResponse(BaseModel):
    activeMode: str
    activeTemplate: str = ""
    modes: dict
    templates: dict = {}
    sectionOrder: list[str]
    branding: dict = {}


class ResumeExportConfigSaveRequest(BaseModel):
    activeMode: str = ""
    activeTemplate: str = ""
    modes: dict = {}
    templates: dict = {}
    sectionOrder: list[str] = []
    branding: dict = {}


class ReindexResponse(BaseModel):
    sections: int
    message: str
