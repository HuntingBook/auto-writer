from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True, extra="ignore")

  app_env: str = "dev"
  app_secret_key: str = "change-me"

  database_url: str
  redis_url: str
  deepseek_base_url: str = "https://api.deepseek.com"
  deepseek_model: str = "deepseek-chat"
  deepseek_embedding_model: str = "deepseek-embedding-v2"

  artifacts_dir: str = "/data/artifacts"


settings = Settings()
