from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    openrouter_api_key: str = Field(default="", env="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL"
    )
    # Any model slug listed on openrouter.ai/models
    llm_model: str = Field(
        default="anthropic/claude-sonnet-4-5", env="LLM_MODEL"
    )
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    output_dir: str = Field(default="/app/outputs", env="OUTPUT_DIR")
    backend_host: str = Field(default="0.0.0.0", env="BACKEND_HOST")
    backend_port: int = Field(default=8000, env="BACKEND_PORT")
    arxiv_max_results: int = Field(default=50, env="ARXIV_MAX_RESULTS")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields like BACKEND_URL (used by frontend)


settings = Settings()
