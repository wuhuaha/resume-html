from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    llm_provider: str = "auto"
    codex_api_key: str = ""
    openai_api_key: str = ""
    codex_base_url: str = "https://api.openai.com/v1"
    codex_chat_model: str = "gpt-5.5"
    codex_export_model: str = "gpt-5.5"
    codex_reasoning_effort: str = "xhigh"
    codex_endpoint: str = "responses"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_chat_model: str = "deepseek-v4-flash"
    deepseek_export_model: str = "deepseek-v4-pro"
    xiaomi_mimo_api_key: str = ""
    xiaomi_mimo_base_url: str = "https://api.xiaomimimo.com/v1/chat/completions"
    xiaomi_mimo_asr_model: str = "mimo-v2.5-asr"
    xiaomi_mimo_tts_model: str = "mimo-v2.5-tts"
    xiaomi_mimo_tts_voiceclone_model: str = "mimo-v2.5-tts-voiceclone"
    xiaomi_mimo_tts_voice: str = "冰糖"
    xiaomi_mimo_tts_style: str = "自然、清晰、专业，语速适中，适合向招聘方面试讲解。"
    voice_clone_reference_path: str = "../storage/voice_clone_reference"
    showcase_mode: bool = False
    admin_password: str = "admin"
    content_path: str = "../content/profile.md"
    home_briefing_path: str = "../content/home_briefing.json"
    site_style_path: str = "../content/site_style.json"
    resume_export_config_path: str = "../content/resume_export_config.json"
    resume_avatar_path: str = "../storage/resume_avatar"
    project_github_url: str = "https://github.com/wuhuaha/resume-html"
    static_dir: str = ""
    frontend_origin: str = "http://127.0.0.1:4173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def resolved_content_path(self) -> Path:
        base_dir = Path(__file__).resolve().parents[1]
        return (base_dir / self.content_path).resolve()

    @property
    def resolved_home_briefing_path(self) -> Path:
        base_dir = Path(__file__).resolve().parents[1]
        return (base_dir / self.home_briefing_path).resolve()

    @property
    def resolved_site_style_path(self) -> Path:
        base_dir = Path(__file__).resolve().parents[1]
        return (base_dir / self.site_style_path).resolve()

    @property
    def resolved_resume_export_config_path(self) -> Path:
        base_dir = Path(__file__).resolve().parents[1]
        return (base_dir / self.resume_export_config_path).resolve()

    @property
    def resolved_resume_avatar_path(self) -> Path:
        base_dir = Path(__file__).resolve().parents[1]
        return (base_dir / self.resume_avatar_path).resolve()

    @property
    def resolved_static_dir(self) -> Path | None:
        if not self.static_dir:
            return None
        base_dir = Path(__file__).resolve().parents[1]
        return (base_dir / self.static_dir).resolve()

    @property
    def resolved_voice_clone_reference_path(self) -> Path:
        base_dir = Path(__file__).resolve().parents[1]
        return (base_dir / self.voice_clone_reference_path).resolve()


settings = Settings()
