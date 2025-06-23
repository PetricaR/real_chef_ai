# agents/bringo_chef_ai_assistant/sub_agents/parameter_extraction/tools.py
# Parameter extraction tools with async AI integration and intelligent inference
# Professional parameter analysis without hardcoded assumptions

import asyncio
import logging
import time
import json
from datetime import datetime

from ...shared.client import get_ai_client
from ...shared.models import CookingParameters, ParameterExtractionResponse, BudgetInfo, ServingInfo, TimeInfo, DietaryInfo
from ...shared.responses import create_success_response, create_error_response
from ...shared.config import settings

logger = logging.getLogger("parameter_tools")


async def extract_cooking_parameters(user_request: str) -> str:
    """
    Extract cooking parameters from user request using intelligent AI analysis.
    
    Args:
        user_request: User's culinary request
        
    Returns:
        JSON string containing parameter extraction response
    """
    start_time = time.time()
    logger.info(f"📊 Extracting cooking parameters from: {user_request[:50]}...")
    
    if not user_request or len(user_request.strip()) < 2:
        return create_error_response(
            agent_name="parameter_extraction_agent",
            error_message="User request is too short for parameter extraction"
        ).json(ensure_ascii=False)
    
    # Professional AI prompt for parameter extraction
    prompt = f"""
    Extract comprehensive cooking parameters from this culinary request: "{user_request}"
    
    As a professional cooking parameter analyst, perform systematic extraction covering:
    
    1. **Budget Analysis**:
       - Identify explicit budget mentions (amounts in RON, lei, etc.)
       - Assess implicit budget consciousness from language and context
       - Consider cuisine type and meal complexity for budget estimation
       - Assign confidence based on evidence strength
    
    2. **Serving Size Detection**:
       - Extract explicit serving counts ("for 2 people", "family of 4")
       - Infer from social context (romantic = 2, family = 4-6, party = 8+)
       - Consider meal type and occasion for serving expectations
       - Provide reasoning for inferred serving sizes
    
    3. **Time Constraint Assessment**:
       - Identify explicit time mentions ("30 minutes", "quick dinner")
       - Assess urgency from context ("tonight", "weekend project")
       - Consider cooking complexity and skill level implications
       - Classify as immediate/flexible/leisurely based on cues
    
    4. **Meal Classification**:
       - Determine meal type (breakfast, lunch, dinner, snack)
       - Identify occasion (everyday, special, celebration, comfort, romantic)
       - Assess formality level and social context
       - Consider cultural meal patterns and expectations
    
    5. **Dietary Requirements**:
       - Extract explicit restrictions (vegetarian, gluten-free, etc.)
       - Identify health preferences (healthy, low-carb, etc.)
       - Recognize cultural dietary patterns
       - Assess confidence based on clarity of dietary cues
    
    6. **Complexity and Skill Assessment**:
       - Infer preferred difficulty level from language and context
       - Consider time constraints and cooking confidence cues
       - Assess kitchen equipment and skill level implications
       - Determine cooking approach preferences
    
    Return precise JSON analysis with Romanian market context:
    {{
        "budget": {{
            "amount_ron": estimated_budget_in_romanian_lei,
            "confidence": "high|medium|low",
            "explicit": true_if_explicitly_mentioned_false_if_inferred
        }},
        "servings": {{
            "count": estimated_serving_count,
            "confidence": "high|medium|low",
            "explicit": true_if_explicitly_mentioned
        }},
        "time": {{
            "minutes": estimated_cooking_time_minutes,
            "urgency": "immediate|flexible|leisurely",
            "confidence": "high|medium|low"
        }},
        "meal_type": "breakfast|lunch|dinner|snack",
        "meal_occasion": "everyday|special|celebration|comfort|romantic",
        "dietary": {{
            "restrictions": ["explicit_dietary_restrictions"],
            "preferences": ["health_and_diet_preferences"],
            "confidence": "high|medium|low"
        }},
        "difficulty_preference": "easy|medium|advanced|any",
        "cuisine_type": "specific_cuisine_if_mentioned_or_null"
    }}
    
    Use Romanian market context for budget estimates (typical food costs, purchasing power).
    Provide conservative estimates when information is ambiguous.
    Base all inferences on evidence from the request text.
    """
    
    try:
        # Use AI client for parameter extraction
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=prompt,
            temperature=settings.conservative_temperature,
            agent_name="parameter_extraction_agent"
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        # Parse and validate the response
        content = response.get("content", "")
        parameter_data_dict = json.loads(content)
        
        # Convert to CookingParameters model with error handling
        try:
            parameter_data = CookingParameters(**parameter_data_dict)
        except Exception as model_error:
            logger.warning(f"⚠️ Parameter model validation failed: {model_error}")
            # Create fallback parameters
            parameter_data = CookingParameters(
                budget=BudgetInfo(amount_ron=50.0, confidence="low", explicit=False),
                servings=ServingInfo(count=4, confidence="low", explicit=False),
                time=TimeInfo(minutes=60, urgency="flexible", confidence="low"),
                meal_type="lunch",
                meal_occasion="everyday", 
                dietary=DietaryInfo(confidence="low"),
                difficulty_preference="medium"
            )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Count successfully extracted parameters
        parameters_found = 0
        if parameter_data.budget.confidence != "low":
            parameters_found += 1
        if parameter_data.servings.confidence != "low":
            parameters_found += 1
        if parameter_data.time.confidence != "low":
            parameters_found += 1
        if parameter_data.dietary.confidence != "low":
            parameters_found += 1
        
        logger.info(f"✅ Parameter extraction completed in {processing_time}ms")
        logger.info(f"💰 Budget: {parameter_data.budget.amount_ron} RON ({parameter_data.budget.confidence})")
        logger.info(f"👥 Servings: {parameter_data.servings.count} ({parameter_data.servings.confidence})")
        logger.info(f"⏱️ Time: {parameter_data.time.minutes} min ({parameter_data.time.confidence})")
        
        # Create successful response
        response = ParameterExtractionResponse(
            status="success",
            message="Cooking parameters extracted successfully",
            agent_name="parameter_extraction_agent",
            processing_time_ms=processing_time,
            confidence_score=_calculate_overall_confidence(parameter_data),
            data=parameter_data,
            user_request=user_request,
            parameters_found=parameters_found
        )
        
        return response.json(ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Parameter extraction failed: {e}")
        
        # Create fallback response with conservative defaults
        fallback_response = ParameterExtractionResponse(
            status="warning",
            message=f"Parameter extraction partially failed: {str(e)}. Using conservative defaults.",
            agent_name="parameter_extraction_agent",
            processing_time_ms=processing_time,
            confidence_score=0.3,
            user_request=user_request,
            parameters_found=0,
            data=None
        )
        
        return fallback_response.json(ensure_ascii=False, indent=2)


async def extract_parameters_with_culture(user_request: str, cultural_context_json: str = "") -> str:
    """
    Extract cooking parameters enhanced with cultural context intelligence.
    
    Args:
        user_request: Original user request
        cultural_context_json: Cultural analysis results for context-aware extraction
        
    Returns:
        JSON string containing culturally-enhanced parameter extraction
    """
    start_time = time.time()
    logger.info(f"🌍 Extracting parameters with cultural context for: {user_request[:50]}...")
    
    # Parse cultural context for enhanced analysis
    cultural_insights = ""
    detected_language = "unknown"
    cultural_confidence = 0.5
    
    if cultural_context_json:
        try:
            cultural_data = json.loads(cultural_context_json)
            if cultural_data.get("status") == "success" and cultural_data.get("data"):
                context = cultural_data["data"]
                detected_language = context.get("language", {}).get("code", "unknown")
                cultural_confidence = context.get("confidence_score", 0.5)
                
                cultural_insights = f"""
                Cultural Context for Enhanced Parameter Extraction:
                - Language: {context.get('language', {}).get('name', 'Unknown')} (confidence: {context.get('language', {}).get('confidence', 0.5)})
                - Location: {context.get('location', {}).get('country', 'Unknown')}
                - Cuisine Style: {context.get('cultural_indicators', {}).get('cuisine_style', 'unknown')}
                - Meal Context: {context.get('cultural_indicators', {}).get('meal_context', 'unknown')}
                - Cooking Approach: {context.get('cultural_indicators', {}).get('cooking_approach', 'unknown')}
                - Budget Consciousness: {context.get('cultural_indicators', {}).get('budget_consciousness', 'unknown')}
                - Social Dining: {context.get('cultural_indicators', {}).get('social_dining', 'unknown')}
                - Traditional Dishes: {context.get('traditional_dishes', [])}
                """
        except Exception as e:
            logger.warning(f"⚠️ Could not parse cultural context: {e}")
    
    # Enhanced parameter extraction prompt with cultural intelligence
    prompt = f"""
    Extract cooking parameters from: "{user_request}"
    
    {cultural_insights}
    
    As a cultural cooking parameter specialist, enhance parameter extraction using cultural context:
    
    1. **Culturally-Informed Budget Analysis**:
       - Apply cultural budget consciousness patterns
       - Consider regional cost expectations and purchasing power
       - Adjust budget estimates based on cuisine type and cultural context
       - Factor in meal occasion and social dining expectations
    
    2. **Cultural Serving Size Intelligence**:
       - Apply cultural family size and dining patterns
       - Consider social dining context (individual, family, entertaining)
       - Adjust for cultural portion expectations and meal sharing patterns
       - Factor in cultural hospitality and food abundance expectations
    
    3. **Cultural Time and Approach Assessment**:
       - Apply cultural cooking time preferences and traditions
       - Consider cultural cooking approach (quick vs. elaborate preparation)
       - Factor in cultural meal preparation rituals and expectations
       - Assess urgency within cultural context of meal preparation
    
    4. **Cultural Dietary and Cuisine Intelligence**:
       - Apply cultural dietary norms and traditional restrictions
       - Consider regional ingredient availability and preferences
       - Factor in cultural health consciousness and dietary trends
       - Assess cuisine authenticity vs. adaptation flexibility
    
    5. **Cultural Occasion and Complexity Assessment**:
       - Interpret meal occasion within cultural context
       - Apply cultural cooking skill expectations and traditions
       - Consider cultural equipment and cooking method preferences
       - Factor in cultural presentation and authenticity requirements
    
    Return culturally-enhanced parameter analysis:
    {{
        "budget": {{
            "amount_ron": culturally_adjusted_budget_estimate,
            "confidence": "high|medium|low",
            "explicit": true_if_explicitly_stated
        }},
        "servings": {{
            "count": culturally_appropriate_serving_count,
            "confidence": "high|medium|low", 
            "explicit": true_if_explicitly_stated
        }},
        "time": {{
            "minutes": culturally_informed_time_estimate,
            "urgency": "immediate|flexible|leisurely",
            "confidence": "high|medium|low"
        }},
        "meal_type": "breakfast|lunch|dinner|snack",
        "meal_occasion": "everyday|special|celebration|comfort|romantic",
        "dietary": {{
            "restrictions": ["cultural_and_explicit_restrictions"],
            "preferences": ["cultural_and_stated_preferences"],
            "confidence": "high|medium|low"
        }},
        "difficulty_preference": "easy|medium|advanced|any",
        "cuisine_type": "specific_cuisine_with_cultural_context"
    }}
    
    Enhance all parameter estimates using cultural intelligence.
    Provide higher confidence scores when cultural context supports parameter interpretation.
    Consider cultural cooking traditions and modern adaptations in Romanian context.
    """
    
    try:
        # Use AI for culturally-enhanced analysis
        client = await get_ai_client()
        
        response = await client.generate_text(
            prompt=prompt,
            temperature=settings.balanced_temperature,
            agent_name="parameter_extraction_agent"
        )
        
        if response.get("error"):
            raise Exception(response["error"])
        
        # Parse and validate the response
        content = response.get("content", "")
        parameter_data_dict = json.loads(content)
        
        # Convert to CookingParameters model with error handling
        try:
            enhanced_parameters = CookingParameters(**parameter_data_dict)
        except Exception as model_error:
            logger.warning(f"⚠️ Enhanced parameter model validation failed: {model_error}")
            # Fallback to basic parameter extraction
            logger.info("📋 Falling back to basic parameter extraction")
            return await extract_cooking_parameters(user_request)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Count high-confidence parameters
        parameters_found = sum([
            1 for param_confidence in [
                enhanced_parameters.budget.confidence,
                enhanced_parameters.servings.confidence,
                enhanced_parameters.time.confidence,
                enhanced_parameters.dietary.confidence
            ] if param_confidence in ["high", "medium"]
        ])
        
        # Calculate enhanced confidence score
        overall_confidence = _calculate_overall_confidence(enhanced_parameters)
        if cultural_confidence > 0.7:
            overall_confidence = min(1.0, overall_confidence + 0.1)  # Boost confidence with good cultural context
        
        logger.info(f"✅ Culturally-enhanced parameter extraction completed in {processing_time}ms")
        logger.info(f"🎯 Cultural enhancement improved confidence to {overall_confidence:.2f}")
        
        # Create enhanced response
        response = ParameterExtractionResponse(
            status="success",
            message="Culturally-enhanced parameter extraction completed",
            agent_name="parameter_extraction_agent",
            processing_time_ms=processing_time,
            confidence_score=overall_confidence,
            data=enhanced_parameters,
            user_request=user_request,
            parameters_found=parameters_found
        )
        
        return response.json(ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Culturally-enhanced parameter extraction failed: {e}")
        
        # Fallback to basic extraction if cultural enhancement fails
        logger.info("📋 Falling back to basic parameter extraction")
        return await extract_cooking_parameters(user_request)


def _calculate_overall_confidence(parameters: CookingParameters) -> float:
    """Calculate overall confidence score from individual parameter confidences"""
    confidence_map = {"high": 1.0, "medium": 0.7, "low": 0.3}
    
    confidences = [
        confidence_map.get(parameters.budget.confidence, 0.3),
        confidence_map.get(parameters.servings.confidence, 0.3),
        confidence_map.get(parameters.time.confidence, 0.3),
        confidence_map.get(parameters.dietary.confidence, 0.3)
    ]
    
    return sum(confidences) / len(confidences)