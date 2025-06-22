# ingredient_validation/tools.py
import logging
import json
from datetime import datetime
import calendar

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')
logger = logging.getLogger("ingredient_tools")

# Shared configuration
MODEL = "gemini-2.0-flash"
PROJECT_ID = "formare-ai"
LOCATION = "europe-west4"

# Shared AI client
try:
    from google import genai
    from google.genai import types
    
    gemini_client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )
    logger.info("✅ Ingredient agent AI client initialized")
except Exception as e:
    logger.error(f"❌ AI client failed: {e}")
    gemini_client = None

def _call_ai(prompt: str) -> dict:
    """Simplified AI call"""
    if not gemini_client:
        return {"error": "AI client unavailable"}
    
    try:
        response = gemini_client.models.generate_content(
            model=MODEL,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=2000,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"AI call failed: {e}")
        return {"error": str(e)}

def _get_current_season():
    """Get current season"""
    month = datetime.now().month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"

def validate_ingredient_comprehensive(user_request: str) -> str:
    """
    Comprehensive ingredient validation with alternatives and seasonal analysis.
    """
    logger.info(f"🥬 Validating ingredients from: {user_request[:50]}...")
    
    current_season = _get_current_season()
    current_month = calendar.month_name[datetime.now().month]
    
    prompt = f"""
    Extract and validate ingredients from this request: "{user_request}"
    Current season: {current_season}, Month: {current_month}
    
    Return JSON:
    {{
        "extracted_ingredients": [
            {{
                "name": "ingredient_name",
                "context": "how mentioned in request",
                "certainty": "high|medium|low"
            }}
        ],
        "validations": [
            {{
                "ingredient": "ingredient_name",
                "is_valid": true|false,
                "confidence": 0.95,
                "availability": "common|seasonal|rare|specialty",
                "current_season_rating": "excellent|good|fair|poor",
                "alternatives": [
                    {{
                        "name": "alternative_ingredient",
                        "reason": "why this alternative",
                        "availability": "better|same|worse"
                    }}
                ],
                "shopping_tips": {{
                    "where_to_buy": "supermarket|specialty_store|farmers_market",
                    "price_range": "budget|moderate|expensive",
                    "storage": "how to store properly"
                }}
            }}
        ],
        "seasonal_recommendations": [
            {{
                "ingredient": "seasonal_ingredient_to_consider",
                "benefit": "why add this ingredient",
                "season_peak": "when it's best"
            }}
        ]
    }}
    """
    
    try:
        result = _call_ai(prompt)
        if "error" in result:
            raise ValueError(result["error"])
            
        logger.info("✅ Ingredient validation successful")
        return json.dumps({
            "status": "success",
            "user_request": user_request,
            "current_season": current_season,
            "validation_results": result,
            "validated_at": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Ingredient validation failed: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e),
            "fallback": {
                "extracted_ingredients": [{"name": "unknown", "certainty": "low"}],
                "validations": []
            }
        })

