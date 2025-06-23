# recipe_creator/tools.py
import logging
import json
from datetime import datetime
import calendar

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')
logger = logging.getLogger("recipe_tools")

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
    logger.info("✅ Recipe agent AI client initialized")
except Exception as e:
    logger.error(f"❌ AI client failed: {e}")
    gemini_client = None

def _call_ai(prompt: str) -> dict:
    """Simplified AI call with higher token limit for recipes"""
    if not gemini_client:
        return {"error": "AI client unavailable"}
    
    try:
        response = gemini_client.models.generate_content(
            model=MODEL,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(
                temperature=0.3,  # Moderate creativity for recipes
                max_output_tokens=4000,  # More tokens for detailed recipes
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

def create_comprehensive_recipe(user_request: str, product_search_results_json: str) -> str:
    """
    Create a comprehensive recipe from product search results.
    """
    logger.info(f"👨‍🍳 Creating recipe for: {user_request[:50]}...")
    
    try:
        product_search_results = json.loads(product_search_results_json)
    except:
        return json.dumps({
            "status": "error",
            "message": "Invalid product search results JSON"
        })
    
    # Extract available products
    available_products = []
    search_results = product_search_results.get('search_results', [])
    for result in search_results:
        if result.get('status') == 'success':
            products = result.get('products', [])
            for product in products[:2]:  # Take top 2 products per ingredient
                available_products.append({
                    'ingredient': result.get('original_ingredient', ''),
                    'product_name': product['name'],
                    'price': product['price'],
                    'available': product['available']
                })
    
    current_season = _get_current_season()
    
    prompt = f"""
    Create a complete recipe for this request: "{user_request}"
    
    Available products:
    {json.dumps(available_products, indent=2)}
    
    Current season: {current_season}
    
    Create a practical, detailed recipe in alwasy in {user_request} languagec. Return JSON:
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
                "calories": calorii_estimate,
                "protein_g": proteine,
                "carbs_g": carbohidrați,
                "fat_g": grăsimi,
                "fiber_g": fibre
            }},
            "serving_suggestions": ["cum se servește"],
            "storage": "cum se păstrează",
            "variations": ["variații posibile"],
            "chef_notes": ["secrete profesionale"]
        }},
        "cost_analysis": {{
            "total_cost_ron": cost_total,
            "cost_per_serving_ron": cost_pe_porție,
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
    """
    Create recipe with full context adaptation.
    """
    logger.info(f"🌍 Creating contextualized recipe for: {user_request[:50]}...")
    
    try:
        product_search_results = json.loads(product_search_results_json)
    except:
        return json.dumps({
            "status": "error",
            "message": "Invalid product search results JSON"
        })
    
    # Parse all contexts
    parameters = {}
    cultural_context = {}
    ingredient_validations = {}
    
    try:
        if parameters_json:
            parameters = json.loads(parameters_json)
    except:
        logger.warning("Invalid parameters JSON")
        
    try:
        if cultural_context_json:
            cultural_context = json.loads(cultural_context_json)
    except:
        logger.warning("Invalid cultural context JSON")
        
    try:
        if ingredient_validations_json:
            ingredient_validations = json.loads(ingredient_validations_json)
    except:
        logger.warning("Invalid ingredient validations JSON")
    
    # Extract context information
    context_info = ""
    
    # Language and cultural info
    if cultural_context.get("status") == "success":
        analysis_list = cultural_context.get("analysis", [])
        # FIX: Handle the list structure correctly
        analysis_data = cultural_context.get("analysis", {})
        if isinstance(analysis_data, list) and analysis_data:
            analysis = analysis_data[0]
        elif isinstance(analysis_data, dict):
            analysis = analysis_data
        else:
            analysis = {}
            
        language = analysis.get("language", {})
        location = analysis.get("location", {})
        context_info += f"""
        Limbă: {language.get('name', 'Romanian')}
        Țară: {location.get('country', 'Romania')}
        Context cultural: {analysis.get('cultural_indicators', {})}
        """
    
    # Cooking parameters
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
    
    # Available products
    available_products = []
    search_results = product_search_results.get('search_results', [])
    for result in search_results:
        if result.get('status') == 'success':
            products = result.get('products', [])
            for product in products[:2]:
                available_products.append({
                    'ingredient': result.get('original_ingredient', ''),
                    'product_name': product['name'],
                    'price': product['price']
                })
    
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
            ... (same structure as comprehensive recipe)
        }},
        "cost_analysis": {{
            "total_cost_ron": cost_total,
            "cost_per_serving_ron": cost_pe_porție,
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