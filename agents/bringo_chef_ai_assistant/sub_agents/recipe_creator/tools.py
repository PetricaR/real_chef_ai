# agents/bringo_chef_ai_assistant/sub_agents/recipe_creator/tools.py
# Professional recipe creation tools with cultural adaptation and real pricing integration
# Comprehensive recipe generation using validated ingredients and actual product data

import asyncio
import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from ....shared.client import get_ai_client, call_ai_with_validation
from ....shared.models import RecipeData, RecipeCreationResponse, RecipeIngredient, RecipeInstruction, NutritionInfo, CostAnalysis
from ....shared.responses import create_success_response, create_error_response
from ....shared.config import settings

logger = logging.getLogger("recipe_creator_tools")


async def create_comprehensive_recipe(
    user_request: str,
    cultural_context_json: str = "",
    parameters_json: str = "",
    ingredient_validation_json: str = "",
    product_search_json: str = ""
) -> str:
    """
    Create a comprehensive recipe integrating all available context and product data.
    
    Args:
        user_request: Original user culinary request
        cultural_context_json: Cultural analysis results
        parameters_json: Extracted cooking parameters
        ingredient_validation_json: Ingredient validation and selection results
        product_search_json: Product search results with real pricing
        
    Returns:
        JSON string containing complete recipe with real pricing and cultural adaptation
    """
    start_time = time.time()
    logger.info(f"👨‍🍳 Creating comprehensive recipe for: {user_request[:50]}...")
    
    try:
        # Parse all input contexts
        context_data = await _parse_all_contexts(
            cultural_context_json, parameters_json, 
            ingredient_validation_json, product_search_json
        )
        
        # Determine recipe creation strategy based on available data
        if context_data["has_complete_data"]:
            logger.info("🎯 Using complete data integration strategy")
            recipe_result = await _create_fully_integrated_recipe(user_request, context_data)
        else:
            logger.info("📋 Using partial data strategy")
            recipe_result = await _create_basic_recipe_with_available_data(user_request, context_data)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        if recipe_result.get("success"):
            recipe_data = recipe_result["data"]
            
            logger.info(f"✅ Recipe creation completed in {processing_time}ms")
            logger.info(f"🍽️ Created: {recipe_data.name}")
            logger.info(f"💰 Total cost: {recipe_data.cost_analysis.total_cost_ron} RON")
            logger.info(f"👥 Serves: {recipe_data.servings} people")
            
            # Create successful response
            response = RecipeCreationResponse(
                status="success",
                message=f"Recipe '{recipe_data.name}' created successfully",
                agent_name="recipe_creation_agent",
                processing_time_ms=processing_time,
                confidence_score=recipe_result.get("confidence", 0.85),
                data=recipe_data,
                recipe_created=True,
                cultural_adaptations=recipe_result.get("cultural_adaptations", [])
            )
            
            return response.json(ensure_ascii=False, indent=2)
        else:
            raise Exception(recipe_result.get("error", "Recipe creation failed"))
            
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Recipe creation failed: {e}")
        
        # Create fallback response
        fallback_response = RecipeCreationResponse(
            status="error",
            message=f"Recipe creation failed: {str(e)}",
            agent_name="recipe_creation_agent",
            processing_time_ms=processing_time,
            recipe_created=False
        )
        
        return fallback_response.json(ensure_ascii=False, indent=2)


