# agents/shared/responses.py
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


def create_warning_response(
    agent_name: str,
    warning_message: str,
    data: Any = None,
    confidence_score: float = None,
    processing_time_ms: int = None
) -> StandardResponse:
    """
    Create a standardized warning response (partial success)
    
    Args:
        agent_name: Name of the responding agent
        warning_message: Warning description
        data: Partial response data
        confidence_score: Agent confidence in partial result
        processing_time_ms: Processing time
        
    Returns:
        Standardized warning response
    """
    logger.warning(f"⚠️ {agent_name} warning: {warning_message}")
    
    return StandardResponse(
        status=StatusType.WARNING,
        message=warning_message,
        agent_name=agent_name,
        confidence_score=confidence_score,
        processing_time_ms=processing_time_ms
    )


def create_processing_response(
    agent_name: str,
    processing_message: str = "Processing request..."
) -> StandardResponse:
    """
    Create a processing status response
    
    Args:
        agent_name: Name of the processing agent
        processing_message: Processing status message
        
    Returns:
        Standardized processing response
    """
    return StandardResponse(
        status=StatusType.PROCESSING,
        message=processing_message,
        agent_name=agent_name
    )


def format_agent_response(
    response: StandardResponse,
    include_metadata: bool = True
) -> str:
    """
    Format an agent response for JSON output
    
    Args:
        response: StandardResponse to format
        include_metadata: Whether to include timing/metadata
        
    Returns:
        JSON formatted response string
    """
    response_dict = response.dict(exclude_none=True)
    
    if not include_metadata:
        # Remove technical metadata for cleaner output
        response_dict.pop('processing_time_ms', None)
        response_dict.pop('timestamp', None)
    
    return response.json(ensure_ascii=False, indent=2)


def extract_response_data(response_json: str, expected_type: type = None) -> Any:
    """
    Safely extract data from a response JSON string
    
    Args:
        response_json: JSON response string
        expected_type: Expected data type for validation
        
    Returns:
        Extracted data or None if extraction fails
    """
    try:
        import json
        response_dict = json.loads(response_json)
        
        if response_dict.get("status") != "success":
            logger.warning(f"⚠️ Non-success response: {response_dict.get('message')}")
            return None
        
        data = response_dict.get("data")
        
        if expected_type and data:
            # Validate data type if specified
            if not isinstance(data, expected_type):
                logger.warning(f"⚠️ Data type mismatch: expected {expected_type}, got {type(data)}")
                return None
        
        return data
        
    except Exception as e:
        logger.error(f"❌ Failed to extract response data: {e}")
        return None


def merge_agent_responses(responses: list, primary_agent: str) -> StandardResponse:
    """
    Merge multiple agent responses into a single response
    
    Args:
        responses: List of StandardResponse objects
        primary_agent: Name of the primary agent for the merged response
        
    Returns:
        Merged StandardResponse
    """
    if not responses:
        return create_error_response(primary_agent, "No responses to merge")
    
    # Check if any responses failed
    failed_responses = [r for r in responses if r.status == StatusType.ERROR]
    if failed_responses:
        error_messages = [r.message for r in failed_responses]
        return create_error_response(
            primary_agent,
            f"Multiple agent failures: {'; '.join(error_messages)}"
        )
    
    # Check for warnings
    warning_responses = [r for r in responses if r.status == StatusType.WARNING]
    if warning_responses:
        warning_messages = [r.message for r in warning_responses]
        return create_warning_response(
            primary_agent,
            f"Partial success with warnings: {'; '.join(warning_messages)}"
        )
    
    # All successful
    total_processing_time = sum(
        r.processing_time_ms for r in responses 
        if r.processing_time_ms is not None
    )
    
    avg_confidence = None
    confidence_scores = [
        r.confidence_score for r in responses 
        if r.confidence_score is not None
    ]
    if confidence_scores:
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
    
    return create_success_response(
        agent_name=primary_agent,
        message=f"Successfully merged {len(responses)} agent responses",
        confidence_score=avg_confidence,
        processing_time_ms=total_processing_time
    )


def validate_response_chain(responses: list, expected_sequence: list) -> bool:
    """
    Validate that a sequence of agent responses follows the expected pattern
    
    Args:
        responses: List of agent responses
        expected_sequence: List of expected agent names in order
        
    Returns:
        True if sequence is valid, False otherwise
    """
    if len(responses) != len(expected_sequence):
        logger.error(f"❌ Response chain length mismatch: got {len(responses)}, expected {len(expected_sequence)}")
        return False
    
    for i, (response, expected_agent) in enumerate(zip(responses, expected_sequence)):
        if response.agent_name != expected_agent:
            logger.error(f"❌ Response chain sequence error at position {i}: got {response.agent_name}, expected {expected_agent}")
            return False
        
        if response.status == StatusType.ERROR:
            logger.error(f"❌ Response chain broken at {expected_agent}: {response.message}")
            return False
    
    logger.info(f"✅ Response chain validated successfully: {' → '.join(expected_sequence)}")
    return True