from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # CORS settings
    allow_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173", 
        "http://192.168.113.18:3000"
    ]
    allow_credentials: bool = True
    allow_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers: List[str] = ["*"]
    expose_headers: List[str] = ["*"]
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Data settings
    data_dir: str = "data"
    nodes_file: str = "nodes.json"
    edges_file: str = "edges.json"
    
    # Node type validation
    valid_node_types: List[str] = [
        'red', 'pink', 'purple', 'blue', 'teal', 
        'green', 'yellow', 'orange', 'brown', 'grey'
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings() 