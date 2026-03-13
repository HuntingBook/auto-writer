from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _read_file_or_default(path: str | None, default: str | None = None) -> str | None:
    if not path:
        return default
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except Exception:
        return default


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
        env_prefix="AUTO_WRITER_",
    )

    app_env: str = "dev"
    secret_key: str | None = None
    secret_key_file: str | None = None

    database_url: str
    redis_url: str
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_embedding_model: str = "deepseek-embedding-v2"

    artifacts_dir: str = "/data/artifacts"
    skip_migrations: bool = False

    def get_secret_key(self) -> str:
        key = _read_file_or_default(self.secret_key_file)
        if key:
            return key
        if self.secret_key:
            return self.secret_key
        raise ValueError(
            "Secret key must be provided via AUTO_WRITER_SECRET_KEY "
            "or AUTO_WRITER_SECRET_KEY_FILE environment variable"
        )


settings = Settings()
