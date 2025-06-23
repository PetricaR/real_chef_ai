# agents/bringo_chef_ai_assistant/shared/__init__.py
# Shared foundation module for BringoChef AI - provides common utilities, models, and configuration
# This module centralizes all shared functionality to ensure consistency across all agents

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