# agents/bringo_chef_ai_assistant/shared/responses.py
# Standardized response utilities for consistent inter-agent communication
# Professional error handling and response formatting across all agents

import logging
from datetime import datetime
from typing import Optional, Any, Dict

from .models import StandardResponse, StatusType

logger = logging.getLogger("bringo_responses")


def create_success_response(
    agent_name: str,
    data: Any = None,
    message: str = None,
    confidence_score: float = None,
    processing_time_ms: int = None
) -> StandardResponse:
    """
    Create a standardized success response
    
    Args:
        agent_name: Name of the responding agent
        data: Response data payload
        message: Optional success message
        confidence_score: Agent confidence in the result
        processing_time_ms: Processing time in milliseconds
        
    Returns:
        Standardized success response
    """
    return StandardResponse(
        status=StatusType.SUCCESS,
        message=message or "Operation completed successfully",
        agent_name=agent_name,
        confidence_score=confidence_score,
        processing_time_ms=processing_time_ms
    )


def create_error_response(
    agent_name: str,
    error_message: str,
    error_details: Optional[Dict[str, Any]] = None,
    processing_time_ms: int = None
) -> StandardResponse:
    """
    Create a standardized error response
    
    Args:
        agent_name: Name of the responding agent
        error_message: Clear error description
        error_details: Additional error context
        processing_time_ms: Processing time before error
        
    Returns:
        Standardized error response
    """
    logger.error(f"❌ {agent_name} error: {error_message}")
    
    full_message = error_message
    if error_details:
        full_message += f" | Details: {error_details}"
    
    return StandardResponse(
        status=StatusType.ERROR,
        message=full_message,
        agent_name=agent_name,
        processing_time_ms=processing_time_ms
    )