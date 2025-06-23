# agents/shared/__init__.py
# Shared foundation module for BringoChef AI - provides common utilities, models, and configuration
# Pure AI-driven approach with async/threading support for optimal performance

from .config import settings
from .models import *
from .client import AsyncAIClient, get_ai_client
from .responses import StandardResponse, create_success_response, create_error_response

__all__ = [
    # Configuration
    'settings',
    
    # Models
    'LanguageInfo',
    'CulturalAnalysis', 
    'CookingParameters',
    'IngredientValidation',
    'ProductSearchResult',
    'RecipeData',
    'TutorialData',
    'CulturalAnalysisResponse',
    'ParameterExtractionResponse', 
    'IngredientValidationResponse',
    'ProductSearchResponse',
    'RecipeCreationResponse',
    'TutorialResponse',
    'ConversationResponse',
    
    # Client utilities
    'AsyncAIClient',
    'get_ai_client',
    
    # Response utilities
    'StandardResponse',
    'create_success_response',
    'create_error_response'
]