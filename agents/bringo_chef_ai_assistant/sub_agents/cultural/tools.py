# agents/bringo_chef_ai_assistant/sub_agents/cultural/tools.py
# Cultural analysis tools with async AI integration and professional prompt engineering
# Pure AI-driven cultural context extraction without hardcoded assumptions

import asyncio
import logging
import time
from datetime import datetime

from ....shared.client import get_ai_client, call_ai_with_validation
from ....shared.models import CulturalAnalysis, CulturalAnalysisResponse
from ....shared.responses import create_success_response, create_error_response
from ....shared.config import settings

logger = logging.getLogger("cultural_tools")


async def detect_language_and_culture(user_request: str) -> str:
    """
    Detect language, location, and basic cultural context from culinary request using AI.
    
    Args:
        user_request: User's culinary request in any language
        
    Returns:
        JSON string containing cultural analysis response
    """
    start_time = time.time()
    logger.info(f"🌍 Analyzing cultural context for request: {user_request[:50]}...")
    
    if not user_request or len(user_request.strip()) < 2:
        return create_error_response(
            agent_name="cultural_context_agent",
            error_message="User request is too short for meaningful cultural analysis"
        ).json(ensure_ascii=False)
    
    # Professional AI prompt for language and cultural detection
    prompt = f"""
    Analyze this culinary request for comprehensive cultural context: "{user_request}"
    
    As a professional cultural analysis specialist, perform detailed analysis covering:
    
    1. **Language Detection**:
       - Identify primary language with confidence score (0.0-1.0)
       - Detect any regional dialect or variation
       - Assess linguistic cultural markers
    
    2. **Geographic Analysis**: 
       - Determine likely location/country based on language and cultural cues
       - Identify regional cooking preferences if apparent
       - Assess confidence in geographic assessment
    
    3. **Cultural Cooking Indicators**:
       - Cuisine style preference (traditional, modern, fusion, international)
       - Meal context (casual, formal, celebration, comfort, romantic, family)
       - Cooking approach (quick, elaborate, rustic, refined)
       - Budget consciousness level (high, medium, low)
       - Time approach (immediate, flexible, leisurely) 
       - Social dining context (individual, family, entertaining, intimate)
    
    4. **Traditional Dish Recognition**:
       - Identify any specific traditional dishes mentioned or implied
       - Assess cultural significance and authenticity requirements
       - Provide confidence scores for dish identification
    
    Return precise JSON analysis:
    {{
        "language": {{
            "code": "two-letter language code (ro, en, de, hu, etc.)",
            "name": "full language name",
            "confidence": confidence_score_0_to_1,
            "dialect": "regional dialect or null"
        }},
        "location": {{
            "country": "most likely country",
            "region": "specific region if detectable or null", 
            "confidence": confidence_score_0_to_1
        }},
        "cultural_indicators": {{
            "cuisine_style": "traditional|modern|fusion|international",
            "meal_context": "casual|formal|celebration|comfort|romantic|family",
            "cooking_approach": "quick|elaborate|rustic|refined", 
            "budget_consciousness": "high|medium|low",
            "time_approach": "immediate|flexible|leisurely",
            "social_dining": "individual|family|entertaining|intimate"
        }},
        "traditional_dishes": [
            {{
                "name": "dish name if identified",
                "origin": "cultural origin",
                "confidence": confidence_score,
                "cultural_significance": "brief explanation"
            }}
        ],
        "confidence_score": overall_analysis_confidence_0_to_1
    }}
    
    Focus on culinary-relevant cultural aspects. Be conservative with confidence scores.
    Provide professional analysis based on linguistic and cultural evidence in the request.
    """
    
    try:
        # Use AI client with validation
        result = await call_ai_with_validation(
            prompt=prompt,
            expected_model=CulturalAnalysis,
            agent_name="cultural_context_agent",
            temperature=settings.conservative_temperature
        )
        
        if not result["success"]:
            raise Exception(result["error"])
        
        processing_time = int((time.time() - start_time) * 1000)
        cultural_data = result["data"]
        
        logger.info(f"✅ Cultural analysis completed in {processing_time}ms")
        logger.info(f"🎯 Detected: {cultural_data.language.name} ({cultural_data.language.confidence:.2f} confidence)")
        
        # Create successful response
        response = CulturalAnalysisResponse(
            status="success",
            message="Cultural context analysis completed successfully",
            agent_name="cultural_context_agent",
            processing_time_ms=processing_time,
            confidence_score=cultural_data.confidence_score,
            data=cultural_data,
            user_request=user_request,
            detected_language=cultural_data.language.code
        )
        
        return response.json(ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Cultural analysis failed: {e}")
        
        # Create fallback response with conservative defaults
        fallback_response = CulturalAnalysisResponse(
            status="warning",
            message=f"Cultural analysis partially failed: {str(e)}. Using conservative defaults.",
            agent_name="cultural_context_agent", 
            processing_time_ms=processing_time,
            confidence_score=0.5,
            user_request=user_request,
            detected_language="ro",  # Conservative default for Romanian market
            data=None
        )
        
        return fallback_response.json(ensure_ascii=False, indent=2)


async def analyze_cultural_context(user_request: str, basic_analysis_json: str = "") -> str:
    """
    Perform deeper cultural context analysis building on basic language detection.
    
    Args:
        user_request: Original user request
        basic_analysis_json: Optional basic cultural analysis to enhance
        
    Returns:
        JSON string containing enhanced cultural analysis
    """
    start_time = time.time()
    logger.info(f"🎭 Performing deep cultural analysis for: {user_request[:50]}...")
    
    # Parse basic analysis if provided
    basic_context = ""
    if basic_analysis_json:
        try:
            import json
            basic_data = json.loads(basic_analysis_json)
            if basic_data.get("status") == "success" and basic_data.get("data"):
                cultural_data = basic_data["data"]
                basic_context = f"""
                Previous Analysis Context:
                - Language: {cultural_data.get('language', {}).get('name', 'Unknown')}
                - Location: {cultural_data.get('location', {}).get('country', 'Unknown')}
                - Initial Cultural Indicators: {cultural_data.get('cultural_indicators', {})}
                """
        except Exception as e:
            logger.warning(f"⚠️ Could not parse basic analysis: {e}")
    
    # Enhanced cultural analysis prompt
    prompt = f"""
    Perform comprehensive cultural cooking context analysis for: "{user_request}"
    
    {basic_context}
    
    As a culinary cultural specialist, provide detailed analysis covering:
    
    1. **Advanced Cultural Patterns**:
       - Identify specific cooking traditions and preferences
       - Assess seasonal cooking awareness and ingredient preferences
       - Determine traditional vs. modern cooking preferences
       - Evaluate health and dietary consciousness levels
    
    2. **Culinary Cultural Mapping**:
       - Map to specific cultural cooking styles and techniques
       - Identify preferred protein, carbohydrate, and flavor profiles
       - Assess spice tolerance and flavor complexity preferences
       - Determine typical meal structure and portion expectations
    
    3. **Social and Economic Context**:
       - Assess cooking skill level implications
       - Determine kitchen equipment and cooking method preferences  
       - Evaluate ingredient accessibility and market preferences
       - Identify value-consciousness and quality expectations
    
    4. **Traditional Recipe Recognition**:
       - Identify specific traditional recipes or cooking methods referenced
       - Assess cultural authenticity requirements vs. adaptation flexibility
       - Determine seasonal and regional ingredient preferences
       - Provide cultural context for ingredient substitutions
    
    Return enhanced cultural analysis JSON:
    {{
        "language": {{
            "code": "language_code",
            "name": "language_name", 
            "confidence": confidence_score,
            "dialect": "dialect_or_null"
        }},
        "location": {{
            "country": "country_name",
            "region": "region_or_null",
            "confidence": confidence_score
        }},
        "cultural_indicators": {{
            "cuisine_style": "traditional|modern|fusion|international",
            "meal_context": "casual|formal|celebration|comfort|romantic|family",
            "cooking_approach": "quick|elaborate|rustic|refined",
            "budget_consciousness": "high|medium|low",
            "time_approach": "immediate|flexible|leisurely", 
            "social_dining": "individual|family|entertaining|intimate"
        }},
        "traditional_dishes": [
            {{
                "name": "traditional_dish_name",
                "origin": "cultural_origin",
                "confidence": confidence_score,
                "cultural_significance": "cultural_importance_explanation"
            }}
        ],
        "confidence_score": overall_confidence_0_to_1
    }}
    
    Provide professional, evidence-based cultural analysis relevant to recipe creation.
    Focus on actionable insights that will inform ingredient selection and cooking methods.
    """
    
    try:
        # Use AI for enhanced analysis
        result = await call_ai_with_validation(
            prompt=prompt,
            expected_model=CulturalAnalysis,
            agent_name="cultural_context_agent", 
            temperature=settings.balanced_temperature
        )
        
        if not result["success"]:
            raise Exception(result["error"])
        
        processing_time = int((time.time() - start_time) * 1000)
        enhanced_data = result["data"]
        
        logger.info(f"✅ Enhanced cultural analysis completed in {processing_time}ms")
        logger.info(f"🎯 Cultural style: {enhanced_data.cultural_indicators.cuisine_style}")
        logger.info(f"🍽️ Meal context: {enhanced_data.cultural_indicators.meal_context}")
        
        # Create comprehensive response
        response = CulturalAnalysisResponse(
            status="success",
            message="Enhanced cultural context analysis completed",
            agent_name="cultural_context_agent",
            processing_time_ms=processing_time,
            confidence_score=enhanced_data.confidence_score,
            data=enhanced_data,
            user_request=user_request,
            detected_language=enhanced_data.language.code
        )
        
        return response.json(ensure_ascii=False, indent=2)
        
    except Exception as e:
        processing_time = int((time.time() - start_time) * 1000)
        logger.error(f"❌ Enhanced cultural analysis failed: {e}")
        
        # Return the basic analysis if enhancement fails
        if basic_analysis_json:
            logger.info("📋 Returning basic analysis due to enhancement failure")
            return basic_analysis_json
        
        # Create error response
        error_response = CulturalAnalysisResponse(
            status="error",
            message=f"Cultural analysis failed: {str(e)}",
            agent_name="cultural_context_agent",
            processing_time_ms=processing_time,
            user_request=user_request
        )
        
        return error_response.json(ensure_ascii=False, indent=2)