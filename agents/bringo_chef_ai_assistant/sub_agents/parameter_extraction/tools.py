# parameter_extraction/tools.py
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')
logger = logging.getLogger("parameter_tools")

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
    logger.info("✅ Parameter agent AI client initialized")
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
                max_output_tokens=1500,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"AI call failed: {e}")
        return {"error": str(e)}

def extract_cooking_parameters(user_request: str) -> str:
    """
    Extract cooking parameters from user request.
    """
    logger.info(f"📊 Extracting parameters from: {user_request[:50]}...")
    
    prompt = f"""
    Extract cooking parameters from: "{user_request}"
    
    Return JSON:
    {{
        "budget": {{
            "amount_ron": estimated_amount,
            "confidence": "high|medium|low",
            "explicit": true|false
        }},
        "servings": {{
            "count": estimated_count,
            "confidence": "high|medium|low",
            "explicit": true|false
        }},
        "time": {{
            "minutes": estimated_minutes,
            "urgency": "immediate|today|flexible",
            "confidence": "high|medium|low"
        }},
        "meal": {{
            "type": "breakfast|lunch|dinner|snack",
            "occasion": "everyday|special|comfort",
            "confidence": "high|medium|low"
        }},
        "dietary": {{
            "restrictions": ["vegetarian", "gluten-free", etc],
            "preferences": ["healthy", "low-carb", etc],
            "confidence": "high|medium|low"
        }},
        "difficulty": {{
            "level": "easy|medium|hard",
            "confidence": "high|medium|low"
        }}
    }}
    """
    
    try:
        result = _call_ai(prompt)
        if "error" in result:
            raise ValueError(result["error"])
            
        logger.info("✅ Parameter extraction successful")
        return json.dumps({
            "status": "success",
            "user_request": user_request,
            "extracted_parameters": result,
            "extracted_at": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Parameter extraction failed: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e),
            "fallback_parameters": {
                "budget": {"amount_ron": 50.0, "confidence": "low"},
                "servings": {"count": 4, "confidence": "low"},
                "time": {"minutes": 60, "confidence": "low"},
                "meal": {"type": "lunch", "confidence": "low"}
            }
        })

def extract_parameters_with_culture(user_request: str, cultural_context_json: str) -> str:
    """Extract cooking parameters with cultural context"""
    logger.info(f"🌍 Extracting parameters with culture for: {user_request[:50]}...")
    
    try:
        cultural_data = json.loads(cultural_context_json)
        
        # FIX: Handle the list structure correctly
        analysis_data = cultural_data.get("analysis", {})
        if isinstance(analysis_data, list) and analysis_data:
            analysis = analysis_data[0]
        elif isinstance(analysis_data, dict):
            analysis = analysis_data
        else:
            analysis = {}
        
        # Now these will work correctly
        language = analysis.get("language", {})
        location = analysis.get("location", {})
        cultural_indicators = analysis.get("cultural_indicators", {})
        
        # Rest of your existing AI logic here...
        prompt = f"""
        Extract cooking parameters from: "{user_request}"
        
        Cultural context:
        - Language: {language.get('name', 'Romanian')}
        - Location: {location.get('country', 'Romania')}
        - Context: {cultural_indicators.get('meal_context', 'casual')}
        
        Return JSON with budget, servings, cuisine_type, meal_context, etc.
        """
        
        result = _call_ai(prompt)
        
        if "error" in result:
            # Your existing fallback logic
            pass
            
        logger.info("✅ Parameter extraction successful")
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Parameter extraction failed: {e}")
        # Your existing error handling
        return json.dumps({"error": str(e)}, ensure_ascii=False)