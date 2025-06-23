# agents/bringo_chef_ai_assistant/sub_agents/tutorial/tools.py
# Professional tutorial creation tools with async image generation and educational content development
# Dynamic tutorial generation adapted to any recipe type with cultural cooking methods

import asyncio
import logging
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from google.adk.tools import ToolContext

from ...shared.client import get_ai_client
from ...shared.models import TutorialData, TutorialStep, TutorialResponse
from ...shared.responses import create_success_response, create_error_response
from ...shared.config import settings

logger = logging.getLogger("tutorial_tools")


async def analyze_recipe_for_tutorial(recipe_json: str) -> str:
    """
    Analyze a recipe to determine tutorial suitability and generate tutorial strategy.
    
    Args:
        recipe_json: Complete recipe data from recipe creation agent
        
    Returns:
        JSON string containing tutorial analysis and recommendations
    """
    start_time = time.time()
    logger.info("🧠 Analyzing recipe for tutorial creation potential...")
    
    try:
        recipe_data = json.loads(recipe_json)
        
        if recipe_data.get("status") not in ["success"]:
            raise Exception("Invalid recipe data for tutorial analysis")
        
        # Extract recipe information
        recipe_info = recipe_data.get("data", {})
        
        if not recipe_info:
            raise Exception("No recipe data found for tutorial analysis")
        
        recipe_name = recipe_info.get("name", "Unknown Recipe")
        cuisine_type = recipe_info.get("cuisine_type", "international")
        difficulty = recipe_info.get("difficulty", "medium")
        ingredients = recipe_info.get("ingredients", [])
        instructions = recipe_info.get("instructions", [])
        
        logger.info(f"📋 Analyzing: {recipe_name} ({cuisine_type} cuisine)")
        
        # Create comprehensive tutorial analysis prompt
        analysis_prompt = f"""
        Analyze this specific recipe for visual cooking tutorial creation potential:
        
        Recipe Details:
        - Name: {recipe_name}
        - Cuisine Type: {cuisine_type}
        - Difficulty: {difficulty}
        - Ingredients: {len(ingredients)} items
        - Instructions: {len(instructions)} steps
        
        Detailed Recipe Information:
        {json.dumps(recipe_info, indent=2)[:2000]}  # Truncate for prompt size
        
        As a professional cooking tutorial specialist, evaluate this SPECIFIC recipe:
        
        1. **Visual Tutorial Potential Assessment**:
           - Evaluate specific cooking techniques used in THIS recipe
           - Assess visual transformation opportunities throughout cooking process
           - Identify key moments that benefit from visual demonstration
           - Determine educational value for home cooks learning THIS dish
        
        2. **Tutorial Structure Optimization**:
           - Identify the 7 most important visual moments for THIS specific recipe
           - Assess complexity and demonstration requirements for each technique
           - Evaluate ingredient preparation and cooking method visibility
           - Determine optimal camera angles and demonstration approaches
        
        3. **Educational Value Analysis**:
           - Identify specific cooking skills THIS recipe teaches
           - Assess technique difficulty and learning curve for home cooks
           - Evaluate cultural cooking methods and traditional techniques
           - Determine troubleshooting and quality indicator opportunities
        
        4. **Cultural and Cuisine-Specific Considerations**:
           - Analyze cultural cooking techniques specific to {cuisine_type} cuisine
           - Identify traditional methods and authentic preparation approaches
           - Assess cultural presentation and serving considerations
           - Evaluate adaptation requirements for modern home cooking
        
        Return detailed tutorial analysis:
        {{
            "tutorial_suitability": {{
                "visual_demonstration_score": score_1_to_10_for_this_recipe,
                "educational_value_score": score_1_to_10_for_learning_potential,
                "technique_clarity_score": score_1_to_10_for_visual_clarity,
                "cultural_authenticity_score": score_1_to_10_for_cultural_teaching,
                "overall_suitability_score": average_score,
                "suitability_rating": "excellent|good|fair|challenging"
            }},
            "tutorial_advantages": {{
                "visual_appeal_factors": ["specific_visual_elements_in_this_recipe"],
                "key_learning_techniques": ["specific_techniques_this_recipe_teaches"],
                "demonstration_opportunities": ["best_visual_moments_for_this_dish"],
                "cultural_education_value": ["cultural_elements_to_highlight"],
                "skill_building_potential": ["cooking_skills_developed"]
            }},
            "tutorial_structure_recommendation": {{
                "optimal_7_step_breakdown": [
                    "step_1_focus_for_this_recipe",
                    "step_2_focus_for_this_recipe", 
                    "step_3_focus_for_this_recipe",
                    "step_4_focus_for_this_recipe",
                    "step_5_focus_for_this_recipe",
                    "step_6_focus_for_this_recipe",
                    "step_7_focus_for_this_recipe"
                ],
                "critical_demonstration_moments": ["most_important_visual_moments"],
                "technique_highlight_priorities": ["key_techniques_to_emphasize"],
                "educational_progression": "how_tutorial_builds_skills"
            }},
            "production_considerations": {{
                "photography_challenges": ["potential_visual_challenges"],
                "equipment_requirements": ["special_equipment_needed"],
                "timing_considerations": ["time_sensitive_moments"],
                "cultural_sensitivity_notes": ["cultural_considerations"]
            }}
        }}
        
        Focus specifically on THIS recipe: "{recipe_name}" - not generic cooking advice.
        Provide actionable analysis for creating an effective tutorial for THIS specific dish.
        """
        
        # Use AI for recipe analysis
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=analysis_prompt,
            temperature=settings.conservative_temperature,
            agent_name="tutorial_agent"
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        analysis_data = json.loads(response.get("content", "{}"))
        processing_time = int((time.time() - start_time) * 1000)
        
        # Extract suitability score
        suitability_score = analysis_data.get("tutorial_suitability", {}).get("overall_suitability_score", 7.0)
        suitability_rating = analysis_data.get("tutorial_suitability", {}).get("suitability_rating", "good")
        
        logger.info(f"✅ Tutorial analysis completed in {processing_time}ms")
        logger.info(f"🎯 Suitability score: {suitability_score}/10 ({suitability_rating})")
        
        # Create analysis response
        response_obj = {
            "status": "success",
            "message": f"Tutorial analysis completed for {recipe_name}",
            "agent_name": "tutorial_agent",
            "processing_time_ms": processing_time,
            "recipe_name": recipe_name,
            "cuisine_type": cuisine_type,
            "suitability_score": suitability_score,
            "suitability_rating": suitability_rating,
            "analysis_data": analysis_data,
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(response_obj, ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Recipe tutorial analysis failed: {e}")
        
        # Create fallback analysis
        fallback_response = {
            "status": "warning",
            "message": f"Tutorial analysis partially failed: {str(e)}. Using conservative assessment.",
            "agent_name": "tutorial_agent",
            "processing_time_ms": processing_time,
            "suitability_score": 6.0,
            "suitability_rating": "fair",
            "analysis_data": {
                "tutorial_suitability": {
                    "overall_suitability_score": 6.0,
                    "suitability_rating": "fair"
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(fallback_response, ensure_ascii=False, indent=2)


async def generate_visual_tutorial(recipe_json: str, tool_context: ToolContext) -> str:
    """
    Generate a complete 7-step visual cooking tutorial from any recipe type.
    
    Args:
        recipe_json: Complete recipe data
        tool_context: Tool context for saving generated images
        
    Returns:
        JSON string containing complete tutorial with generated images
    """
    start_time = time.time()
    logger.info("🎨 Generating dynamic 7-step visual cooking tutorial...")
    
    try:
        recipe_data = json.loads(recipe_json)
        
        if recipe_data.get("status") != "success":
            raise Exception("Invalid recipe data for tutorial generation")
        
        recipe_info = recipe_data.get("data", {})
        
        if not recipe_info:
            raise Exception("No recipe data found for tutorial generation")
        
        recipe_name = recipe_info.get("name", "Unknown Recipe")
        cuisine_type = recipe_info.get("cuisine_type", "international")
        difficulty = recipe_info.get("difficulty", "medium")
        
        logger.info(f"🎯 Creating tutorial for: {recipe_name} ({cuisine_type})")
        
        # Generate dynamic tutorial steps using AI
        tutorial_steps = await _generate_dynamic_tutorial_steps(recipe_info)
        
        if not tutorial_steps or len(tutorial_steps) != 7:
            raise Exception(f"Failed to generate 7 tutorial steps, got {len(tutorial_steps) if tutorial_steps else 0}")
        
        # Generate images for each tutorial step
        generated_images = await _generate_tutorial_images(tutorial_steps, recipe_name, cuisine_type, tool_context)
        
        # Calculate success metrics
        successful_images = sum(1 for result in generated_images if result.get("success"))
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"✅ Tutorial generation completed in {processing_time}ms")
        logger.info(f"🎨 Generated {successful_images}/7 tutorial images")
        
        # Create tutorial data model
        tutorial_data = TutorialData(
            recipe_name=recipe_name,
            cuisine_type=cuisine_type,
            tutorial_type="7-step dynamic visual cooking tutorial",
            steps=tutorial_steps,
            generated_files=[result.get("filename") for result in generated_images if result.get("success")],
            total_steps=7,
            steps_completed=successful_images,
            tutorial_suitability_score=8.0,  # Good default score
            generation_notes=f"Successfully generated {successful_images}/7 tutorial images for {cuisine_type} cuisine"
        )
        
        # Create tutorial response
        response = TutorialResponse(
            status="success" if successful_images >= 5 else "warning",
            message=f"Generated {successful_images}/7 tutorial images for {recipe_name}",
            agent_name="tutorial_agent",
            processing_time_ms=processing_time,
            confidence_score=successful_images / 7.0,
            data=tutorial_data,
            tutorial_created=True,
            images_generated=successful_images
        )
        
        return response.model_dump_json(indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Tutorial generation failed: {e}")
        
        # Create error response
        error_response = TutorialResponse(
            status="error",
            message=f"Tutorial generation failed: {str(e)}",
            agent_name="tutorial_agent",
            processing_time_ms=processing_time,
            tutorial_created=False,
            images_generated=0
        )
        
        return error_response.model_dump_json(indent=2)


async def optimize_tutorial_for_learning(tutorial_json: str, learning_objectives: List[str] = None) -> str:
    """
    Optimize tutorial content for maximum educational value and learning outcomes.
    
    Args:
        tutorial_json: Generated tutorial data
        learning_objectives: Specific learning objectives to optimize for
        
    Returns:
        JSON string containing optimized tutorial with enhanced educational content
    """
    start_time = time.time()
    logger.info("📚 Optimizing tutorial for enhanced learning outcomes...")
    
    try:
        tutorial_data = json.loads(tutorial_json)
        
        if tutorial_data.get("status") not in ["success", "warning"]:
            raise Exception("Invalid tutorial data for optimization")
        
        existing_tutorial = tutorial_data.get("data", {})
        
        if not existing_tutorial:
            raise Exception("No tutorial data found for optimization")
        
        # Set default learning objectives if not provided
        if not learning_objectives:
            learning_objectives = [
                "basic_cooking_techniques",
                "ingredient_preparation",
                "timing_and_coordination",
                "quality_indicators",
                "cultural_cooking_methods"
            ]
        
        # Create learning optimization prompt
        optimization_prompt = f"""
        Optimize this cooking tutorial for maximum educational value and learning outcomes:
        
        Existing Tutorial: {json.dumps(existing_tutorial, indent=2)[:2000]}
        Learning Objectives: {learning_objectives}
        
        As a culinary education specialist, enhance this tutorial for optimal learning:
        
        1. **Educational Content Enhancement**:
           - Add specific learning objectives for each tutorial step
           - Include professional cooking tips and technique explanations
           - Provide quality indicators and visual cues for success
           - Add troubleshooting guidance for common issues
        
        2. **Skill Development Optimization**:
           - Structure tutorial for progressive skill building
           - Highlight transferable cooking techniques
           - Include professional chef secrets and methods
           - Emphasize technique mastery over recipe memorization
        
        3. **Cultural Education Integration**:
           - Include cultural context and cooking tradition explanations
           - Highlight authentic techniques and their significance
           - Explain ingredient selection and cultural preferences
           - Provide historical and cultural background where relevant
        
        4. **Practical Learning Support**:
           - Add timing guidance and workflow optimization
           - Include equipment recommendations and alternatives
           - Provide scaling instructions for different serving sizes
           - Add storage, reheating, and meal prep guidance
        
        Return optimized tutorial structure:
        {{
            "enhanced_tutorial": {{
                "learning_objectives": ["specific_skills_students_will_learn"],
                "educational_progression": "how_tutorial_builds_cooking_competence",
                "optimized_steps": [
                    {{
                        "step_number": 1,
                        "title": "enhanced_step_title_with_learning_focus",
                        "description": "enhanced_description_with_educational_content",
                        "learning_objective": "specific_skill_or_knowledge_gained",
                        "professional_tips": ["chef_techniques_and_secrets"],
                        "quality_indicators": ["visual_cues_for_success"],
                        "troubleshooting": ["common_issues_and_solutions"],
                        "cultural_notes": ["cultural_significance_and_context"]
                    }}
                ],
                "skill_development_summary": "overall_cooking_skills_developed",
                "cultural_education_value": "cultural_knowledge_gained"
            }},
            "learning_assessment": {{
                "beginner_friendliness": "how_suitable_for_cooking_beginners",
                "skill_transfer_potential": "how_skills_apply_to_other_recipes",
                "cultural_authenticity": "level_of_cultural_education_provided",
                "practical_application": "real_world_cooking_skill_development"
            }}
        }}
        
        Focus on creating an educational experience that builds lasting cooking skills and cultural appreciation.
        """
        
        # Use AI for tutorial optimization
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=optimization_prompt,
            temperature=settings.balanced_temperature,
            agent_name="tutorial_agent"
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        optimization_data = json.loads(response.get("content", "{}"))
        processing_time = int((time.time() - start_time) * 1000)
        
        logger.info(f"✅ Tutorial optimization completed in {processing_time}ms")
        
        # Create optimization response
        response_obj = {
            "status": "success",
            "message": "Tutorial optimized for enhanced learning outcomes",
            "agent_name": "tutorial_agent",
            "processing_time_ms": processing_time,
            "original_tutorial": existing_tutorial,
            "optimization_data": optimization_data,
            "learning_objectives": learning_objectives,
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(response_obj, ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Tutorial optimization failed: {e}")
        
        error_response = {
            "status": "error",
            "message": f"Tutorial optimization failed: {str(e)}",
            "agent_name": "tutorial_agent",
            "processing_time_ms": processing_time
        }
        
        return json.dumps(error_response, ensure_ascii=False, indent=2)


async def _generate_dynamic_tutorial_steps(recipe_info: Dict[str, Any]) -> List[TutorialStep]:
    """Generate dynamic tutorial steps based on specific recipe content"""
    
    recipe_name = recipe_info.get("name", "Recipe")
    cuisine_type = recipe_info.get("cuisine_type", "international")
    ingredients = recipe_info.get("ingredients", [])
    instructions = recipe_info.get("instructions", [])
    
    # Create dynamic step generation prompt
    step_prompt = f"""
    Generate exactly 7 detailed tutorial steps for this specific recipe: {recipe_name}
    
    Recipe Details:
    - Cuisine: {cuisine_type}
    - Ingredients: {json.dumps(ingredients[:10], indent=2)}
    - Instructions: {json.dumps(instructions[:10], indent=2)}
    
    Create 7 tutorial steps that are SPECIFIC to this recipe and cuisine type:
    
    Step 1 - Ingredient Setup & Organization: All ingredients for {recipe_name} laid out and organized
    Step 2 - Initial Preparation: Specific prep work needed for {recipe_name}
    Step 3 - Cooking Foundation: Equipment setup and initial cooking for {recipe_name}
    Step 4 - Critical Technique: Main cooking technique specific to {recipe_name}
    Step 5 - Flavor Development: Combining and developing flavors for {recipe_name}
    Step 6 - Finishing Touches: Final preparation and plating for {recipe_name}
    Step 7 - Final Presentation: Completed {recipe_name} ready to serve
    
    Return exactly 7 detailed tutorial steps:
    {{
        "tutorial_steps": [
            {{
                "step_number": 1,
                "title": "specific_title_for_this_recipe",
                "description": "detailed_description_specific_to_{recipe_name}",
                "image_prompt": "professional_cooking_tutorial_photography_prompt_for_this_step",
                "estimated_time_minutes": realistic_time_estimate,
                "key_techniques": ["specific_techniques_for_this_recipe"]
            }}
        ]
    }}
    
    Make each step SPECIFIC to {recipe_name} and {cuisine_type} cuisine - not generic cooking steps.
    """
    
    try:
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=step_prompt,
            temperature=settings.balanced_temperature,
            agent_name="tutorial_agent"
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        step_data = json.loads(response.get("content", "{}"))
        tutorial_steps_data = step_data.get("tutorial_steps", [])
        
        # Convert to TutorialStep models
        tutorial_steps = []
        for step_data in tutorial_steps_data:
            step = TutorialStep(
                step_number=step_data.get("step_number", 1),
                title=step_data.get("title", "Tutorial Step"),
                description=step_data.get("description", "Tutorial instruction"),
                image_prompt=step_data.get("image_prompt", "Cooking tutorial image"),
                estimated_time_minutes=step_data.get("estimated_time_minutes", 5),
                key_techniques=step_data.get("key_techniques", [])
            )
            tutorial_steps.append(step)
        
        return tutorial_steps
        
    except Exception as e:
        logger.error(f"❌ Dynamic step generation failed: {e}")
        
        # Fallback to generic tutorial steps
        return _create_fallback_tutorial_steps(recipe_info)


def _create_fallback_tutorial_steps(recipe_info: Dict[str, Any]) -> List[TutorialStep]:
    """Create fallback tutorial steps when AI generation fails"""
    recipe_name = recipe_info.get("name", "Recipe")
    cuisine_type = recipe_info.get("cuisine_type", "international")
    
    fallback_steps = [
        TutorialStep(
            step_number=1,
            title=f"Ingredient Setup for {recipe_name}",
            description=f"Organize all ingredients needed for {recipe_name} on a clean workspace",
            image_prompt=f"Professional cooking setup with all ingredients for {recipe_name} organized on counter",
            estimated_time_minutes=5,
            key_techniques=["mise_en_place", "organization"]
        ),
        TutorialStep(
            step_number=2,
            title=f"Preparation for {recipe_name}",
            description=f"Complete all necessary prep work for {recipe_name}",
            image_prompt=f"Ingredient preparation in progress for {recipe_name}",
            estimated_time_minutes=10,
            key_techniques=["knife_skills", "preparation"]
        ),
        TutorialStep(
            step_number=3,
            title=f"Cooking Setup for {recipe_name}",
            description=f"Prepare cooking equipment and begin initial cooking for {recipe_name}",
            image_prompt=f"Cooking equipment ready and initial cooking beginning for {recipe_name}",
            estimated_time_minutes=5,
            key_techniques=["equipment_setup", "heat_control"]
        ),
        TutorialStep(
            step_number=4,
            title=f"Main Cooking Technique",
            description=f"Execute the primary cooking method for {recipe_name}",
            image_prompt=f"Main cooking technique being demonstrated for {recipe_name}",
            estimated_time_minutes=15,
            key_techniques=["primary_cooking_method"]
        ),
        TutorialStep(
            step_number=5,
            title=f"Flavor Combination",
            description=f"Combine ingredients and develop flavors for {recipe_name}",
            image_prompt=f"Ingredients being combined and flavors developing for {recipe_name}",
            estimated_time_minutes=10,
            key_techniques=["flavor_development", "seasoning"]
        ),
        TutorialStep(
            step_number=6,
            title=f"Final Preparation",
            description=f"Complete final cooking and prepare for plating {recipe_name}",
            image_prompt=f"Final cooking stage and plating preparation for {recipe_name}",
            estimated_time_minutes=5,
            key_techniques=["finishing_techniques", "plating_prep"]
        ),
        TutorialStep(
            step_number=7,
            title=f"Completed {recipe_name}",
            description=f"Final presentation of completed {recipe_name}",
            image_prompt=f"Beautiful final presentation of completed {recipe_name} ready to serve",
            estimated_time_minutes=2,
            key_techniques=["presentation", "plating"]
        )
    ]
    
    return fallback_steps


async def _generate_tutorial_images(
    tutorial_steps: List[TutorialStep],
    recipe_name: str,
    cuisine_type: str,
    tool_context: ToolContext
) -> List[Dict[str, Any]]:
    """Generate tutorial images for all steps using async operations"""
    
    logger.info(f"🎨 Generating {len(tutorial_steps)} tutorial images for {recipe_name}")
    
    # Create image generation tasks
    generation_tasks = []
    for step in tutorial_steps:
        task = _generate_single_tutorial_image(step, recipe_name, cuisine_type, tool_context)
        generation_tasks.append(task)
    
    # Execute image generation concurrently with controlled concurrency
    semaphore = asyncio.Semaphore(3)  # Limit concurrent image generation
    
    async def limited_generation(task):
        async with semaphore:
            return await task
    
    # Execute with rate limiting
    results = []
    for i, task in enumerate(generation_tasks):
        try:
            result = await limited_generation(task)
            results.append(result)
            
            # Add delay between generations to respect rate limits
            if i < len(generation_tasks) - 1:
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"❌ Image generation failed for step {i+1}: {e}")
            results.append({
                "success": False,
                "error": str(e),
                "step_number": i + 1
            })
    
    return results


async def _generate_single_tutorial_image(
    step: TutorialStep,
    recipe_name: str,
    cuisine_type: str,
    tool_context: ToolContext
) -> Dict[str, Any]:
    """Generate a single tutorial image with professional prompt enhancement"""
    
    try:
        # Create safe filename
        safe_recipe_name = "".join(c for c in recipe_name.lower() if c.isalnum() or c in ['_', '-'])[:20]
        filename = f"{safe_recipe_name}_step_{step.step_number:02d}.png"
        
        # Enhance the image prompt for professional cooking tutorial photography
        enhanced_prompt = f"""
        Professional cooking tutorial photography for {recipe_name} ({cuisine_type} cuisine) - Step {step.step_number}/7:
        
        {step.image_prompt}
        
        Style: Clean, educational cooking photography with professional kitchen lighting. 
        Show clear view of ingredients, techniques, and cooking progress for {recipe_name}.
        High-quality food photography suitable for cooking instruction.
        Consistent tutorial style with excellent detail visibility.
        {cuisine_type} cuisine authentic presentation and cooking methods.
        Professional kitchen setup with proper lighting and composition.
        """
        
        # Generate image using AI client
        client = await get_ai_client()
        
        # Generate single image
        image_results = await client.generate_images(
            prompts=[enhanced_prompt],
            agent_name="tutorial_agent"
        )
        
        if not image_results or not image_results[0].get("image_data"):
            raise Exception("No image data generated")
        
        image_result = image_results[0]
        
        if image_result.get("error"):
            raise Exception(image_result["error"])
        
        # Save image using tool context
        from google.genai import types as genai_types
        
        await tool_context.save_artifact(
            filename,
            genai_types.Part.from_bytes(
                data=image_result["image_data"],
                mime_type='image/png'
            )
        )
        
        logger.info(f"✅ Generated tutorial image for step {step.step_number}: {filename}")
        
        return {
            "success": True,
            "filename": filename,
            "step_number": step.step_number,
            "step_title": step.title
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to generate image for step {step.step_number}: {e}")
        return {
            "success": False,
            "error": str(e),
            "step_number": step.step_number
        }