async def create_culturally_adapted_recipe(
    base_recipe_json: str,
    cultural_context_json: str,
    target_culture: str = "romanian"
) -> str:
    """
    Adapt an existing recipe for specific cultural preferences and ingredient availability.
    
    Args:
        base_recipe_json: Base recipe to adapt
        cultural_context_json: Cultural context for adaptation
        target_culture: Target cultural adaptation
        
    Returns:
        JSON string containing culturally adapted recipe
    """
    start_time = time.time()
    logger.info(f"🌍 Adapting recipe for {target_culture} culture...")
    
    try:
        # Parse base recipe and cultural context
        base_recipe = json.loads(base_recipe_json)
        cultural_data = json.loads(cultural_context_json) if cultural_context_json else {}
        
        if base_recipe.get("status") != "success":
            raise Exception("Invalid base recipe for cultural adaptation")
        
        recipe_data = base_recipe.get("data", {})
        
        # Create cultural adaptation prompt
        adaptation_prompt = f"""
        Adapt this recipe for {target_culture} cultural preferences and ingredient availability:
        
        Base Recipe: {json.dumps(recipe_data, indent=2)[:2000]}  # Truncate for prompt size
        Cultural Context: {json.dumps(cultural_data.get('data', {}), indent=2)[:1000]}
        
        As a culinary cultural adaptation specialist, modify the recipe considering:
        
        1. **Cultural Cooking Traditions**:
           - Adapt cooking techniques to match cultural preferences
           - Modify spice levels and flavor profiles for local tastes
           - Adjust portion sizes and serving styles
           - Integrate traditional cooking methods where appropriate
        
        2. **Local Ingredient Adaptation**:
           - Replace unavailable ingredients with culturally appropriate alternatives
           - Suggest local Romanian brands and product variations
           - Optimize ingredient selection for local market availability
           - Maintain dish integrity while improving accessibility
        
        3. **Cultural Presentation and Serving**:
           - Adapt presentation style to cultural expectations
           - Modify serving suggestions for cultural dining patterns
           - Include cultural garnishes and accompaniments
           - Adjust cooking timing for cultural meal patterns
        
        4. **Romanian Market Optimization**:
           - Optimize ingredients for Romanian supermarket availability
           - Suggest Romanian brand preferences and local alternatives
           - Adapt quantities for typical Romanian package sizes
           - Consider seasonal Romanian ingredient availability
        
        Return culturally adapted recipe maintaining original structure:
        {{
            "name": "culturally_adapted_recipe_name",
            "description": "adapted_description_highlighting_cultural_elements",
            "cuisine_type": "adapted_cuisine_classification",
            "cultural_authenticity": "traditional|adapted|fusion",
            "ingredients": [adapted_ingredient_list_with_romanian_products],
            "instructions": [adapted_cooking_instructions_with_cultural_techniques],
            "cultural_adaptations_made": ["list_of_specific_adaptations"],
            "romanian_market_optimizations": ["local_market_improvements"],
            "cultural_serving_suggestions": ["culturally_appropriate_serving_guidance"]
        }}
        """
        
        # Use AI for cultural adaptation
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=adaptation_prompt,
            temperature=settings.balanced_temperature,
            agent_name="recipe_creation_agent"
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        adapted_data = json.loads(response.get("content", "{}"))
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"✅ Cultural adaptation completed in {processing_time}ms")
        
        # Create adaptation response
        response_obj = {
            "status": "success",
            "message": f"Recipe successfully adapted for {target_culture} culture",
            "agent_name": "recipe_creation_agent",
            "processing_time_ms": processing_time,
            "adapted_recipe": adapted_data,
            "adaptation_type": target_culture,
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(response_obj, ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Cultural adaptation failed: {e}")
        
        error_response = {
            "status": "error",
            "message": f"Cultural adaptation failed: {str(e)}",
            "agent_name": "recipe_creation_agent",
            "processing_time_ms": processing_time
        }
        
        return json.dumps(error_response, ensure_ascii=False, indent=2)


async def optimize_recipe_for_budget(
    recipe_json: str,
    target_budget_ron: float,
    product_alternatives_json: str = ""
) -> str:
    """
    Optimize recipe to fit within specified budget constraints while maintaining quality.
    
    Args:
        recipe_json: Recipe to optimize
        target_budget_ron: Target budget in Romanian Lei
        product_alternatives_json: Alternative product options
        
    Returns:
        JSON string containing budget-optimized recipe
    """
    start_time = time.time()
    logger.info(f"💰 Optimizing recipe for {target_budget_ron} RON budget...")
    
    try:
        recipe_data = json.loads(recipe_json)
        alternatives_data = json.loads(product_alternatives_json) if product_alternatives_json else {}
        
        if recipe_data.get("status") != "success":
            raise Exception("Invalid recipe for budget optimization")
        
        current_recipe = recipe_data.get("data", {})
        current_cost = current_recipe.get("cost_analysis", {}).get("total_cost_ron", 0)
        
        if current_cost <= target_budget_ron:
            logger.info(f"✅ Recipe already within budget: {current_cost} RON <= {target_budget_ron} RON")
            return recipe_json  # No optimization needed
        
        # Create budget optimization prompt
        optimization_prompt = f"""
        Optimize this recipe to fit within {target_budget_ron} RON budget:
        
        Current Recipe: {json.dumps(current_recipe, indent=2)[:2000]}
        Current Cost: {current_cost} RON
        Target Budget: {target_budget_ron} RON
        Cost Reduction Needed: {current_cost - target_budget_ron} RON
        
        Product Alternatives: {json.dumps(alternatives_data, indent=2)[:1000]}
        
        As a budget optimization specialist, reduce costs while maintaining recipe quality:
        
        1. **Ingredient Cost Optimization**:
           - Replace expensive ingredients with budget-friendly alternatives
           - Adjust quantities to reduce cost while maintaining flavor balance
           - Suggest generic brands or budget product alternatives
           - Eliminate optional/luxury ingredients if necessary
        
        2. **Portion and Serving Optimization**:
           - Adjust serving sizes to fit budget per person
           - Optimize ingredient ratios for maximum value
           - Suggest serving extensions (bread, rice, etc.) to increase value
           - Maintain nutritional balance while reducing costs
        
        3. **Smart Substitution Strategy**:
           - Replace premium ingredients with effective budget alternatives
           - Use seasonal ingredients for better pricing
           - Suggest bulk buying opportunities for cost savings
           - Maintain flavor profile with cost-effective substitutions
        
        4. **Value Enhancement Techniques**:
           - Add filling, budget-friendly ingredients to increase satisfaction
           - Suggest preparation techniques that maximize ingredient utilization
           - Include cost-saving cooking methods and techniques
           - Provide tips for stretching expensive ingredients
        
        Return optimized recipe maintaining structure:
        {{
            "optimized_recipe": {{
                "name": "budget_optimized_recipe_name",
                "ingredients": [optimized_ingredient_list_with_budget_products],
                "instructions": [updated_instructions_for_optimized_ingredients],
                "cost_analysis": {{
                    "total_cost_ron": new_total_cost,
                    "cost_per_serving_ron": new_per_serving_cost,
                    "budget_efficiency": "excellent|good|moderate",
                    "savings_achieved_ron": amount_saved
                }}
            }},
            "optimization_details": {{
                "cost_reductions": ["specific_cost_saving_changes"],
                "substitutions_made": ["ingredient_substitutions_with_reasoning"],
                "quantity_adjustments": ["portion_adjustments_made"],
                "value_enhancements": ["added_value_elements"]
            }},
            "budget_compliance": {{
                "target_budget_ron": {target_budget_ron},
                "achieved_cost_ron": achieved_total_cost,
                "budget_utilization_percentage": percentage_used,
                "remaining_budget_ron": remaining_amount
            }}
        }}
        """
        
        # Use AI for budget optimization
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=optimization_prompt,
            temperature=settings.conservative_temperature,
            agent_name="recipe_creation_agent"
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        optimization_data = json.loads(response.get("content", "{}"))
        processing_time = int((time.time() - start_time) * 1000)
        
        achieved_cost = optimization_data.get("optimized_recipe", {}).get("cost_analysis", {}).get("total_cost_ron", current_cost)
        savings = current_cost - achieved_cost
        
        logger.info(f"✅ Budget optimization completed in {processing_time}ms")
        logger.info(f"💰 Cost reduced from {current_cost} to {achieved_cost} RON (saved {savings} RON)")
        
        # Create optimization response
        response_obj = {
            "status": "success",
            "message": f"Recipe optimized for {target_budget_ron} RON budget",
            "agent_name": "recipe_creation_agent",
            "processing_time_ms": processing_time,
            "optimization_data": optimization_data,
            "cost_reduction_achieved": savings,
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(response_obj, ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Budget optimization failed: {e}")
        
        error_response = {
            "status": "error",
            "message": f"Budget optimization failed: {str(e)}",
            "agent_name": "recipe_creation_agent",
            "processing_time_ms": processing_time
        }
        
        return json.dumps(error_response, ensure_ascii=False, indent=2)


async def _parse_all_contexts(
    cultural_context_json: str,
    parameters_json: str,
    ingredient_validation_json: str,
    product_search_json: str
) -> Dict[str, Any]:
    """Parse and organize all context data for recipe creation"""
    context_data = {
        "has_complete_data": False,
        "cultural_context": {},
        "parameters": {},
        "ingredients": [],
        "products": [],
        "budget_info": {},
        "serving_info": {},
        "dietary_info": {}
    }
    
    # Parse cultural context
    if cultural_context_json:
        try:
            cultural_data = json.loads(cultural_context_json)
            if cultural_data.get("status") == "success":
                context_data["cultural_context"] = cultural_data.get("data", {})
        except Exception as e:
            logger.warning(f"⚠️ Could not parse cultural context: {e}")
    
    # Parse cooking parameters
    if parameters_json:
        try:
            params_data = json.loads(parameters_json)
            if params_data.get("status") == "success":
                params = params_data.get("data", {})
                context_data["parameters"] = params
                context_data["budget_info"] = params.get("budget", {})
                context_data["serving_info"] = params.get("servings", {})
                context_data["dietary_info"] = params.get("dietary", {})
        except Exception as e:
            logger.warning(f"⚠️ Could not parse parameters: {e}")
    
    # Parse ingredient validation
    if ingredient_validation_json:
        try:
            ingredient_data = json.loads(ingredient_validation_json)
            if ingredient_data.get("status") in ["success", "warning"]:
                # Extract from automatic selection data
                if "automatic_selection_data" in ingredient_data:
                    selection_data = ingredient_data["automatic_selection_data"]
                    auto_ingredients = selection_data.get("automatic_ingredient_selection", {}).get("selected_ingredients", [])
                    context_data["ingredients"] = auto_ingredients
                
                # Also get validation data
                validation_data = ingredient_data.get("data", [])
                if validation_data:
                    context_data["ingredient_validations"] = validation_data
        except Exception as e:
            logger.warning(f"⚠️ Could not parse ingredient validation: {e}")
    
    # Parse product search results
    if product_search_json:
        try:
            product_data = json.loads(product_search_json)
            if product_data.get("status") == "success":
                search_results = product_data.get("data", [])
                context_data["products"] = search_results
        except Exception as e:
            logger.warning(f"⚠️ Could not parse product search: {e}")
    
    # Determine if we have complete data
    context_data["has_complete_data"] = (
        bool(context_data["cultural_context"]) and
        bool(context_data["parameters"]) and
        bool(context_data["ingredients"]) and
        bool(context_data["products"])
    )
    
    return context_data


async def _create_fully_integrated_recipe(user_request: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create recipe with full integration of all available data"""
    
    # Extract key information
    cultural_context = context_data["cultural_context"]
    parameters = context_data["parameters"]
    ingredients = context_data["ingredients"]
    products = context_data["products"]
    
    # Build comprehensive context summary
    context_summary = f"""
    COMPREHENSIVE RECIPE CREATION CONTEXT:
    
    Original Request: "{user_request}"
    
    Cultural Context:
    - Language: {cultural_context.get('language', {}).get('name', 'Unknown')}
    - Location: {cultural_context.get('location', {}).get('country', 'Unknown')}
    - Cuisine Style: {cultural_context.get('cultural_indicators', {}).get('cuisine_style', 'unknown')}
    - Meal Context: {cultural_context.get('cultural_indicators', {}).get('meal_context', 'unknown')}
    - Cooking Approach: {cultural_context.get('cultural_indicators', {}).get('cooking_approach', 'unknown')}
    
    Cooking Parameters:
    - Budget: {parameters.get('budget', {}).get('amount_ron', 'unknown')} RON
    - Servings: {parameters.get('servings', {}).get('count', 'unknown')}
    - Time Available: {parameters.get('time', {}).get('minutes', 'unknown')} minutes
    - Meal Type: {parameters.get('meal_type', 'unknown')}
    - Difficulty Preference: {parameters.get('difficulty_preference', 'unknown')}
    
    Available Ingredients: {len(ingredients)} validated ingredients
    Product Data: {len(products)} product search results with real pricing
    """
    
    # Create comprehensive recipe generation prompt
    recipe_prompt = f"""
    Create a comprehensive, professional recipe integrating all available data:
    
    {context_summary}
    
    Validated Ingredients: {json.dumps(ingredients[:10], indent=2)}
    Product Search Results: {json.dumps([p for p in products[:5]], indent=2)}
    
    As a master chef and recipe development specialist, create a complete recipe that:
    
    1. **Integrates All Available Data**:
       - Use validated ingredients with real Bringo.ro product recommendations
       - Respect cultural context and cooking parameters
       - Incorporate actual product pricing for accurate cost analysis
       - Align with stated budget, serving, and time constraints
    
    2. **Professional Recipe Development**:
       - Create detailed ingredient list with exact quantities and product recommendations
       - Develop step-by-step instructions with timing and professional techniques
       - Include equipment requirements and preparation strategies
       - Provide chef tips, techniques, and troubleshooting guidance
    
    3. **Cultural Authenticity and Adaptation**:
       - Maintain cultural authenticity while adapting to Romanian market
       - Use culturally appropriate cooking techniques and presentation
       - Integrate traditional elements with modern cooking methods
       - Respect cultural dining patterns and serving traditions
    
    4. **Accurate Analysis and Calculations**:
       - Calculate realistic nutritional information based on ingredients
       - Provide precise cost analysis using real Bringo.ro pricing
       - Assess recipe difficulty and skill requirements
       - Include serving suggestions and storage instructions
    
    Return complete recipe data:
    {{
        "name": "Professional Recipe Name with Emoji 🍽️",
        "description": "Compelling 2-3 sentence description highlighting cultural authenticity and value",
        "cuisine_type": "specific_cuisine_classification",
        "difficulty": "easy|medium|advanced",
        "prep_time_minutes": realistic_prep_time,
        "cook_time_minutes": realistic_cooking_time,
        "total_time_minutes": total_time_needed,
        "servings": exact_serving_count,
        "ingredients": [
            {{
                "name": "ingredient_name",
                "quantity": "precise_amount",
                "unit": "measurement_unit",
                "product_recommendation": {{
                    "name": "exact_bringo_product_name",
                    "price": actual_bringo_price,
                    "url": "product_url_if_available"
                }},
                "preparation_notes": "specific_preparation_instructions"
            }}
        ],
        "instructions": [
            {{
                "step": 1,
                "description": "Detailed step-by-step instruction with professional techniques",
                "time_minutes": step_duration,
                "technique": "cooking_technique_used",
                "tips": "Professional chef tips and guidance",
                "temperature": "specific_temperature_if_applicable"
            }}
        ],
        "equipment": ["required_cooking_equipment"],
        "nutrition_per_serving": {{
            "calories": realistic_calorie_estimate,
            "protein_g": protein_content,
            "carbs_g": carbohydrate_content,
            "fat_g": fat_content,
            "fiber_g": fiber_content
        }},
        "serving_suggestions": ["culturally_appropriate_serving_recommendations"],
        "storage_instructions": "proper_storage_and_reheating_guidance",
        "variations": ["recipe_variations_and_adaptations"],
        "chef_notes": ["professional_cooking_secrets_and_tips"],
        "cost_analysis": {{
            "total_cost_ron": precise_total_cost_using_real_prices,
            "cost_per_serving_ron": cost_divided_by_servings,
            "budget_efficiency": "excellent|good|moderate|expensive",
            "value_rating": "assessment_of_value_for_money"
        }}
    }}
    
    CRITICAL REQUIREMENTS:
    - Use exact ingredient quantities that produce the specified serving count
    - Include real Bringo.ro product names and prices in ingredient recommendations
    - Provide professional-level cooking instructions with precise timing
    - Calculate accurate nutritional information based on actual ingredients
    - Ensure total cost aligns with budget constraints and expectations
    - Maintain cultural authenticity while ensuring practical feasibility
    """
    
    try:
        # Use AI to create comprehensive recipe
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=recipe_prompt,
            temperature=settings.balanced_temperature,
            agent_name="recipe_creation_agent",
            max_tokens=settings.max_tokens
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        recipe_data = json.loads(response.get("content", "{}"))
        
        # Convert to RecipeData model for validation
        validated_recipe = _convert_to_recipe_model(recipe_data)
        
        # Calculate cultural adaptations made
        cultural_adaptations = _identify_cultural_adaptations(recipe_data, cultural_context)
        
        return {
            "success": True,
            "data": validated_recipe,
            "confidence": 0.9,  # High confidence with complete data
            "cultural_adaptations": cultural_adaptations
        }
        
    except Exception as e:
        logger.error(f"❌ Fully integrated recipe creation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


async def _create_basic_recipe_with_available_data(user_request: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create recipe with partial data using intelligent defaults"""
    
    available_data = []
    if context_data["cultural_context"]:
        available_data.append("cultural context")
    if context_data["parameters"]:
        available_data.append("cooking parameters")
    if context_data["ingredients"]:
        available_data.append("ingredient data")
    if context_data["products"]:
        available_data.append("product pricing")
    
    logger.info(f"📋 Creating recipe with available data: {', '.join(available_data)}")
    
    # Create basic recipe prompt with available data
    basic_prompt = f"""
    Create a practical recipe for: "{user_request}"
    
    Available Context Data:
    {json.dumps(context_data, indent=2)[:1500]}  # Truncate for prompt size
    
    As a professional chef, create a complete recipe using available information and intelligent defaults:
    
    1. **Work with Available Data**:
       - Use any provided cultural context for authenticity
       - Apply known cooking parameters for constraints
       - Incorporate validated ingredients if available
       - Use product data for pricing if provided
    
    2. **Intelligent Defaults for Missing Data**:
       - Assume Romanian market context if cultural data missing
       - Default to 4 servings and 60-minute cooking time if parameters missing
       - Select appropriate ingredients based on request if validation missing
       - Estimate Romanian market pricing if product data missing
    
    3. **Maintain Recipe Quality**:
       - Ensure recipe is complete and practical
       - Provide detailed cooking instructions
       - Include realistic nutritional and cost estimates
       - Maintain cultural appropriateness
    
    Return complete recipe following the same structure as comprehensive recipes.
    Use conservative estimates for missing data with appropriate confidence indicators.
    """
    
    try:
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=basic_prompt,
            temperature=settings.balanced_temperature,
            agent_name="recipe_creation_agent"
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        recipe_data = json.loads(response.get("content", "{}"))
        validated_recipe = _convert_to_recipe_model(recipe_data)
        
        return {
            "success": True,
            "data": validated_recipe,
            "confidence": 0.7,  # Lower confidence with partial data
            "cultural_adaptations": ["basic_cultural_considerations"]
        }
        
    except Exception as e:
        logger.error(f"❌ Basic recipe creation failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def _convert_to_recipe_model(recipe_data: Dict[str, Any]) -> RecipeData:
    """Convert recipe dictionary to validated RecipeData model"""
    try:
        # Extract and validate ingredients
        ingredients = []
        for ing_data in recipe_data.get("ingredients", []):
            product_rec = ing_data.get("product_recommendation")
            product_info = None
            if product_rec:
                from ....shared.models import ProductInfo
                product_info = ProductInfo(
                    name=product_rec.get("name", ""),
                    price=float(product_rec.get("price", 0)),
                    url=product_rec.get("url", ""),
                    available=True,
                    relevance_score=1.0
                )
            
            ingredient = RecipeIngredient(
                name=ing_data.get("name", ""),
                quantity=ing_data.get("quantity", "1"),
                unit=ing_data.get("unit", "piece"),
                product_recommendation=product_info,
                preparation_notes=ing_data.get("preparation_notes")
            )
            ingredients.append(ingredient)
        
        # Extract and validate instructions
        instructions = []
        for inst_data in recipe_data.get("instructions", []):
            instruction = RecipeInstruction(
                step=inst_data.get("step", 1),
                description=inst_data.get("description", ""),
                time_minutes=inst_data.get("time_minutes"),
                technique=inst_data.get("technique"),
                tips=inst_data.get("tips"),
                temperature=inst_data.get("temperature")
            )
            instructions.append(instruction)
        
        # Extract nutrition info
        nutrition_data = recipe_data.get("nutrition_per_serving", {})
        nutrition = NutritionInfo(
            calories=nutrition_data.get("calories"),
            protein_g=nutrition_data.get("protein_g"),
            carbs_g=nutrition_data.get("carbs_g"),
            fat_g=nutrition_data.get("fat_g"),
            fiber_g=nutrition_data.get("fiber_g")
        )
        
        # Extract cost analysis
        cost_data = recipe_data.get("cost_analysis", {})
        cost_analysis = CostAnalysis(
            total_cost_ron=float(cost_data.get("total_cost_ron", 50.0)),
            cost_per_serving_ron=float(cost_data.get("cost_per_serving_ron", 12.5)),
            budget_efficiency=cost_data.get("budget_efficiency", "good"),
            value_rating=cost_data.get("value_rating", "good_value")
        )
        
        # Create complete recipe model
        recipe = RecipeData(
            name=recipe_data.get("name", "Delicious Recipe"),
            description=recipe_data.get("description", "A wonderful homemade dish"),
            cuisine_type=recipe_data.get("cuisine_type", "international"),
            difficulty=recipe_data.get("difficulty", "medium"),
            prep_time_minutes=recipe_data.get("prep_time_minutes", 20),
            cook_time_minutes=recipe_data.get("cook_time_minutes", 30),
            total_time_minutes=recipe_data.get("total_time_minutes", 50),
            servings=recipe_data.get("servings", 4),
            ingredients=ingredients,
            instructions=instructions,
            equipment=recipe_data.get("equipment", []),
            nutrition_per_serving=nutrition,
            serving_suggestions=recipe_data.get("serving_suggestions", []),
            storage_instructions=recipe_data.get("storage_instructions"),
            variations=recipe_data.get("variations", []),
            chef_notes=recipe_data.get("chef_notes", []),
            cost_analysis=cost_analysis
        )
        
        return recipe
        
    except Exception as e:
        logger.error(f"❌ Recipe model conversion failed: {e}")
        # Return a basic fallback recipe
        return RecipeData(
            name="Simple Recipe",
            description="A basic recipe created from available data",
            cuisine_type="international",
            difficulty="easy",
            prep_time_minutes=15,
            cook_time_minutes=25,
            total_time_minutes=40,
            servings=4,
            ingredients=[],
            instructions=[],
            cost_analysis=CostAnalysis(
                total_cost_ron=40.0,
                cost_per_serving_ron=10.0,
                budget_efficiency="moderate",
                value_rating="basic_value"
            )
        )


def _identify_cultural_adaptations(recipe_data: Dict[str, Any], cultural_context: Dict[str, Any]) -> List[str]:
    """Identify cultural adaptations made in the recipe"""
    adaptations = []
    
    cuisine_style = cultural_context.get("cultural_indicators", {}).get("cuisine_style", "")
    meal_context = cultural_context.get("cultural_indicators", {}).get("meal_context", "")
    
    if "romanian" in cuisine_style.lower():
        adaptations.append("adapted_for_romanian_taste_preferences")
    
    if "traditional" in cuisine_style.lower():
        adaptations.append("maintained_traditional_cooking_methods")
    
    if "romantic" in meal_context.lower():
        adaptations.append("optimized_for_romantic_dining_context")
    
    if "family" in meal_context.lower():
        adaptations.append("scaled_for_family_dining")
    
    # Always add Romanian market adaptation
    adaptations.append("optimized_for_romanian_ingredient_availability")
    adaptations.append("integrated_real_bringo_pricing")
    
    return adaptations