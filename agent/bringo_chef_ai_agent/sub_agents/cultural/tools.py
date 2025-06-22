# cultural_agent/tools.py
import logging
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')
logger = logging.getLogger("cultural_tools")

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
    logger.info("✅ Cultural agent AI client initialized")
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

def detect_language_and_culture(user_request: str) -> str:
    """
    Detect language, country, and basic cultural context from culinary request.
    """
    logger.info(f"🌍 Detecting language and culture for: {user_request[:50]}...")
    
    prompt = f"""
    Analyze this culinary request for language and cultural context: "{user_request}"
    
    Return JSON:
    {{
        "language": {{
            "code": "ro|en|de|hu",
            "name": "Romanian|English|German|Hungarian",
            "confidence": 0.95,
            "dialect": "moldovan|transylvanian|etc or null"
        }},
        "location": {{
            "country": "Romania|Germany|Hungary|etc",
            "region": "Transilvania|Moldavia|etc or null",
            "confidence": 0.90
        }},
        "cultural_indicators": {{
            "cuisine_style": "traditional|modern|fusion",
            "meal_context": "family|individual|formal|casual",
            "cooking_approach": "rustic|refined|quick|elaborate"
        }}
    }}
    """
    
    try:
        result = _call_ai(prompt)
        if "error" in result:
            raise ValueError(result["error"])
            
        logger.info("✅ Language and culture detection successful")
        return json.dumps({
            "status": "success",
            "user_request": user_request,
            "analysis": result,
            "analyzed_at": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Detection failed: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e),
            "fallback": {
                "language": {"code": "ro", "confidence": 0.5},
                "location": {"country": "Romania", "confidence": 0.5}
            }
        })

def analyze_cultural_context(user_request: str) -> str:
    """
    Analyze deeper cultural context and traditional dishes.
    """
    logger.info(f"🎭 Analyzing cultural context for: {user_request[:50]}...")
    
    prompt = f"""
    Analyze cultural food context in this request: "{user_request}"
    
    Return JSON:
    {{
        "traditional_dishes": [
            {{
                "name": "dish_name",
                "origin": "country/region",
                "confidence": 0.85,
                "cultural_significance": "brief explanation"
            }}
        ],
        "cultural_patterns": {{
            "budget_consciousness": "high|medium|low",
            "time_approach": "quick|moderate|slow",
            "social_dining": "individual|family|community",
            "health_focus": "traditional|modern|mixed"
        }},
        "dietary_culture": {{
            "meat_preference": "high|medium|low",
            "seasonal_awareness": "high|medium|low",
            "traditional_ingredients": ["ingredient1", "ingredient2"]
        }}
    }}
    """
    
    try:
        result = _call_ai(prompt)
        if "error" in result:
            raise ValueError(result["error"])
            
        logger.info("✅ Cultural context analysis successful")
        return json.dumps({
            "status": "success",
            "user_request": user_request,
            "analysis": result,
            "analyzed_at": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Cultural analysis failed: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e),
            "fallback": {
                "cultural_patterns": {
                    "budget_consciousness": "medium",
                    "social_dining": "family"
                }
            }
        })