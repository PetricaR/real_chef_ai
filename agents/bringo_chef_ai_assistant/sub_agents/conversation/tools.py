# agents/bringo_chef_ai_assistant/sub_agents/conversation/tools.py
# Professional conversation management and presentation tools
# Beautiful markdown presentation creation and intelligent conversation flow management

import asyncio
import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

from ...shared.client import get_ai_client
from ...shared.models import ConversationResponse
from ...shared.responses import create_success_response, create_error_response
from ...shared.config import settings

logger = logging.getLogger("conversation_tools")


async def create_recipe_presentation(
    recipe_json: str,
    cultural_context_json: str = "",
    product_search_json: str = ""
) -> str:
    """
    Create a beautiful, comprehensive presentation for a completed recipe.
    
    Args:
        recipe_json: Complete recipe data from recipe creation agent
        cultural_context_json: Cultural context for personalization
        product_search_json: Product search results for pricing display
        
    Returns:
        JSON string containing beautiful recipe presentation
    """
    start_time = time.time()
    logger.info("🎨 Creating beautiful recipe presentation...")
    
    try:
        # Parse recipe data
        recipe_data = json.loads(recipe_json)
        
        if recipe_data.get("status") != "success":
            raise Exception("Invalid recipe data for presentation")
        
        recipe_info = recipe_data.get("data", {})
        
        if not recipe_info:
            raise Exception("No recipe data found for presentation")
        
        # Parse additional context
        cultural_context = {}
        product_data = {}
        
        if cultural_context_json:
            try:
                cultural_data = json.loads(cultural_context_json)
                if cultural_data.get("status") == "success":
                    cultural_context = cultural_data.get("data", {})
            except Exception as e:
                logger.warning(f"⚠️ Could not parse cultural context: {e}")
        
        if product_search_json:
            try:
                product_search_data = json.loads(product_search_json)
                if product_search_data.get("status") == "success":
                    product_data = product_search_data
            except Exception as e:
                logger.warning(f"⚠️ Could not parse product search data: {e}")
        
        # Create comprehensive presentation prompt
        presentation_prompt = f"""
        Create a beautiful, engaging presentation for this completed recipe:
        
        Recipe Data: {json.dumps(recipe_info, indent=2)[:2000]}
        Cultural Context: {json.dumps(cultural_context, indent=2)[:500]}
        Product Search Results: {json.dumps(product_data.get("shopping_analysis", {}), indent=2)[:500]}
        
        As a professional presentation specialist, create an engaging markdown presentation that:
        
        1. **Celebrates Achievement**: Highlight the successful recipe creation
        2. **Showcases Value**: Emphasize cost benefits and quality achieved
        3. **Provides Clarity**: Present all information in scannable, organized format
        4. **Motivates Action**: Inspire the user to cook this recipe
        5. **Cultural Respect**: Acknowledge cultural elements appropriately
        
        Create a comprehensive markdown presentation:
        {{
            "presentation_markdown": "Complete beautiful markdown presentation",
            "key_highlights": ["main selling points and achievements"],
            "value_propositions": ["cost benefits and practical advantages"],
            "cultural_elements": ["cultural significance and traditions highlighted"],
            "next_step_suggestions": ["logical next actions for the user"],
            "engagement_factors": ["elements that make this presentation compelling"]
        }}
        
        Presentation Structure Requirements:
        
        # 🍽️ [Recipe Name with Emoji]
        
        **✅ Recipe Successfully Created!**
        
        ## 📊 Recipe Overview
        | Metric | Value |
        |--------|-------|
        | **Total Cost** | [Real cost in RON] |
        | **Cost per Serving** | [Per person cost] |
        | **Prep Time** | [Preparation time] |
        | **Cook Time** | [Cooking time] |
        | **Difficulty** | [Skill level] |
        | **Serves** | [Number of people] |
        | **Cuisine** | [Cultural style] |
        
        ## 🛒 Shopping List with Real Prices
        
        ### Essential Ingredients
        [Detailed ingredient list with actual Bringo.ro products and prices]
        
        ### Optional Enhancements
        [Optional ingredients for upgrades]
        
        ## 👨‍🍳 Cooking Instructions
        
        ### [Step-by-step cooking instructions with timing and tips]
        
        ## 🎯 What You've Accomplished
        
        ✅ **Recipe Created**: [Achievement description]
        ✅ **Budget Optimized**: [Budget success story]
        ✅ **Cultural Authenticity**: [Cultural respect achieved]
        ✅ **Market Research**: [Product finding success]
        
        ## 🚀 Ready for Next Steps?
        
        ### Option 1: Create Visual Tutorial 🎨
        [Tutorial creation offer]
        
        ### Option 2: Explore Variations 🔄
        [Recipe variation suggestions]
        
        ### Option 3: Start New Recipe 🆕
        [New recipe suggestions]
        
        ---
        
        **💡 Pro Tip**: [Compelling value statement about this recipe]
        
        Use professional markdown formatting with:
        - Rich emoji usage for visual appeal
        - Clear table formatting for data
        - Proper headers and sections
        - Bullet points and numbered lists
        - Emphasis (bold, italic) for key information
        - Scannable visual hierarchy
        
        Make this presentation feel like a celebration of achievement while providing practical value.
        """
        
        # Use AI for presentation creation
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=presentation_prompt,
            temperature=settings.creative_temperature,
            agent_name="conversation_agent"
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        presentation_data = json.loads(response.get("content", "{}"))
        processing_time = int((time.time() - start_time) * 1000)
        
        # Extract key information
        recipe_name = recipe_info.get("name", "Your Recipe")
        total_cost = recipe_info.get("cost_analysis", {}).get("total_cost_ron", 0)
        servings = recipe_info.get("servings", 4)
        
        logger.info(f"✅ Recipe presentation created in {processing_time}ms")
        logger.info(f"🍽️ Presented: {recipe_name}")
        logger.info(f"💰 Total cost: {total_cost} RON for {servings} servings")
        
        # Create conversation response
        response_obj = ConversationResponse(
            status="success",
            message=f"Beautiful recipe presentation created for {recipe_name}",
            agent_name="conversation_agent",
            processing_time_ms=processing_time,
            confidence_score=0.95,
            presentation_content=presentation_data.get("presentation_markdown", ""),
            suggested_next_steps=presentation_data.get("next_step_suggestions", [
                "Create visual cooking tutorial",
                "Explore recipe variations", 
                "Start new recipe"
            ]),
            conversation_stage="recipe_completed"
        )
        
        # Add presentation analysis
        response_dict = response_obj.dict()
        response_dict["presentation_analysis"] = {
            "key_highlights": presentation_data.get("key_highlights", []),
            "value_propositions": presentation_data.get("value_propositions", []),
            "cultural_elements": presentation_data.get("cultural_elements", []),
            "engagement_factors": presentation_data.get("engagement_factors", [])
        }
        
        return json.dumps(response_dict, ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Recipe presentation creation failed: {e}")
        
        # Create fallback presentation
        fallback_response = ConversationResponse(
            status="warning",
            message=f"Recipe presentation partially created: {str(e)}",
            agent_name="conversation_agent",
            processing_time_ms=processing_time,
            presentation_content="# 🍽️ Your Recipe is Ready!\n\nYour recipe has been successfully created. All the cooking details are available above.",
            suggested_next_steps=["Create visual tutorial", "Explore variations"],
            conversation_stage="recipe_completed"
        )
        
        return fallback_response.model_dump_json(indent=2)


async def create_tutorial_presentation(tutorial_json: str) -> str:
    """
    Create a beautiful presentation celebrating tutorial creation and showcasing results.
    
    Args:
        tutorial_json: Complete tutorial data from tutorial agent
        
    Returns:
        JSON string containing beautiful tutorial presentation
    """
    start_time = time.time()
    logger.info("🎨 Creating tutorial achievement presentation...")
    
    try:
        tutorial_data = json.loads(tutorial_json)
        
        if tutorial_data.get("status") not in ["success", "warning"]:
            raise Exception("Invalid tutorial data for presentation")
        
        tutorial_info = tutorial_data.get("data", {})
        
        if not tutorial_info:
            raise Exception("No tutorial data found for presentation")
        
        # Create tutorial presentation prompt
        tutorial_presentation_prompt = f"""
        Create a celebratory presentation for this completed visual cooking tutorial:
        
        Tutorial Data: {json.dumps(tutorial_info, indent=2)[:1500]}
        Tutorial Stats: 
        - Images Generated: {tutorial_data.get('images_generated', 0)}
        - Tutorial Created: {tutorial_data.get('tutorial_created', False)}
        - Recipe Name: {tutorial_info.get('recipe_name', 'Unknown')}
        - Cuisine Type: {tutorial_info.get('cuisine_type', 'International')}
        
        Create an achievement celebration presentation:
        {{
            "celebration_markdown": "Comprehensive tutorial achievement presentation",
            "achievement_highlights": ["specific accomplishments to celebrate"],
            "tutorial_value": ["educational and practical value provided"],
            "usage_guidance": ["how to best use this tutorial"],
            "learning_outcomes": ["cooking skills gained from this tutorial"]
        }}
        
        Presentation Structure:
        
        # 🎥 Visual Cooking Tutorial Created! 
        
        ## 🎉 Congratulations - Your Tutorial is Ready!
        
        **✅ Successfully Generated Professional Cooking Tutorial**
        
        ### 📹 Tutorial Overview
        | Feature | Details |
        |---------|---------|
        | **Recipe** | [Recipe name with emoji] |
        | **Cuisine Style** | [Cultural cuisine type] |
        | **Tutorial Steps** | [Number] professional images |
        | **Learning Focus** | [Main cooking skills taught] |
        | **Difficulty Level** | [Skill level] |
        | **Estimated Tutorial Time** | [Total time to follow] |
        
        ### 🎯 What Your Tutorial Includes
        
        #### Step-by-Step Visual Guide
        [Description of tutorial progression and learning journey]
        
        #### Professional Cooking Techniques
        [Key techniques demonstrated in the tutorial]
        
        #### Cultural Cooking Methods
        [Cultural elements and traditional techniques shown]
        
        ### 📚 Learning Outcomes
        
        **After completing this tutorial, you'll master:**
        - [Specific cooking skill 1]
        - [Specific cooking skill 2]
        - [Cultural cooking technique]
        - [Professional chef method]
        
        ### 🎨 Generated Tutorial Images
        [List and description of generated tutorial files]
        
        ### 🚀 How to Use Your Tutorial
        
        1. **Follow Step-by-Step**: Use images as visual guides while cooking
        2. **Practice Techniques**: Focus on mastering each demonstrated technique
        3. **Build Skills**: Apply learned methods to other recipes
        4. **Share Knowledge**: Teach others using your visual tutorial
        
        ### 🌟 What You've Achieved
        
        ✅ **Professional Tutorial**: Created restaurant-quality visual cooking guide
        ✅ **Skill Building**: Developed transferable cooking techniques  
        ✅ **Cultural Learning**: Gained authentic cultural cooking knowledge
        ✅ **Visual Learning**: Enhanced cooking understanding through professional images
        
        ### 🎯 Ready for More Cooking Adventures?
        
        #### Option 1: Try Your Tutorial 👨‍🍳
        Cook the recipe using your visual guide
        
        #### Option 2: Create Recipe Variations 🔄  
        Adapt the recipe with different ingredients
        
        #### Option 3: Explore New Cuisines 🌍
        Create tutorials for different cultural cuisines
        
        ---
        
        **🌟 Amazing Work!** You now have a professional visual cooking tutorial that will help you master authentic [cuisine] cooking techniques!
        
        Use celebratory tone, rich formatting, and inspire continued cooking exploration.
        """
        
        # Generate tutorial presentation
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=tutorial_presentation_prompt,
            temperature=settings.creative_temperature,
            agent_name="conversation_agent"
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        presentation_data = json.loads(response.get("content", "{}"))
        processing_time = int((time.time() - start_time) * 1000)
        
        # Extract tutorial information
        recipe_name = tutorial_info.get("recipe_name", "Your Recipe")
        images_generated = tutorial_data.get("images_generated", 0)
        
        logger.info(f"✅ Tutorial presentation created in {processing_time}ms")
        logger.info(f"🎥 Tutorial for: {recipe_name}")
        logger.info(f"🎨 Images showcased: {images_generated}")
        
        # Create conversation response
        response_obj = ConversationResponse(
            status="success",
            message=f"Tutorial presentation created for {recipe_name}",
            agent_name="conversation_agent",
            processing_time_ms=processing_time,
            confidence_score=0.95,
            presentation_content=presentation_data.get("celebration_markdown", ""),
            suggested_next_steps=[
                "Cook the recipe using your visual tutorial",
                "Create recipe variations and adaptations",
                "Explore tutorials for different cuisines",
                "Share your tutorial with friends and family"
            ],
            conversation_stage="tutorial_completed"
        )
        
        # Add tutorial analysis
        response_dict = response_obj.dict()
        response_dict["tutorial_analysis"] = {
            "achievement_highlights": presentation_data.get("achievement_highlights", []),
            "tutorial_value": presentation_data.get("tutorial_value", []),
            "usage_guidance": presentation_data.get("usage_guidance", []),
            "learning_outcomes": presentation_data.get("learning_outcomes", [])
        }
        
        return json.dumps(response_dict, ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Tutorial presentation creation failed: {e}")
        
        # Create fallback celebration
        fallback_response = ConversationResponse(
            status="warning",
            message=f"Tutorial presentation partially created: {str(e)}",
            agent_name="conversation_agent",
            processing_time_ms=processing_time,
            presentation_content="# 🎥 Your Visual Tutorial is Ready!\n\n🎉 **Congratulations!** Your cooking tutorial has been successfully created with professional images to guide your cooking journey.",
            suggested_next_steps=["Use tutorial to cook the recipe", "Explore recipe variations"],
            conversation_stage="tutorial_completed"
        )
        
        return fallback_response.model_dump_json(indent=2)


async def manage_conversation_flow(
    user_message: str,
    conversation_history: List[Dict[str, Any]] = None,
    current_stage: str = "initial"
) -> str:
    """
    Manage conversation flow and determine appropriate next actions and responses.
    
    Args:
        user_message: Current user message or request
        conversation_history: Previous conversation context
        current_stage: Current conversation stage
        
    Returns:
        JSON string containing conversation management recommendations
    """
    start_time = time.time()
    logger.info(f"💬 Managing conversation flow for stage: {current_stage}")
    
    try:
        # Prepare conversation context
        history_summary = ""
        if conversation_history:
            history_summary = f"Previous interactions: {len(conversation_history)} messages"
            
        # Create conversation management prompt
        flow_prompt = f"""
        Analyze conversation flow and provide intelligent conversation management:
        
        Current User Message: "{user_message}"
        Current Conversation Stage: {current_stage}
        Conversation History: {history_summary}
        
        As a conversation flow specialist, analyze and recommend:
        
        1. **User Intent Analysis**:
           - Determine what the user wants to accomplish
           - Assess satisfaction with current results
           - Identify any concerns or clarification needs
           - Evaluate engagement level and enthusiasm
        
        2. **Conversation Stage Assessment**:
           - Validate current conversation stage accuracy
           - Determine if stage progression is appropriate
           - Identify any workflow bottlenecks or issues
           - Assess completion readiness for current stage
        
        3. **Next Action Recommendations**:
           - Suggest immediate next steps for optimal user experience
           - Prioritize actions based on user value and satisfaction
           - Consider user time and effort investment
           - Balance immediate needs with future opportunities
        
        4. **Engagement Optimization**:
           - Recommend engagement strategies for current context
           - Suggest motivational elements and achievement highlights
           - Identify opportunities for learning and skill building
           - Propose value-added suggestions and enhancements
        
        Return conversation management analysis:
        {{
            "user_intent_analysis": {{
                "primary_intent": "what_user_wants_to_accomplish",
                "satisfaction_level": "high|medium|low|unclear",
                "engagement_indicators": ["signs_of_user_engagement"],
                "concerns_or_issues": ["any_user_concerns_detected"],
                "motivation_level": "enthusiastic|interested|neutral|reluctant"
            }},
            "conversation_assessment": {{
                "current_stage_accuracy": "accurate|needs_adjustment",
                "progression_recommendation": "continue|advance|revisit|restart",
                "workflow_status": "on_track|delayed|blocked|completed",
                "user_journey_position": "beginning|middle|advanced|completion"
            }},
            "next_action_priorities": {{
                "immediate_actions": ["highest_priority_next_steps"],
                "recommended_sequence": ["logical_action_progression"],
                "optional_enhancements": ["value_added_opportunities"],
                "time_sensitive_items": ["actions_requiring_immediate_attention"]
            }},
            "engagement_strategy": {{
                "motivational_elements": ["ways_to_maintain_enthusiasm"],
                "achievement_highlights": ["successes_to_celebrate"],
                "learning_opportunities": ["skill_building_suggestions"],
                "value_propositions": ["benefits_to_emphasize"]
            }},
            "conversation_recommendations": {{
                "tone_adjustment": "maintain|increase_enthusiasm|provide_reassurance|celebrate_achievement",
                "information_priority": "practical_guidance|cost_benefits|cultural_education|technical_skills",
                "interaction_style": "professional|casual|encouraging|educational",
                "follow_up_timing": "immediate|short_term|long_term"
            }}
        }}
        
        Provide actionable recommendations that enhance user experience and conversation flow.
        """
        
        # Use AI for conversation analysis
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=flow_prompt,
            temperature=settings.balanced_temperature,
            agent_name="conversation_agent"
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        flow_data = json.loads(response.get("content", "{}"))
        processing_time = int((time.time() - start_time) * 1000)
        
        # Extract key insights
        user_satisfaction = flow_data.get("user_intent_analysis", {}).get("satisfaction_level", "unclear")
        next_actions = flow_data.get("next_action_priorities", {}).get("immediate_actions", [])
        
        logger.info(f"✅ Conversation flow analysis completed in {processing_time}ms")
        logger.info(f"😊 User satisfaction: {user_satisfaction}")
        logger.info(f"🎯 Next actions identified: {len(next_actions)}")
        
        # Create flow management response
        response_obj = {
            "status": "success",
            "message": "Conversation flow analysis completed",
            "agent_name": "conversation_agent",
            "processing_time_ms": processing_time,
            "user_message": user_message,
            "current_stage": current_stage,
            "flow_analysis": flow_data,
            "recommended_actions": next_actions,
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(response_obj, ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Conversation flow management failed: {e}")
        
        # Create fallback flow recommendations
        fallback_response = {
            "status": "warning",
            "message": f"Conversation flow analysis partially failed: {str(e)}",
            "agent_name": "conversation_agent",
            "processing_time_ms": processing_time,
            "fallback_recommendations": {
                "immediate_actions": ["Continue with recipe creation", "Offer tutorial creation"],
                "engagement_strategy": "Maintain positive momentum",
                "user_satisfaction": "unclear"
            }
        }
        
        return json.dumps(fallback_response, ensure_ascii=False, indent=2)


async def generate_next_step_recommendations(
    completed_workflows: List[str],
    user_preferences: Dict[str, Any] = None,
    conversation_context: str = ""
) -> str:
    """
    Generate intelligent next step recommendations based on completed workflows and user preferences.
    
    Args:
        completed_workflows: List of completed workflow stages
        user_preferences: User preferences and interests
        conversation_context: Current conversation context
        
    Returns:
        JSON string containing personalized next step recommendations
    """
    start_time = time.time()
    logger.info(f"🎯 Generating next step recommendations for {len(completed_workflows)} completed workflows")
    
    try:
        # Prepare context information
        user_prefs = user_preferences or {}
        workflow_summary = ", ".join(completed_workflows) if completed_workflows else "none"
        
        # Create next steps recommendation prompt
        recommendations_prompt = f"""
        Generate personalized next step recommendations based on user journey and preferences:
        
        Completed Workflows: {workflow_summary}
        User Preferences: {json.dumps(user_prefs, indent=2)}
        Conversation Context: "{conversation_context}"
        
        As a personalization specialist, recommend next steps that:
        
        1. **Build on Achievements**: Leverage completed workflows for progression
        2. **Match Interests**: Align with user preferences and cooking goals
        3. **Add Value**: Provide meaningful enhancement to user experience
        4. **Encourage Growth**: Support cooking skill and cultural knowledge development
        5. **Maintain Engagement**: Keep user excited about cooking exploration
        
        Consider these recommendation categories:
        
        ### Immediate Next Steps (within next session)
        - Direct continuations of current workflow
        - Quick wins and immediate value additions
        - Skill practice and technique reinforcement
        
        ### Short-term Exploration (within next week)
        - Related recipe exploration and variations
        - Cultural cuisine deep dives
        - Skill building progressions
        
        ### Long-term Development (ongoing learning)
        - Advanced cooking technique mastery
        - Cultural cooking tradition exploration
        - Seasonal cooking and ingredient mastery
        
        Return personalized recommendations:
        {{
            "immediate_recommendations": [
                {{
                    "action": "specific_action_recommendation",
                    "description": "what_this_accomplishes",
                    "value_proposition": "why_this_benefits_user",
                    "effort_level": "low|medium|high",
                    "time_required": "estimated_time_minutes",
                    "skills_developed": ["cooking_skills_gained"]
                }}
            ],
            "short_term_opportunities": [
                {{
                    "category": "recipe_exploration|skill_building|cultural_learning",
                    "suggestion": "specific_suggestion",
                    "learning_outcome": "what_user_will_gain",
                    "difficulty_progression": "beginner|intermediate|advanced"
                }}
            ],
            "long_term_development": [
                {{
                    "mastery_path": "cooking_mastery_journey",
                    "milestones": ["achievement_milestones"],
                    "cultural_exploration": "cultural_cooking_traditions_to_explore",
                    "advanced_techniques": ["professional_techniques_to_master"]
                }}
            ],
            "personalization_factors": {{
                "preference_alignment": "how_recommendations_match_user_preferences",
                "skill_level_appropriateness": "recommendations_match_current_skill_level",
                "cultural_interests": "cultural_elements_considered",
                "practical_considerations": "real_world_applicability"
            }}
        }}
        
        Focus on actionable, specific recommendations that inspire continued cooking exploration.
        """
        
        # Generate recommendations using AI
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=recommendations_prompt,
            temperature=settings.creative_temperature,
            agent_name="conversation_agent"
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        recommendations_data = json.loads(response.get("content", "{}"))
        processing_time = int((time.time() - start_time) * 1000)
        
        # Extract recommendation counts
        immediate_count = len(recommendations_data.get("immediate_recommendations", []))
        short_term_count = len(recommendations_data.get("short_term_opportunities", []))
        
        logger.info(f"✅ Next step recommendations generated in {processing_time}ms")
        logger.info(f"🎯 Immediate recommendations: {immediate_count}")
        logger.info(f"📅 Short-term opportunities: {short_term_count}")
        
        # Create recommendations response
        response_obj = {
            "status": "success",
            "message": f"Generated {immediate_count + short_term_count} personalized recommendations",
            "agent_name": "conversation_agent",
            "processing_time_ms": processing_time,
            "completed_workflows": completed_workflows,
            "recommendations_data": recommendations_data,
            "personalization_applied": bool(user_preferences),
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(response_obj, ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Next step recommendations generation failed: {e}")
        
        # Create fallback recommendations
        fallback_recommendations = {
            "immediate_recommendations": [
                {
                    "action": "Create visual cooking tutorial",
                    "description": "Generate step-by-step cooking images",
                    "value_proposition": "Learn through visual guidance",
                    "effort_level": "low",
                    "time_required": "5 minutes",
                    "skills_developed": ["visual_learning", "technique_mastery"]
                },
                {
                    "action": "Explore recipe variations",
                    "description": "Discover adaptations and alternatives",
                    "value_proposition": "Expand cooking repertoire",
                    "effort_level": "medium",
                    "time_required": "10 minutes",
                    "skills_developed": ["creativity", "adaptation"]
                }
            ]
        }
        
        fallback_response = {
            "status": "warning",
            "message": f"Recommendations generation partially failed: {str(e)}",
            "agent_name": "conversation_agent",
            "processing_time_ms": processing_time,
            "fallback_recommendations": fallback_recommendations
        }
        
        return json.dumps(fallback_response, ensure_ascii=False, indent=2)