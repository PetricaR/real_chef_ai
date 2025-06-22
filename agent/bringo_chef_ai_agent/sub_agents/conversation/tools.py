# conversation_agent/tools.py
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')
logger = logging.getLogger("conversation_tools")

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
    logger.info("✅ Conversation agent AI client initialized")
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
                temperature=0.3,
                max_output_tokens=3000,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"AI call failed: {e}")
        return {"error": str(e)}

def format_recipe_presentation(recipe_json: str, cultural_context_json: str = "") -> str:
    """
    Format recipe results into beautiful, culturally-adapted presentation.
    """
    logger.info("🎨 Formatting recipe presentation...")
    
    try:
        recipe_data = json.loads(recipe_json) if recipe_json else {}
        cultural_data = json.loads(cultural_context_json) if cultural_context_json else {}
    except:
        return json.dumps({
            "status": "error",
            "message": "Invalid recipe or cultural context JSON"
        })
    
    if recipe_data.get("status") != "success":
        return json.dumps({
            "status": "error",
            "message": "Recipe creation failed, cannot format presentation"
        })
    
    # Extract recipe information
    recipe_info = recipe_data.get("recipe_data", {}).get("recipe", {})
    cost_analysis = recipe_data.get("recipe_data", {}).get("cost_analysis", {})
    
    # Extract cultural information for language adaptation
    language = "ro"  # default
    if cultural_data.get("status") == "success":
        lang_info = cultural_data.get("analysis", {}).get("language", {})
        language = lang_info.get("code", "ro")
    
    prompt = f"""
    Create a beautiful, engaging presentation for this recipe in {language}:
    
    Recipe: {json.dumps(recipe_info, indent=2)}
    Cost analysis: {json.dumps(cost_analysis, indent=2)}
    
    Create an attractive markdown presentation that includes:
    
    Return JSON with markdown content:
    {{
        "presentation": {{
            "markdown_content": "Full beautiful markdown presentation with emojis, tables, clear structure",
            "language_used": "{language}",
            "presentation_style": "warm|professional|casual",
            "key_highlights": ["main selling points of this recipe"],
            "next_steps_suggested": ["logical next actions for user"]
        }},
        "summary": {{
            "recipe_name": "recipe name with emoji",
            "total_cost": "cost in RON",
            "difficulty": "difficulty level",
            "time_required": "total time",
            "value_proposition": "why this recipe is great"
        }}
    }}
    
    Markdown should include:
    - Attractive header with recipe name and emoji
    - Key info table (cost, time, servings, difficulty)
    - Ingredients list with Bringo products and prices
    - Step-by-step instructions with timing
    - Cost breakdown table
    - Cultural notes and tips
    - Next steps (offer tutorial, variations, shopping tips)
    
    Make it visually appealing with proper markdown formatting, emojis, tables, and clear sections.
    """
    
    try:
        result = _call_ai(prompt)
        if "error" in result:
            raise ValueError(result["error"])
            
        logger.info("✅ Recipe presentation formatted successfully")
        return json.dumps({
            "status": "success",
            "presentation_data": result,
            "formatted_at": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Recipe presentation failed: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e),
            "fallback_presentation": {
                "markdown_content": f"# {recipe_info.get('name', 'Rețetă')} \n\nRețeta ta este gata!",
                "summary": {"recipe_name": recipe_info.get('name', 'Rețetă')}
            }
        })

def format_tutorial_presentation(tutorial_json: str) -> str:
    """
    Format tutorial results into beautiful presentation.
    """
    logger.info("🎨 Formatting tutorial presentation...")
    
    try:
        tutorial_data = json.loads(tutorial_json) if tutorial_json else {}
    except:
        return json.dumps({
            "status": "error",
            "message": "Invalid tutorial JSON"
        })
    
    if tutorial_data.get("status") != "success":
        return json.dumps({
            "status": "error",
            "message": "Tutorial creation failed, cannot format presentation"
        })
    
    prompt = f"""
    Create a beautiful presentation for this tutorial completion:
    
    Tutorial data: {json.dumps(tutorial_data, indent=2)}
    
    Create an engaging markdown presentation that celebrates the tutorial creation:
    
    Return JSON:
    {{
        "presentation": {{
            "markdown_content": "Beautiful markdown with tutorial summary, image gallery, step descriptions",
            "celebration_tone": "enthusiastic|professional|encouraging",
            "tutorial_highlights": ["key features of the tutorial"],
            "usage_suggestions": ["how user can best use this tutorial"]
        }},
        "summary": {{
            "tutorial_name": "tutorial name with emoji",
            "steps_created": "number of steps",
            "files_generated": "list of image files",
            "tutorial_value": "what makes this tutorial special"
        }}
    }}
    
    Include:
    - Celebratory header with tutorial completion
    - Tutorial overview table
    - Step-by-step breakdown with descriptions
    - Generated files list
    - How to use the tutorial
    - Recipe cost reminders
    - Encouragement and next steps
    """
    
    try:
        result = _call_ai(prompt)
        if "error" in result:
            raise ValueError(result["error"])
            
        logger.info("✅ Tutorial presentation formatted successfully")
        return json.dumps({
            "status": "success",
            "presentation_data": result,
            "formatted_at": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Tutorial presentation failed: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

def manage_conversation_context(user_message: str, previous_results_json: str = "") -> str:
    """
    Manage conversation flow and suggest next steps based on conversation context.
    """
    logger.info("💬 Managing conversation context...")
    
    try:
        previous_results = json.loads(previous_results_json) if previous_results_json else {}
    except:
        previous_results = {}
    
    prompt = f"""
    Analyze this conversation context and manage the flow:
    
    Current user message: "{user_message}"
    Previous results: {json.dumps(previous_results, indent=2)}
    
    Determine conversation state and suggest next actions:
    
    Return JSON:
    {{
        "conversation_analysis": {{
            "user_intent": "recipe_request|tutorial_request|follow_up|clarification|new_request",
            "conversation_stage": "initial|recipe_created|tutorial_offered|tutorial_created|completed",
            "user_satisfaction": "high|medium|low|unclear",
            "language_preference": "ro|en|de|etc"
        }},
        "context_management": {{
            "has_previous_recipe": true|false,
            "has_previous_tutorial": true|false,
            "can_offer_tutorial": true|false,
            "needs_clarification": true|false,
            "conversation_flow": "continue|restart|enhance|clarify"
        }},
        "next_steps": {{
            "immediate_action": "create_recipe|offer_tutorial|generate_tutorial|ask_clarification|provide_variations",
            "suggested_responses": ["specific response suggestions for user"],
            "conversation_hooks": ["ways to engage user further"],
            "value_adds": ["additional value we can provide"]
        }},
        "presentation_guidance": {{
            "tone": "enthusiastic|helpful|professional|encouraging",
            "format_preference": "markdown|simple|detailed|visual",
            "cultural_adaptation": "traditional|modern|neutral",
            "engagement_level": "high|medium|low"
        }}
    }}
    """
    
    try:
        result = _call_ai(prompt)
        if "error" in result:
            raise ValueError(result["error"])
            
        logger.info("✅ Conversation context managed successfully")
        return json.dumps({
            "status": "success",
            "context_analysis": result,
            "analyzed_at": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Conversation management failed: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e),
            "fallback_guidance": {
                "next_steps": {"immediate_action": "create_recipe"},
                "presentation_guidance": {"tone": "helpful", "format_preference": "markdown"}
            }
        })