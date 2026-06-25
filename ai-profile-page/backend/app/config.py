from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_chat_model: str = "deepseek-v4-flash"
    deepseek_export_model: str = "deepseek-v4-pro"
    content_path: str = "../content/profile.md"
    frontend_origin: str = "http://127.0.0.1:4173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def resolved_content_path(self) -> Path:
        base_dir = Path(__file__).resolve().parents[1]
        return (base_dir / self.content_path).resolve()


settings = Settings()

