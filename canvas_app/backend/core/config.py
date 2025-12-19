"""Application configuration."""
from pathlib import Path
from typing import List

try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback if pydantic-settings not installed
    from pydantic import BaseModel as BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    app_name: str = "NormCode Canvas"
    debug: bool = True
    
    # CORS settings
    cors_origins: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    # Paths - relative to project root
    @property
    def project_root(self) -> Path:
        return Path(__file__).parent.parent.parent.parent
    
    @property
    def infra_path(self) -> Path:
        return self.project_root / "infra"
    
    # Default LLM settings
    default_llm_model: str = "demo"
    
    class Config:
        env_file = ".env"


settings = Settings()
