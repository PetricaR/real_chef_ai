# agents/bringo_chef_ai_assistant/sub_agents/ingredient_validation/tools.py
# Intelligent ingredient selection and validation with pure AI-driven approach
# Automatic ingredient selection based on cultural context and cooking parameters

import asyncio
import logging
import time
import json
from datetime import datetime
from typing import List, Dict, Any

from ...shared.client import get_ai_client
from ...shared.models import IngredientValidation, IngredientValidationResponse
from ...shared.responses import create_success_response, create_error_response
from ...shared.config import settings

logger = logging.getLogger("ingredient_tools")


async def select_and_validate_ingredients(
    user_request: str,
    cultural_context_json: str = "",
    parameters_json: str = ""
) -> str:
    """
    Intelligently select and validate ingredients based on cultural context and parameters.
    This is the main function that automatically chooses ingredients without asking the user.
    
    Args:
        user_request: Original user culinary request
        cultural_context_json: Cultural analysis results
        parameters_json: Extracted cooking parameters
        
    Returns:
        JSON string containing intelligent ingredient selection and validation
    """
    start_time = time.time()
    logger.info(f"🧠 Intelligent ingredient selection for: {user_request[:50]}...")
    
    # Parse context information for intelligent selection
    context_summary = await _parse_context_for_selection(cultural_context_json, parameters_json)
    
    # Get current season for seasonal optimization
    current_season = _get_current_season()
    
    # Professional AI prompt for intelligent ingredient selection
    prompt = f"""
    Automatically select optimal ingredients for this culinary request: "{user_request}"
    
    Context Information:
    {context_summary}
    Current Season: {current_season}
    
    As an expert ingredient selection specialist, automatically choose the best ingredients for this request:
    
    ## AUTOMATIC INGREDIENT SELECTION PROTOCOL
    
    1. **Cuisine Analysis & Dish Selection**:
       - Analyze the request to determine optimal dish type
       - Consider cultural context, budget, and cooking parameters
       - Select a specific dish that best fits all constraints
       - Ensure dish authenticity while maintaining practical feasibility
    
    2. **Intelligent Ingredient Selection**:
       - Automatically select ALL necessary ingredients for the chosen dish
       - Balance authenticity with Romanian market availability
       - Optimize for budget constraints and serving requirements
       - Consider seasonal availability and pricing
       - Include both essential and optional enhancement ingredients
    
    3. **Romanian Market Optimization**:
       - Provide accurate Romanian names for all ingredients
       - Consider local ingredient variations and preferences
       - Ensure all ingredients are available in typical Romanian supermarkets
       - Optimize ingredient selection for local purchasing patterns
    
    4. **Validation and Alternative Generation**:
       - Validate each ingredient for appropriateness and availability
       - Generate smart alternatives for potentially unavailable items
       - Consider nutritional and flavor compatibility
       - Provide substitution options that maintain dish integrity
    
    5. **Budget and Quantity Optimization**:
       - Calculate realistic quantities for the specified serving count
       - Estimate accurate Romanian market prices
       - Ensure total cost aligns with budget constraints
       - Optimize ingredient selection for maximum value
    
    Return comprehensive ingredient analysis:
    {{
        "automatic_ingredient_selection": {{
            "selected_dish": "specific_dish_name_that_fits_context",
            "reasoning": "detailed_explanation_why_this_dish_is_optimal",
            "cuisine_authenticity": "traditional|adapted|fusion",
            "difficulty_match": "how_dish_matches_skill_level",
            "selected_ingredients": [
                {{
                    "name": "ingredient_name_english",
                    "romanian_name": "accurate_romanian_ingredient_name",
                    "quantity": "specific_amount_for_stated_servings",
                    "unit": "measurement_unit",
                    "importance": "essential|important|optional",
                    "estimated_cost_ron": realistic_romanian_market_price,
                    "selection_reason": "why_this_ingredient_chosen"
                }}
            ]
        }},
        "validations": [
            {{
                "ingredient": "ingredient_name",
                "romanian_name": "nume_ingredient_romana",
                "is_valid": true,
                "confidence": confidence_score_0_to_1,
                "seasonal_rating": "excellent|good|fair|poor_for_{current_season}",
                "availability_assessment": "common|seasonal|specialty|rare",
                "alternatives": ["romanian_alternative_1", "romanian_alternative_2"],
                "substitutes": ["suitable_substitute_1", "suitable_substitute_2"],
                "shopping_tips": "where_and_how_to_buy_in_romania",
                "storage_advice": "how_to_store_properly"
            }}
        ],
        "budget_analysis": {{
            "total_estimated_cost_ron": total_ingredient_cost,
            "cost_per_serving_ron": cost_divided_by_servings,
            "budget_efficiency": "excellent|good|moderate|expensive",
            "budget_utilization_percentage": percentage_of_stated_budget,
            "optimization_suggestions": ["specific_cost_saving_recommendations"],
            "value_assessment": "assessment_of_value_for_money"
        }},
        "romanian_market_insights": {{
            "best_shopping_strategy": "optimal_shopping_approach",
            "seasonal_considerations": "seasonal_pricing_and_availability_notes",
            "local_alternatives": "romanian_specific_ingredient_alternatives",
            "cultural_adaptations": "how_recipe_adapted_for_romanian_market"
        }}
    }}
    
    CRITICAL REQUIREMENTS:
    - Automatically select a complete ingredient list (10-15 ingredients typical)
    - Provide accurate Romanian ingredient names for effective product search
    - Ensure all selections fit within the stated budget and cultural context
    - Never ask for user input - make intelligent decisions based on context
    - Prioritize commonly available ingredients over specialty items
    - Consider Romanian cooking traditions and market preferences
    """
    
    try:
        # Use AI for intelligent ingredient selection
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=prompt,
            temperature=settings.balanced_temperature,
            agent_name="ingredient_validation_agent"
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        # Parse and validate the response
        content = response.get("content", "")
        parsed_data = json.loads(content)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Extract key metrics
        ingredient_count = len(parsed_data.get("automatic_ingredient_selection", {}).get("selected_ingredients", []))
        total_cost = parsed_data.get("budget_analysis", {}).get("total_estimated_cost_ron", 0)
        
        logger.info(f"✅ Intelligent ingredient selection completed in {processing_time}ms")
        logger.info(f"🥬 Selected {ingredient_count} ingredients")
        logger.info(f"💰 Total estimated cost: {total_cost} RON")
        logger.info(f"🍽️ Recommended dish: {parsed_data.get('automatic_ingredient_selection', {}).get('selected_dish', 'Unknown')}")
        
        # Create successful response
        response_obj = IngredientValidationResponse(
            status="success",
            message=f"Automatically selected {ingredient_count} ingredients for optimal recipe",
            agent_name="ingredient_validation_agent",
            processing_time_ms=processing_time,
            confidence_score=_calculate_selection_confidence(parsed_data),
            total_ingredients=ingredient_count,
            validation_success_rate=1.0,  # All selected ingredients are validated
            data=parsed_data.get("validations", [])
        )
        
        # Add the full selection data to the response
        response_dict = response_obj.dict()
        response_dict["automatic_selection_data"] = parsed_data
        
        return json.dumps(response_dict, ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Intelligent ingredient selection failed: {e}")
        
        # Create fallback response with basic ingredient selection
        fallback_response = IngredientValidationResponse(
            status="warning",
            message=f"Intelligent selection partially failed: {str(e)}. Using basic ingredient selection.",
            agent_name="ingredient_validation_agent",
            processing_time_ms=processing_time,
            confidence_score=0.4,
            total_ingredients=0,
            validation_success_rate=0.0
        )
        
        return fallback_response.model_dump_json(indent=2)


async def validate_ingredients_with_context(
    ingredients_list: str,
    cultural_context_json: str = "",
    parameters_json: str = ""
) -> str:
    """
    Validate a provided list of ingredients with cultural context and parameters.
    
    Args:
        ingredients_list: Comma-separated list of ingredients to validate
        cultural_context_json: Cultural analysis results
        parameters_json: Extracted cooking parameters
        
    Returns:
        JSON string containing validation results
    """
    start_time = time.time()
    logger.info(f"🔍 Validating ingredient list: {ingredients_list[:50]}...")
    
    if not ingredients_list or len(ingredients_list.strip()) < 2:
        return create_error_response(
            agent_name="ingredient_validation_agent",
            error_message="No ingredients provided for validation"
        ).model_dump_json()
    
    # Parse ingredients from the list
    ingredients = [ing.strip() for ing in ingredients_list.split(",") if ing.strip()]
    
    if not ingredients:
        return create_error_response(
            agent_name="ingredient_validation_agent",
            error_message="Could not parse any valid ingredients from the list"
        ).model_dump_json()
    
    # Parse context information
    context_summary = await _parse_context_for_selection(cultural_context_json, parameters_json)
    current_season = _get_current_season()
    
    # Professional validation prompt
    prompt = f"""
    Validate these ingredients for Romanian market availability and appropriateness: {ingredients}
    
    Context Information:
    {context_summary}
    Current Season: {current_season}
    
    As a professional ingredient validation specialist, analyze each ingredient:
    
    1. **Availability Assessment**:
       - Evaluate availability in typical Romanian supermarkets
       - Consider seasonal availability and pricing patterns
       - Assess whether ingredient is common, seasonal, specialty, or rare
    
    2. **Romanian Translation and Alternatives**:
       - Provide accurate Romanian ingredient names for product search
       - Suggest local Romanian alternatives if original ingredient is unavailable
       - Consider regional ingredient variations and preferences
    
    3. **Cultural and Culinary Appropriateness**:
       - Assess ingredient fit with detected cultural context
       - Validate ingredient combinations for culinary compatibility
       - Consider traditional Romanian cooking methods and preferences
    
    4. **Budget and Quality Optimization**:
       - Estimate realistic Romanian market prices
       - Suggest quality alternatives within budget constraints
       - Provide shopping and storage recommendations
    
    Return detailed validation analysis:
    {{
        "validations": [
            {{
                "ingredient": "original_ingredient_name",
                "romanian_name": "accurate_romanian_translation",
                "is_valid": true_or_false,
                "confidence": confidence_score_0_to_1,
                "seasonal_rating": "excellent|good|fair|poor_for_{current_season}",
                "availability_assessment": "common|seasonal|specialty|rare",
                "estimated_cost_ron": realistic_market_price,
                "alternatives": ["romanian_alternative_1", "romanian_alternative_2"],
                "substitutes": ["suitable_substitute_1", "suitable_substitute_2"],
                "validation_notes": "specific_validation_reasoning",
                "shopping_recommendations": "where_and_how_to_buy",
                "storage_advice": "proper_storage_methods"
            }}
        ],
        "overall_assessment": {{
            "total_ingredients_validated": {len(ingredients)},
            "validation_success_rate": percentage_successfully_validated,
            "cultural_compatibility": "excellent|good|fair|poor",
            "budget_feasibility": "within_budget|slightly_over|significantly_over",
            "seasonal_optimization": "well_optimized|moderately_optimized|poorly_optimized"
        }},
        "recommendations": {{
            "ingredient_improvements": ["suggestions_for_better_ingredients"],
            "cost_optimizations": ["ways_to_reduce_costs"],
            "availability_improvements": ["how_to_improve_availability"],
            "cultural_enhancements": ["ways_to_improve_cultural_authenticity"]
        }}
    }}
    
    Provide professional, actionable validation results for Romanian market context.
    """
    
    try:
        # Use AI for validation
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=prompt,
            temperature=settings.conservative_temperature,
            agent_name="ingredient_validation_agent"
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        # Parse and validate the response
        content = response.get("content", "")
        parsed_data = json.loads(content)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Extract validation metrics
        validations = parsed_data.get("validations", [])
        valid_ingredients = sum(1 for v in validations if v.get("is_valid", False))
        success_rate = valid_ingredients / len(ingredients) if ingredients else 0
        
        logger.info(f"✅ Ingredient validation completed in {processing_time}ms")
        logger.info(f"✅ {valid_ingredients}/{len(ingredients)} ingredients validated successfully")
        
        # Create validation response
        response_obj = IngredientValidationResponse(
            status="success" if success_rate >= 0.8 else "warning",
            message=f"Validated {valid_ingredients}/{len(ingredients)} ingredients successfully",
            agent_name="ingredient_validation_agent",
            processing_time_ms=processing_time,
            confidence_score=success_rate,
            total_ingredients=len(ingredients),
            validation_success_rate=success_rate,
            data=validations
        )
        
        # Add full validation data
        response_dict = response_obj.dict()
        response_dict["validation_details"] = parsed_data
        
        return json.dumps(response_dict, ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Ingredient validation failed: {e}")
        
        # Create error response
        error_response = IngredientValidationResponse(
            status="error",
            message=f"Ingredient validation failed: {str(e)}",
            agent_name="ingredient_validation_agent",
            processing_time_ms=processing_time,
            total_ingredients=len(ingredients),
            validation_success_rate=0.0
        )
        
        return error_response.model_dump_json(indent=2)


async def _parse_context_for_selection(cultural_context_json: str, parameters_json: str) -> str:
    """Parse and summarize context information for ingredient selection"""
    context_summary = "Context: Limited information available\n"
    
    # Parse cultural context
    if cultural_context_json:
        try:
            cultural_data = json.loads(cultural_context_json)
            if cultural_data.get("status") == "success" and cultural_data.get("data"):
                context = cultural_data["data"]
                context_summary += f"""
Cultural Context:
- Language: {context.get('language', {}).get('name', 'Unknown')}
- Location: {context.get('location', {}).get('country', 'Unknown')}
- Cuisine Style: {context.get('cultural_indicators', {}).get('cuisine_style', 'unknown')}
- Meal Context: {context.get('cultural_indicators', {}).get('meal_context', 'unknown')}
- Cooking Approach: {context.get('cultural_indicators', {}).get('cooking_approach', 'unknown')}
- Budget Consciousness: {context.get('cultural_indicators', {}).get('budget_consciousness', 'unknown')}
- Social Dining: {context.get('cultural_indicators', {}).get('social_dining', 'unknown')}
"""
        except Exception as e:
            logger.warning(f"⚠️ Could not parse cultural context: {e}")
    
    # Parse cooking parameters
    if parameters_json:
        try:
            params_data = json.loads(parameters_json)
            if params_data.get("status") == "success" and params_data.get("data"):
                params = params_data["data"]
                context_summary += f"""
Cooking Parameters:
- Budget: {params.get('budget', {}).get('amount_ron', 'unknown')} RON
- Servings: {params.get('servings', {}).get('count', 'unknown')}
- Time Available: {params.get('time', {}).get('minutes', 'unknown')} minutes
- Meal Type: {params.get('meal_type', 'unknown')}
- Meal Occasion: {params.get('meal_occasion', 'unknown')}
- Difficulty Preference: {params.get('difficulty_preference', 'unknown')}
- Dietary Requirements: {params.get('dietary', {}).get('restrictions', [])}
"""
        except Exception as e:
            logger.warning(f"⚠️ Could not parse cooking parameters: {e}")
    
    return context_summary


def _get_current_season() -> str:
    """Get current season for seasonal optimization"""
    month = datetime.now().month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"


def _calculate_selection_confidence(parsed_data: Dict[str, Any]) -> float:
    """Calculate overall confidence score for ingredient selection"""
    try:
        # Base confidence on budget efficiency and validation quality
        budget_analysis = parsed_data.get("budget_analysis", {})
        budget_efficiency = budget_analysis.get("budget_efficiency", "moderate")
        
        efficiency_scores = {
            "excellent": 1.0,
            "good": 0.8,
            "moderate": 0.6,
            "expensive": 0.4
        }
        
        base_score = efficiency_scores.get(budget_efficiency, 0.6)
        
        # Adjust based on ingredient count and validation
        ingredient_count = len(parsed_data.get("automatic_ingredient_selection", {}).get("selected_ingredients", []))
        if ingredient_count >= 8:  # Good ingredient selection
            base_score += 0.1
        
        return min(1.0, base_score)
        
    except Exception:
        return 0.7  # Default confidence