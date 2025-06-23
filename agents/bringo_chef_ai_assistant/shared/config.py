# agents/shared/config.py
# Minimal configuration management for BringoChef AI
# Pure AI-driven approach - no hardcoded translations or assumptions

from pydantic import BaseSettings, Field
from typing import Dict


class BringoChefSettings(BaseSettings):
    """
    Minimal, professional configuration for BringoChef AI system.
    Everything else is handled dynamically by AI agents.
    """
    
    # AI Model Configuration
    text_model: str = Field(default="gemini-2.5-flash")
    image_model: str = Field(default="imagen-3.0-generate-002")
    
    # Google Cloud Configuration  
    project_id: str = Field(default="formare-ai")
    location: str = Field(default="europe-west4")
    
    # Bringo.ro Integration
    bringo_base_url: str = Field(default="https://www.bringo.ro")
    bringo_store: str = Field(default="carrefour_park_lake")
    max_products_per_search: int = Field(default=8)
    request_timeout: int = Field(default=15)
    
    # AI Parameters
    conservative_temperature: float = Field(default=0.1)
    balanced_temperature: float = Field(default=0.3)
    creative_temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=4000)
    
    # Performance Settings
    max_concurrent_requests: int = Field(default=5)
    max_retry_attempts: int = Field(default=3)
    min_confidence_threshold: float = Field(default=0.7)
    
    # Professional Request Headers
    request_headers: Dict[str, str] = Field(
        default={
            'User-Agent': 'Mozilla/5.0 (compatible; BringoChef/2.0)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ro-RO,ro;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }
    )
    
    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="%(asctime)s | %(name)s | %(levelname)s | %(message)s")
    
    class Config:
        env_file = ".env"
        env_prefix = "BRINGO_"


# Global settings instance
settings = BringoChefSettings()