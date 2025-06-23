# agents/bringo_chef_ai_assistant/shared/config.py
# Minimal configuration management for BringoChef AI
# Pure AI-driven approach - no hardcoded translations or assumptions

import os
from typing import Dict
from dataclasses import dataclass


@dataclass
class BringoChefSettings:
    """
    Minimal, professional configuration for BringoChef AI system.
    Everything else is handled dynamically by AI agents.
    """
    
    # AI Model Configuration
    text_model: str = "gemini-2.5-flash"
    image_model: str = "imagen-3.0-generate-002"
    
    # Google Cloud Configuration  
    project_id: str = "formare-ai"
    location: str = "europe-west4"
    
    # Bringo.ro Integration
    bringo_base_url: str = "https://www.bringo.ro"
    bringo_store: str = "carrefour_park_lake"
    max_products_per_search: int = 8
    request_timeout: int = 15
    
    # AI Parameters
    conservative_temperature: float = 0.1
    balanced_temperature: float = 0.3
    creative_temperature: float = 0.7
    max_tokens: int = 4000
    
    # Performance Settings
    max_concurrent_requests: int = 5
    max_retry_attempts: int = 3
    min_confidence_threshold: float = 0.7
    
    # Professional Request Headers
    request_headers: Dict[str, str] = None
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    
    def __post_init__(self):
        """Initialize after creation"""
        if self.request_headers is None:
            self.request_headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; BringoChef/2.0)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ro-RO,ro;q=0.9,en;q=0.8',
                'Connection': 'keep-alive'
            }
        
        # Override with environment variables if present
        self.text_model = os.getenv("BRINGO_TEXT_MODEL", self.text_model)
        self.image_model = os.getenv("BRINGO_IMAGE_MODEL", self.image_model)
        self.project_id = os.getenv("BRINGO_PROJECT_ID", self.project_id)
        self.location = os.getenv("BRINGO_LOCATION", self.location)
        self.bringo_base_url = os.getenv("BRINGO_BASE_URL", self.bringo_base_url)
        self.bringo_store = os.getenv("BRINGO_STORE", self.bringo_store)
        
        # Override numeric settings
        if os.getenv("BRINGO_MAX_PRODUCTS_PER_SEARCH"):
            self.max_products_per_search = int(os.getenv("BRINGO_MAX_PRODUCTS_PER_SEARCH"))
        if os.getenv("BRINGO_REQUEST_TIMEOUT"):
            self.request_timeout = int(os.getenv("BRINGO_REQUEST_TIMEOUT"))
        if os.getenv("BRINGO_MAX_CONCURRENT_REQUESTS"):
            self.max_concurrent_requests = int(os.getenv("BRINGO_MAX_CONCURRENT_REQUESTS"))


# Global settings instance
settings = BringoChefSettings()