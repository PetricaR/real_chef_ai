# recipe_creator/tools.py

import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')
logger = logging.getLogger("recipe_tools")

# Shared configuration
MODEL = "gemini-2.0-flash"
PROJECT_ID = "formare-ai"
LOCATION = "europe-west4"

# Initialize AI client
try:
    from google import genai
    from google.genai import types

    gemini_client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )
    logger.info("✅ Recipe agent AI client initialized")
except Exception as e:
    logger.error(f"❌ AI client failed: {e}")
    gemini_client = None


def _call_ai(prompt: str) -> dict:
    """Simplified AI call with higher token limit for recipes"""
    if not gemini_client:
        logger.warning("Gemini client not initialized")
        return {"error": "AI client unavailable"}

    try:
        response = gemini_client.models.generate_content(
            model=MODEL,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=4000,
                response_mime_type="application/json"
            )
        )
        text = getattr(response, "text", None)
        if not text:
            raise ValueError("AI response has no text")
        return json.loads(text)
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


def _extract_available_products(product_search_results):
    """Helper to extract up to 2 products per ingredient"""
    available_products = []
    for result in product_search_results.get('search_results', []):
        if result.get('status') == 'success':
            for product in result.get('products', [])[:2]:
                available_products.append({
                    'ingredient': result.get('original_ingredient', ''),
                    'product_name': product['name'],
                    'price': product['price'],
                    'available': product.get('available', True)
                })
    return available_products


def create_comprehensive_recipe(user_request: str, product_search_results_json: str) -> str:
    """Create a complete recipe from product search results"""
    logger.info(f"👨‍🍳 Creating recipe for: {user_request[:50]}...")

    try:
        product_search_results = json.loads(product_search_results_json)
    except json.JSONDecodeError:
        return json.dumps({
            "status": "error",
            "message": "Invalid product search results JSON"
        })

    available_products = _extract_available_products(product_search_results)
    current_season = _get_current_season()

    prompt = f"""
    Create a complete recipe for this request: "{user_request}"

    Available products:
    {json.dumps(available_products, indent=2)}

    Current season: {current_season}

    Create a practical, detailed recipe in the user's language.
    Return JSON:
    {{
        "recipe": {{
            "name": "Nume rețetă cu emoji 🍽️",
            "description": "Descriere atrăgătoare 2-3 propoziții",
            "cuisine_type": "românească|italiană|etc",
            "difficulty": "ușor|mediu|avansat",
            "prep_time_minutes": 15,
            "cook_time_minutes": 30,
            "total_time_minutes": 45,
            "servings": 4,
            "ingredients": [
                {{
                    "name": "ingredient",
                    "quantity": "cantitate",
                    "unit": "unitate",
                    "product_recommendation": "produsul specific găsit",
                    "price_ron": preț,
                    "preparation": "cum se pregătește"
                }}
            ],
            "equipment": ["ustensile necesare"],
            "instructions": [
                {{
                    "step": 1,
                    "description": "Instrucțiune detaliată pas cu pas",
                    "time_minutes": 5,
                    "technique": "tehnica folosită",
                    "tips": "sfat profesional"
                }}
            ],
            "nutrition_per_serving": {{
                "calories": 0,
                "protein_g": 0,
                "carbs_g": 0,
                "fat_g": 0,
                "fiber_g": 0
            }},
            "serving_suggestions": ["cum se servește"],
            "storage": "cum se păstrează",
            "variations": ["variații posibile"],
            "chef_notes": ["secrete profesionale"]
        }},
        "cost_analysis": {{
            "total_cost_ron": 0,
            "cost_per_serving_ron": 0,
            "budget_efficiency": "foarte bun|bun|moderat|scump"
        }}
    }}
    """

    try:
        result = _call_ai(prompt)
        if "error" in result:
            raise ValueError(result["error"])

        logger.info("✅ Recipe creation successful")
        return json.dumps({
            "status": "success",
            "user_request": user_request,
            "recipe_data": result,
            "available_products_used": len(available_products),
            "created_at": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ Recipe creation failed: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e),
            "fallback_recipe": {
                "name": "Rețetă simplă",
                "description": "O rețetă de bază bazată pe ingredientele disponibile",
                "instructions": ["Combinați ingredientele găsite", "Gătiți după preferințe"]
            }
        })


