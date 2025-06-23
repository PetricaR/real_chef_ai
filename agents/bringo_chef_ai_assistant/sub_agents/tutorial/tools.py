# tutorial/tools.py
import logging
import json
import asyncio
import re
from datetime import datetime
from google.adk.tools import ToolContext

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')
logger = logging.getLogger("tutorial_tools")

# Shared configuration
TEXT_MODEL = "gemini-2.0-flash"
IMAGE_MODEL = "imagen-3.0-generate-002"
PROJECT_ID = "formare-ai"
LOCATION = "europe-west4"

# Shared AI client
try:
    from google import genai
    from google.genai import types
    
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location=LOCATION
    )
    logger.info("✅ Tutorial agent AI client initialized")
except Exception as e:
    logger.error(f"❌ AI client failed: {e}")
    client = None

def _call_ai_text(prompt: str, temperature: float = 0.1) -> dict:
    """Simplified AI call for text generation"""
    if not client:
        return {"error": "AI client unavailable"}
    
    try:
        response = client.models.generate_content(
            model=TEXT_MODEL,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=3000,
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"AI text call failed: {e}")
        return {"error": str(e)}

def extract_recipe_from_context(conversation_context: str = "") -> str:
    """
    Extract the most recent successful recipe creation from conversation context.
    This enables auto-triggering of tutorial generation.
    """
    logger.info("🔍 Extracting recipe data from conversation context for auto-tutorial...")
    
    try:
        # Look for the most recent successful recipe creation in the conversation
        # Pattern to find JSON recipe data
        json_pattern = r'\{[^{}]*"status":\s*"success"[^{}]*"recipe_data"[^{}]*\}'
        
        # More robust pattern for nested JSON
        nested_pattern = r'\{(?:[^{}]|\{[^{}]*\})*"recipe_data"(?:[^{}]|\{[^{}]*\})*\}'
        
        matches = re.findall(nested_pattern, conversation_context, re.DOTALL)
        
        if not matches:
            # Fallback: look for simpler patterns
            simple_pattern = r'"recipe_data":\s*\{[^}]+\}'
            matches = re.findall(simple_pattern, conversation_context)
        
        if matches:
            # Try to parse the last match (most recent)
            latest_match = matches[-1]
            try:
                # If it's a partial match, try to reconstruct
                if not latest_match.startswith('{'):
                    latest_match = '{' + latest_match + '}'
                
                recipe_data = json.loads(latest_match)
                
                logger.info("✅ Successfully extracted recipe data from context")
                return json.dumps({
                    "status": "success",
                    "message": "Recipe data extracted from conversation context",
                    "recipe_data": recipe_data,
                    "auto_extracted": True,
                    "extracted_at": datetime.now().isoformat()
                })
                
            except json.JSONDecodeError:
                logger.warning("⚠️ Found recipe pattern but couldn't parse JSON")
        
        # If no recipe found, return appropriate response
        logger.info("📝 No recipe data found in context - requesting manual input")
        return json.dumps({
            "status": "no_recipe_found",
            "message": "Am primit controlul pentru tutorial, dar nu găsesc datele rețetei în context. Te rog să îmi transmiți JSON-ul cu rețeta creată sau să creezi mai întâi o rețetă.",
            "action_needed": "provide_recipe_data",
            "searched_at": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Error extracting recipe from context: {e}")
        return json.dumps({
            "status": "error",
            "message": f"Error extracting recipe data: {str(e)}",
            "action_needed": "provide_recipe_data_manually"
        })

def analyze_recipe_for_tutorial(recipe_json: str) -> str:
    """
    Analyze an already created recipe to determine tutorial suitability.
    Enhanced to handle auto-extracted recipe data.
    """
    logger.info("🧠 Analyzing recipe for tutorial creation...")
    
    try:
        recipe_data = json.loads(recipe_json) if recipe_json else {}
    except:
        return json.dumps({
            "status": "error",
            "message": "Invalid recipe JSON provided"
        })
    
    # Handle auto-extracted data
    if recipe_data.get("auto_extracted"):
        logger.info("📥 Processing auto-extracted recipe data")
        recipe_data = recipe_data.get("recipe_data", {})
    
    if recipe_data.get("status") != "success":
        return json.dumps({
            "status": "error",
            "message": "Invalid or failed recipe data provided"
        })
    
    # Extract recipe information from the correct structure
    recipe_info = recipe_data.get("recipe_data", {}).get("recipe", {})
    cost_analysis = recipe_data.get("recipe_data", {}).get("cost_analysis", {})
    
    # Fallback if structure is different
    if not recipe_info and "recipe" in recipe_data:
        recipe_info = recipe_data.get("recipe", {})
        cost_analysis = recipe_data.get("cost_analysis", {})
    
    if not recipe_info:
        return json.dumps({
            "status": "error",
            "message": "No recipe information found in data"
        })
    
    recipe_name = recipe_info.get("name", "Unknown Recipe")
    ingredients = recipe_info.get("ingredients", [])
    instructions = recipe_info.get("instructions", [])
    cuisine_type = recipe_info.get("cuisine_type", "international")
    
    prompt = f"""
    Analyze this specific recipe for visual tutorial creation suitability:
    
    Recipe Name: {recipe_name}
    Cuisine Type: {cuisine_type}
    Ingredients: {json.dumps(ingredients, indent=2)}
    Instructions: {json.dumps(instructions, indent=2)}
    Cost Analysis: {json.dumps(cost_analysis, indent=2)}
    
    Evaluate this SPECIFIC recipe for creating a 7-step visual cooking tutorial. Return JSON:
    {{
        "tutorial_suitability": {{
            "visual_score": <1-10 based on this specific recipe>,
            "learning_value": <1-10 for this recipe's techniques>,
            "step_clarity": <1-10 how clear steps can be shown>,
            "overall_score": <1-10 average>,
            "suitability": "excellent|good|fair|poor"
        }},
        "tutorial_advantages": {{
            "visual_appeal": "Why THIS recipe is visually interesting for tutorial",
            "learning_techniques": ["specific techniques this recipe teaches"],
            "step_visibility": "How well each step of THIS recipe can be demonstrated",
            "skill_development": "What cooking skills THIS recipe develops"
        }},
        "tutorial_challenges": {{
            "difficult_steps": ["steps in THIS recipe that might be hard to show"],
            "timing_issues": ["time-related challenges for THIS recipe"],
            "equipment_considerations": ["equipment needed for THIS recipe"]
        }},
        "tutorial_recommendations": {{
            "best_angles": ["recommended camera angles for THIS recipe"],
            "key_moments": ["most important moments to capture in THIS recipe"],
            "tip_opportunities": ["good moments for cooking tips in THIS recipe"]
        }}
    }}
    
    Focus specifically on THIS recipe: {recipe_name}, not generic cooking advice.
    """
    
    try:
        result = _call_ai_text(prompt)
        if "error" in result:
            # Provide a reasonable default analysis based on the actual recipe
            result = {
                "tutorial_suitability": {
                    "visual_score": 7,
                    "learning_value": 8,
                    "step_clarity": 7,
                    "overall_score": 7.5,
                    "suitability": "good"
                },
                "tutorial_advantages": {
                    "visual_appeal": f"Recipe {recipe_name} shows clear visual progression through cooking stages",
                    "learning_techniques": ["ingredient preparation", "cooking techniques", "presentation"],
                    "step_visibility": "Each cooking step shows distinct visual changes",
                    "skill_development": f"Develops skills needed for {cuisine_type} cuisine"
                },
                "tutorial_challenges": {
                    "difficult_steps": ["timing coordination"],
                    "timing_issues": ["some steps may require real-time demonstration"],
                    "equipment_considerations": ["standard kitchen equipment needed"]
                },
                "tutorial_recommendations": {
                    "best_angles": ["overhead view for preparation", "side view for cooking", "close-up for details"],
                    "key_moments": ["ingredient setup", "key cooking techniques", "final presentation"],
                    "tip_opportunities": ["ingredient tips", "technique guidance", "presentation suggestions"]
                }
            }
            
        logger.info("✅ Recipe tutorial analysis completed")
        return json.dumps({
            "status": "success",
            "recipe_name": recipe_name,
            "cuisine_type": cuisine_type,
            "analysis": result,
            "analyzed_at": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"❌ Recipe analysis failed: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

async def generate_visual_tutorial(recipe_json: str, tool_context: ToolContext) -> str:
    """
    Generate exactly 7 detailed tutorial images DYNAMICALLY from any recipe.
    Enhanced to handle auto-extracted recipe data and better error handling.
    """
    logger.info("🎨 Generating DYNAMIC 7-step visual tutorial from actual recipe...")
    
    try:
        recipe_data = json.loads(recipe_json)
    except:
        return json.dumps({
            "status": "error",
            "message": "Invalid recipe JSON provided"
        })
    
    # Handle auto-extracted data
    if recipe_data.get("auto_extracted"):
        logger.info("📥 Processing auto-extracted recipe data for tutorial generation")
        recipe_data = recipe_data.get("recipe_data", {})
    
    if recipe_data.get("status") != "success":
        return json.dumps({
            "status": "error", 
            "message": "Recipe creation failed, cannot create tutorial"
        })
    
    # Extract recipe information from the correct structure
    recipe_info = recipe_data.get("recipe_data", {}).get("recipe", {})
    cost_analysis = recipe_data.get("recipe_data", {}).get("cost_analysis", {})
    
    # Fallback if structure is different
    if not recipe_info and "recipe" in recipe_data:
        recipe_info = recipe_data.get("recipe", {})
        cost_analysis = recipe_data.get("cost_analysis", {})
    
    if not recipe_info:
        return json.dumps({
            "status": "error",
            "message": "No recipe information found in data"
        })
    
    recipe_name = recipe_info.get("name", "Unknown Recipe")
    ingredients = recipe_info.get("ingredients", [])
    instructions = recipe_info.get("instructions", [])
    cuisine_type = recipe_info.get("cuisine_type", "international")
    
    logger.info(f"Creating DYNAMIC tutorial for: {recipe_name}")
    
    # DYNAMIC tutorial steps generation based on the actual recipe
    tutorial_prompt = f"""
    Create exactly 7 detailed tutorial steps for this SPECIFIC recipe: {recipe_name}
    
    Recipe Details:
    Cuisine: {cuisine_type}
    Ingredients: {json.dumps(ingredients, indent=2)}
    Instructions: {json.dumps(instructions, indent=2)}
    
    Create 7 detailed image descriptions that follow this structure for THIS specific recipe:
    1. **Ingredient Setup** - All ingredients for {recipe_name} laid out and organized
    2. **Initial Preparation** - Chopping, measuring, prep work specific to {recipe_name}
    3. **Cooking Start** - Initial cooking setup for {recipe_name}
    4. **Main Cooking Stage** - Primary technique for {recipe_name}
    5. **Combination/Development** - Adding ingredients, building flavors for {recipe_name}
    6. **Finishing Stage** - Final touches, plating prep for {recipe_name}
    7. **Completed Dish** - Final {recipe_name} presentation
    
    Return JSON with exactly 7 detailed, SPECIFIC image descriptions:
    {{
        "tutorial_steps": [
            "Detailed description for step 1 specific to {recipe_name}...",
            "Detailed description for step 2 specific to {recipe_name}...",
            "Detailed description for step 3 specific to {recipe_name}...",
            "Detailed description for step 4 specific to {recipe_name}...",
            "Detailed description for step 5 specific to {recipe_name}...",
            "Detailed description for step 6 specific to {recipe_name}...",
            "Detailed description for step 7 specific to {recipe_name}..."
        ]
    }}
    
    Each description should be detailed and specific to THIS recipe: {recipe_name}, not generic.
    """
    
    try:
        tutorial_result = _call_ai_text(tutorial_prompt)
        if "error" in tutorial_result:
            raise ValueError(f"Failed to generate tutorial steps: {tutorial_result['error']}")
            
        tutorial_steps = tutorial_result.get("tutorial_steps", [])
        
        if len(tutorial_steps) != 7:
            raise ValueError(f"Expected 7 tutorial steps, got {len(tutorial_steps)}")
            
    except Exception as e:
        logger.error(f"Failed to generate dynamic tutorial steps: {e}")
        # Dynamic fallback based on actual recipe name and ingredients
        ingredient_names = [ing.get("name", "") for ing in ingredients if ing.get("name")]
        tutorial_steps = [
            f"All ingredients for {recipe_name} laid out and organized: {', '.join(ingredient_names[:5])} and other ingredients on a clean kitchen counter",
            f"Preparation stage for {recipe_name}: chopping and measuring ingredients according to recipe requirements",
            f"Initial cooking setup for {recipe_name}: proper equipment preparation and heat setup",
            f"Main cooking technique being demonstrated for {recipe_name} using the prepared ingredients",
            f"Adding and combining ingredients during the cooking process for {recipe_name}",
            f"Final cooking stage and plating preparation for {recipe_name}",
            f"Completed {recipe_name} beautifully plated and ready to serve"
        ]
    
    # Generate images for each tutorial step
    safe_name = "".join(c for c in recipe_name.lower() if c.isalnum() or c in ['_', '-'])[:20]
    successful_files = []
    
    step_names = [
        "01_ingredient_setup",
        "02_preparation", 
        "03_cooking_start",
        "04_main_cooking",
        "05_combination_stage",
        "06_finishing_touches",
        "07_completed_dish"
    ]
    
    for i, (step, step_name) in enumerate(zip(tutorial_steps, step_names)):
        try:
            image_prompt = f"""
            Professional cooking tutorial photography for {recipe_name} ({cuisine_type} cuisine) - Step {i+1} of 7:
            
            {step}
            
            Style: Clean, educational cooking photography with professional kitchen lighting.
            Show clear view of ingredients, techniques, and cooking progress for {recipe_name}.
            Consistent tutorial style with good detail visibility.
            High-quality food photography suitable for cooking instruction.
            {cuisine_type} cuisine authentic presentation and cooking methods.
            """
            
            filename = f"{safe_name}_{step_name}.png"
            
            # Generate image
            if client:
                try:
                    response = client.models.generate_images(
                        model=IMAGE_MODEL,
                        prompt=image_prompt,
                        config={'number_of_images': 1}
                    )
                    
                    if response.generated_images:
                        await tool_context.save_artifact(
                            filename,
                            types.Part.from_bytes(
                                data=response.generated_images[0].image.image_bytes,
                                mime_type='image/png'
                            )
                        )
                        successful_files.append(filename)
                        logger.info(f"✅ Generated tutorial step {i+1}/7: {step_name}")
                    
                    # Delay between generations to avoid rate limits
                    if i < len(tutorial_steps) - 1:
                        await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"❌ Failed to generate image for step {i+1}: {e}")
                    continue
            else:
                logger.error(f"❌ No AI client available for step {i+1}")
                continue
                    
        except Exception as e:
            logger.error(f"❌ Failed to generate image for step {i+1}: {e}")
            continue
    
    # Compile final result
    result = {
        "status": "success",
        "recipe_name": recipe_name,
        "cuisine_type": cuisine_type,
        "tutorial_type": "7-step dynamic visual cooking tutorial",
        "steps_generated": len(successful_files),
        "total_steps": 7,
        "generated_files": successful_files,
        "tutorial_steps": tutorial_steps,
        "step_names": step_names[:len(successful_files)],
        "recipe_details": {
            "total_cost_ron": cost_analysis.get("total_cost_ron", "N/A"),
            "cost_per_serving_ron": cost_analysis.get("cost_per_serving_ron", "N/A"),
            "prep_time": recipe_info.get("prep_time_minutes", "N/A"),
            "cook_time": recipe_info.get("cook_time_minutes", "N/A"),
            "servings": recipe_info.get("servings", "N/A"),
            "difficulty": recipe_info.get("difficulty", "N/A")
        },
        "original_recipe": recipe_info,
        "cost_analysis": cost_analysis,
        "generated_at": datetime.now().isoformat()
    }
    
    logger.info(f"✅ DYNAMIC tutorial completed: {len(successful_files)}/7 steps for {recipe_name}")
    return json.dumps(result, indent=2, ensure_ascii=False)