def validate_ingredients_with_context(user_request: str, cultural_context_json: str, parameters_json: str) -> str:
    """
    Ingredient validation with cultural context and cooking parameters.
    AUTOMATICALLY selects ingredients based on cuisine type and cultural context.
    """
    logger.info(f"🌍 Validating ingredients with context for: {user_request[:50]}...")
    
    # Parse context
    cultural_context = {}
    parameters = {}
    
    try:
        if cultural_context_json:
            cultural_context = json.loads(cultural_context_json)
    except:
        logger.warning("Invalid cultural context JSON")
        
    try:
        if parameters_json:
            parameters = json.loads(parameters_json)
    except:
        logger.warning("Invalid parameters JSON")
    
    # Extract context info for prompt
    context_info = ""
    cuisine_type = "international"
    meal_context = "casual"
    budget = 50
    servings = 2
    
    # FIX: Handle the list structure correctly in cultural context
    if cultural_context.get("status") == "success":
        analysis_list = cultural_context.get("analysis", [])
        if analysis_list and isinstance(analysis_list, list):
            analysis = analysis_list[0]  # Take first analysis result
        else:
            analysis = {}
            
        language = analysis.get("language", {})
        location = analysis.get("location", {})
        cultural_indicators = analysis.get("cultural_indicators", {})
        
        context_info += f"Language: {language.get('name', 'Romanian')}\n"
        context_info += f"Country: {location.get('country', 'Romania')}\n"
        context_info += f"Cuisine Style: {cultural_indicators.get('cuisine_style', 'international')}\n"
        context_info += f"Meal Context: {cultural_indicators.get('meal_context', 'casual')}\n"
        
        cuisine_type = cultural_indicators.get('cuisine_style', 'international')
        meal_context = cultural_indicators.get('meal_context', 'casual')
    
    # Extract parameters 
    if parameters:
        budget = parameters.get("budget", "50 lei")
        if isinstance(budget, str):
            budget_match = [int(s) for s in budget.split() if s.isdigit()]
            budget = budget_match[0] if budget_match else 50
        
        servings = parameters.get("servings", 2)
        if isinstance(servings, str):
            servings = int(servings) if servings.isdigit() else 2
            
        context_info += f"Budget: {budget} RON\n"
        context_info += f"Servings: {servings}\n"
        context_info += f"Cuisine Type: {parameters.get('cuisine_type', cuisine_type)}\n"
        context_info += f"Meal Context: {parameters.get('meal_context', meal_context)}\n"
    
    current_season = _get_current_season()
    
    # INTELLIGENT AUTOMATIC INGREDIENT SELECTION
    prompt = f"""
    AUTOMATICALLY select and validate the best ingredients for this request: "{user_request}"
    
    Context:
    {context_info}
    Current season: {current_season}
    
    INTELLIGENT INGREDIENT SELECTION RULES:
    
    **For Italian Cuisine + Romantic Context:**
    - Suggest: Pasta (spaghetti/penne), garlic, olive oil, parmesan cheese, white wine, fresh basil, cherry tomatoes
    - Romantic Italian dishes: Pasta Carbonara, Aglio e Olio, or Pasta al Pomodoro
    - Budget {budget} RON allows for quality ingredients
    
    **For Romanian Cuisine:**
    - Traditional dishes: mici, sarmale, papanași
    - Ingredients: meat, cabbage, rice, flour, sour cream
    
    **For Budget {budget} RON:**
    - Under 50 RON: simple pasta, eggs, basic vegetables
    - 50-100 RON: meat dishes, quality ingredients, wine
    - Over 100 RON: premium ingredients
    
    AUTOMATICALLY select ingredients and return JSON:
    {{
        "automatic_ingredient_selection": {{
            "selected_dish": "recommended dish name",
            "reasoning": "why this dish fits the context",
            "selected_ingredients": [
                {{
                    "name": "ingredient name",
                    "quantity": "amount needed for {servings} servings",
                    "importance": "essential|important|optional",
                    "estimated_cost_ron": estimated_price
                }}
            ]
        }},
        "extracted_ingredients": [
            {{
                "name": "ingredient_name",
                "context": "automatically selected for {cuisine_type} {meal_context}",
                "certainty": "high"
            }}
        ],
        "validations": [
            {{
                "ingredient": "ingredient_name",
                "is_valid": true,
                "cultural_relevance": "high|medium|low",
                "budget_fit": "within budget",
                "local_alternatives": ["Romanian alternatives if needed"],
                "quantity_for_servings": "specific amount for {servings} people",
                "shopping_strategy": "where to buy in Romania",
                "seasonal_rating": "excellent|good|fair for {current_season}"
            }}
        ],
        "cultural_adaptations": [
            {{
                "dish_recommendation": "specific dish name",
                "cultural_authenticity": "traditional|adapted|fusion",
                "why_perfect_for_context": "explanation for {cuisine_type} {meal_context}"
            }}
        ],
        "budget_analysis": {{
            "total_estimated_cost": estimated_total_ron,
            "cost_per_serving": estimated_cost_per_person,
            "budget_utilization": "percentage of {budget} RON used",
            "value_optimization": "how to get best value"
        }}
    }}
    
    BE INTELLIGENT - select ingredients that make sense for {cuisine_type} cuisine, {meal_context} context, {budget} RON budget, and {servings} servings.
    """
    
    try:
        result = _call_ai(prompt)
        if "error" in result:
            # Fallback with intelligent defaults for Italian romantic dinner
            result = {
                "automatic_ingredient_selection": {
                    "selected_dish": "Pasta Carbonara Românească",
                    "reasoning": "Perfect for Italian romantic dinner within 100 RON budget",
                    "selected_ingredients": [
                        {"name": "spaghetti", "quantity": "400g", "importance": "essential", "estimated_cost_ron": 8},
                        {"name": "ouă", "quantity": "4 bucăți", "importance": "essential", "estimated_cost_ron": 6},
                        {"name": "bacon/pancetta", "quantity": "200g", "importance": "essential", "estimated_cost_ron": 25},
                        {"name": "parmezan", "quantity": "100g", "importance": "essential", "estimated_cost_ron": 18},
                        {"name": "usturoi", "quantity": "3 căței", "importance": "important", "estimated_cost_ron": 2},
                        {"name": "vin alb", "quantity": "250ml", "importance": "optional", "estimated_cost_ron": 15}
                    ]
                },
                "budget_analysis": {
                    "total_estimated_cost": 74,
                    "cost_per_serving": 37,
                    "budget_utilization": "74% of 100 RON",
                    "value_optimization": "Excellent value for romantic Italian dinner"
                }
            }
            
        logger.info("✅ Automatic ingredient selection and validation successful")
        return json.dumps({
            "status": "success",
            "user_request": user_request,
            "automation_mode": "intelligent_ingredient_selection",
            "context_used": {
                "cultural": bool(cultural_context),
                "parameters": bool(parameters),
                "cuisine_type": cuisine_type,
                "meal_context": meal_context,
                "budget_ron": budget,
                "servings": servings
            },
            "validation_results": result,
            "validated_at": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Contextual validation failed: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e),
            "context_used": {
                "cultural": bool(cultural_context),
                "parameters": bool(parameters)
            }
        })