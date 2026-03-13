import os
import logging
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


def read_env_or_file(env_prefix: str, name: str, default: str = "") -> str:
    full_name = f"{env_prefix}{name}"
    value = os.environ.get(full_name, "").strip()
    if value:
        return value

    file_name = f"{full_name}_FILE"
    file_path = os.environ.get(file_name, "").strip()
    if file_path:
        try:
            content = Path(file_path).read_text(encoding="utf-8").strip()
            if content:
                return content
            logger.warning(f"{file_name} file is empty: {file_path}")
        except FileNotFoundError:
            logger.warning(f"{file_name} file not found: {file_path}")
        except Exception as e:
            logger.warning(f"{file_name} read error: {e}")

    return default


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

    app_env: str = read_env_or_file("AUTO_WRITER_", "APP_ENV", "dev")
    app_secret_key: str = read_env_or_file("AUTO_WRITER_", "SECRET_KEY", "change-me")

    database_url: str = read_env_or_file("AUTO_WRITER_", "DATABASE_URL", "")
    redis_url: str = read_env_or_file("AUTO_WRITER_", "REDIS_URL", "")

    deepseek_base_url: str = read_env_or_file("AUTO_WRITER_", "DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = read_env_or_file("AUTO_WRITER_", "DEEPSEEK_MODEL", "deepseek-chat")
    deepseek_embedding_model: str = read_env_or_file("AUTO_WRITER_", "DEEPSEEK_EMBEDDING_MODEL", "deepseek-embedding-v2")
    deepseek_api_key: str = read_env_or_file("AUTO_WRITER_", "DEEPSEEK_API_KEY", "")

    artifacts_dir: str = read_env_or_file("AUTO_WRITER_", "ARTIFACTS_DIR", "/data/artifacts")


settings = Settings()
