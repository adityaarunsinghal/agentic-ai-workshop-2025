"""Configuration for Learning Agent."""

from pathlib import Path
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class VectorConfig(BaseModel):
    """Vector database configuration."""
    collection_name: str = "learning_agent_memory"


class Settings(BaseSettings):
    """Learning agent settings."""

    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent.parent / "data" / "learning-agent")
    vector: VectorConfig = Field(default_factory=VectorConfig)

    class Config:
        env_prefix = "LEARNING_AGENT_"


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()
