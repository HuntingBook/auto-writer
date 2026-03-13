from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


def _read_file(path: str) -> str | None:
  if not path:
    return None
  try:
    return Path(path).read_text(encoding="utf-8").strip() or None
  except Exception:
    return None


class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_prefix="AUTO_WRITER_", env_file=".env", env_ignore_empty=True, extra="ignore")

  env: str = "dev"
  secret_key: str = "change-me"
  secret_key_file: str = ""

  database_url: str = ""
  redis_url: str = ""

  deepseek_api_key: str = ""
  deepseek_api_key_file: str = ""
  deepseek_base_url: str = "https://api.deepseek.com"
  deepseek_model: str = "deepseek-chat"
  deepseek_embedding_model: str = "deepseek-embedding-v2"

  artifacts_dir: str = "/data/artifacts"
  api_port: int = 8000
  skip_migrations: bool = False

  @property
  def effective_secret_key(self) -> str:
    return _read_file(self.secret_key_file) or self.secret_key

  @property
  def effective_deepseek_api_key(self) -> str | None:
    return _read_file(self.deepseek_api_key_file) or self.deepseek_api_key or None


settings = Settings()
