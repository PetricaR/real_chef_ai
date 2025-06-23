# agents/shared/models.py
# Pydantic models for BringoChef AI - type-safe data structures for inter-agent communication
# Professional, flexible models without hardcoded assumptions

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class StatusType(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PROCESSING = "processing"


# Core Data Models

class LanguageInfo(BaseModel):
    """Language detection information"""
    code: str = Field(..., description="Language code (e.g., 'ro', 'en')")
    name: str = Field(..., description="Language name")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence")
    dialect: Optional[str] = Field(None, description="Regional dialect if detected")


class LocationInfo(BaseModel):
    """Geographic location information"""
    country: str = Field(..., description="Detected country")
    region: Optional[str] = Field(None, description="Specific region if detected")
    confidence: float = Field(..., ge=0, le=1, description="Location confidence")


class CulturalIndicators(BaseModel):
    """Cultural cooking patterns and preferences"""
    cuisine_style: str = Field(..., description="Detected cuisine style")
    meal_context: str = Field(..., description="Meal context (casual, formal, etc.)")
    cooking_approach: str = Field(..., description="Cooking approach preference")
    budget_consciousness: str = Field(..., description="Budget awareness level")
    time_approach: str = Field(..., description="Time preference")
    social_dining: str = Field(..., description="Social dining context")


class CulturalAnalysis(BaseModel):
    """Complete cultural context analysis"""
    language: LanguageInfo
    location: LocationInfo
    cultural_indicators: CulturalIndicators
    traditional_dishes: List[Dict[str, Any]] = Field(default_factory=list)
    confidence_score: float = Field(..., ge=0, le=1)


class BudgetInfo(BaseModel):
    """Budget information with validation"""
    amount_ron: float = Field(..., gt=0, description="Budget amount in Romanian Lei")
    confidence: ConfidenceLevel
    explicit: bool = Field(..., description="Whether budget was explicitly stated")
    
    @validator('amount_ron')
    def validate_budget_range(cls, v):
        if v > 10000:  # Reasonable upper limit
            raise ValueError('Budget seems unreasonably high')
        return v


class ServingInfo(BaseModel):
    """Serving size information"""
    count: int = Field(..., gt=0, le=20, description="Number of servings")
    confidence: ConfidenceLevel
    explicit: bool


class TimeInfo(BaseModel):
    """Time constraint information"""
    minutes: int = Field(..., gt=0, description="Available time in minutes")
    urgency: str = Field(..., description="Time urgency level")
    confidence: ConfidenceLevel


class DietaryInfo(BaseModel):
    """Dietary restrictions and preferences"""
    restrictions: List[str] = Field(default_factory=list)
    preferences: List[str] = Field(default_factory=list)
    confidence: ConfidenceLevel


class CookingParameters(BaseModel):
    """Complete cooking parameters"""
    budget: BudgetInfo
    servings: ServingInfo
    time: TimeInfo
    meal_type: str
    meal_occasion: str
    dietary: DietaryInfo
    difficulty_preference: str
    cuisine_type: Optional[str] = None


class ProductInfo(BaseModel):
    """Individual product information from Bringo"""
    name: str
    price: float = Field(..., gt=0)
    url: str
    available: bool = True
    relevance_score: float = Field(..., ge=0, le=1)
    package_size: Optional[str] = None


class IngredientValidation(BaseModel):
    """Validated ingredient with alternatives"""
    name: str
    romanian_name: str
    is_valid: bool
    confidence: float = Field(..., ge=0, le=1)
    seasonal_rating: str
    alternatives: List[str] = Field(default_factory=list)
    substitutes: List[str] = Field(default_factory=list)
    estimated_cost_ron: Optional[float] = None


class ProductSearchResult(BaseModel):
    """Product search results for an ingredient"""
    ingredient: str
    search_terms_used: List[str]
    products_found: List[ProductInfo]
    best_recommendation: Optional[ProductInfo] = None
    total_found: int
    search_success: bool


class RecipeIngredient(BaseModel):
    """Recipe ingredient with product mapping"""
    name: str
    quantity: str
    unit: str
    product_recommendation: Optional[ProductInfo] = None
    preparation_notes: Optional[str] = None
    estimated_cost_ron: Optional[float] = None


class RecipeInstruction(BaseModel):
    """Individual recipe instruction step"""
    step: int
    description: str
    time_minutes: Optional[int] = None
    technique: Optional[str] = None
    tips: Optional[str] = None
    temperature: Optional[str] = None


class NutritionInfo(BaseModel):
    """Nutritional information per serving"""
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None


class CostAnalysis(BaseModel):
    """Recipe cost breakdown"""
    total_cost_ron: float = Field(..., gt=0)
    cost_per_serving_ron: float = Field(..., gt=0)
    budget_efficiency: str
    value_rating: str


class RecipeData(BaseModel):
    """Complete recipe information"""
    name: str
    description: str
    cuisine_type: str
    difficulty: str
    prep_time_minutes: int = Field(..., gt=0)
    cook_time_minutes: int = Field(..., gt=0)
    total_time_minutes: int = Field(..., gt=0)
    servings: int = Field(..., gt=0)
    ingredients: List[RecipeIngredient]
    instructions: List[RecipeInstruction]
    equipment: List[str] = Field(default_factory=list)
    nutrition_per_serving: Optional[NutritionInfo] = None
    serving_suggestions: List[str] = Field(default_factory=list)
    storage_instructions: Optional[str] = None
    variations: List[str] = Field(default_factory=list)
    chef_notes: List[str] = Field(default_factory=list)
    cost_analysis: CostAnalysis


class TutorialStep(BaseModel):
    """Tutorial step information"""
    step_number: int = Field(..., gt=0)
    title: str
    description: str
    image_prompt: str
    estimated_time_minutes: Optional[int] = None
    key_techniques: List[str] = Field(default_factory=list)


class TutorialData(BaseModel):
    """Complete tutorial information"""
    recipe_name: str
    cuisine_type: str
    tutorial_type: str = "7-step visual cooking tutorial"
    steps: List[TutorialStep]
    generated_files: List[str] = Field(default_factory=list)
    total_steps: int = Field(..., gt=0, le=10)
    steps_completed: int = Field(..., ge=0)
    tutorial_suitability_score: float = Field(..., ge=0, le=10)
    generation_notes: Optional[str] = None


# Response Models

class StandardResponse(BaseModel):
    """Standardized response format for all agents"""
    status: StatusType
    message: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    agent_name: str
    processing_time_ms: Optional[int] = None
    confidence_score: Optional[float] = None


class CulturalAnalysisResponse(StandardResponse):
    """Cultural analysis agent response"""
    data: Optional[CulturalAnalysis] = None
    user_request: str
    detected_language: Optional[str] = None


class ParameterExtractionResponse(StandardResponse):
    """Parameter extraction agent response"""
    data: Optional[CookingParameters] = None
    user_request: str
    parameters_found: int = 0


class IngredientValidationResponse(StandardResponse):
    """Ingredient validation agent response"""
    data: Optional[List[IngredientValidation]] = None
    total_ingredients: int = 0
    validation_success_rate: float = 0.0


class ProductSearchResponse(StandardResponse):
    """Product search agent response"""
    data: Optional[List[ProductSearchResult]] = None
    total_searches: int = 0
    successful_searches: int = 0
    total_products_found: int = 0


class RecipeCreationResponse(StandardResponse):
    """Recipe creation agent response"""
    data: Optional[RecipeData] = None
    recipe_created: bool = False
    cultural_adaptations: List[str] = Field(default_factory=list)


class TutorialResponse(StandardResponse):
    """Tutorial agent response"""
    data: Optional[TutorialData] = None
    tutorial_created: bool = False
    images_generated: int = 0


class ConversationResponse(StandardResponse):
    """Conversation agent response"""
    presentation_content: Optional[str] = None
    suggested_next_steps: List[str] = Field(default_factory=list)
    conversation_stage: str = "initial"