def create_recipe_with_context(user_request: str,
                               product_search_results_json: str,
                               parameters_json: str,
                               cultural_context_json: str,
                               ingredient_validations_json: str) -> str:
    """Create recipe with full context adaptation"""
    logger.info(f"🌍 Creating contextualized recipe for: {user_request[:50]}...")

    try:
        product_search_results = json.loads(product_search_results_json)
    except json.JSONDecodeError:
        return json.dumps({
            "status": "error",
            "message": "Invalid product search results JSON"
        })

    try:
        parameters = json.loads(parameters_json) if parameters_json else {}
    except json.JSONDecodeError:
        logger.warning("Invalid parameters JSON")
        parameters = {}

    try:
        cultural_context = json.loads(cultural_context_json) if cultural_context_json else {}
    except json.JSONDecodeError:
        logger.warning("Invalid cultural context JSON")
        cultural_context = {}

    try:
        ingredient_validations = json.loads(ingredient_validations_json) if ingredient_validations_json else {}
    except json.JSONDecodeError:
        logger.warning("Invalid ingredient validations JSON")
        ingredient_validations = {}

    # Cultural & contextual info
    context_info = ""
    analysis = {}

    if cultural_context.get("status") == "success":
        analysis_data = cultural_context.get("analysis", {})
        if isinstance(analysis_data, list) and analysis_data:
            analysis = analysis_data[0]
        elif isinstance(analysis_data, dict):
            analysis = analysis_data
        language = analysis.get("language", {})
        location = analysis.get("location", {})
        context_info += f"""
        Limbă: {language.get('name', 'Romanian')}
        Țară: {location.get('country', 'Romania')}
        Context cultural: {analysis.get('cultural_indicators', {})}
        """

    if parameters.get("status") == "success":
        extracted = parameters.get("extracted_parameters", {})
        budget = extracted.get("budget", {})
        servings = extracted.get("servings", {})
        time_info = extracted.get("time", {})
        dietary = extracted.get("dietary", {})
        context_info += f"""
        Porții: {servings.get('count', 4)}
        Buget: {budget.get('amount_ron', 50)} RON
        Timp disponibil: {time_info.get('minutes', 60)} minute
        Restricții dietetice: {dietary.get('restrictions', [])}
        """

    available_products = _extract_available_products(product_search_results)
    current_season = _get_current_season()

    prompt = f"""
    Create a culturally adapted, personalized recipe for: "{user_request}"

    Context:
    {context_info}

    Available products:
    {json.dumps(available_products, indent=2)}

    Season: {current_season}

    Adapt the recipe to:
    - Cultural cooking traditions and language preferences
    - Budget and serving constraints
    - Time limitations
    - Dietary restrictions
    - Seasonal considerations

    Return JSON with same structure as create_comprehensive_recipe but with:
    - Culturally appropriate cooking techniques
    - Budget-optimized ingredient usage
    - Time-efficient preparation methods
    - Dietary adaptations
    - Cultural serving suggestions

    {{
        "recipe": {{
            "name": "Culturally appropriate name with emoji",
            "cultural_authenticity": "traditional|adapted|fusion",
            "budget_optimizations": ["how recipe saves money"],
            "time_optimizations": ["how recipe saves time"],
            "cultural_notes": ["cultural significance and traditions"],
            ...
        }},
        "cost_analysis": {{
            "total_cost_ron": 0,
            "cost_per_serving_ron": 0,
            "budget_efficiency": "foarte bun|bun|moderat|scump"
        }},
        "adaptations_made": {{
            "cultural": ["cultural adaptations"],
            "budget": ["budget adaptations"],
            "time": ["time adaptations"],
            "dietary": ["dietary adaptations"]
        }}
    }}
    """

    try:
        result = _call_ai(prompt)
        if "error" in result:
            raise ValueError(result["error"])

        logger.info("✅ Contextualized recipe creation successful")
        return json.dumps({
            "status": "success",
            "user_request": user_request,
            "context_used": {
                "parameters": bool(parameters),
                "cultural_context": bool(cultural_context),
                "ingredient_validations": bool(ingredient_validations)
            },
            "recipe_data": result,
            "created_at": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)

    except Exception as e:
        logger.error(f"❌ Contextualized recipe creation failed: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e),
            "context_used": {
                "parameters": bool(parameters),
                "cultural_context": bool(cultural_context),
                "ingredient_validations": bool(ingredient_validations)
            }
        })
