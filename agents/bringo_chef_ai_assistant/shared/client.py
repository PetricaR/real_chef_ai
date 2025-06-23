# agents/shared/client.py
# Professional async AI client with threading support for optimal performance
# Handles all AI communication with proper error handling and rate limiting

import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import asynccontextmanager

from google import genai
from google.genai import types
from google.cloud import secretmanager

from .config import settings
from .models import StandardResponse, StatusType

# Configure professional logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format=settings.log_format
)
logger = logging.getLogger("bringo_ai_client")


class AsyncAIClient:
    """
    Professional async AI client for BringoChef system.
    Handles all AI operations with proper error handling, rate limiting, and performance optimization.
    """
    
    def __init__(self):
        self._client: Optional[genai.Client] = None
        self._executor = ThreadPoolExecutor(max_workers=settings.max_concurrent_requests)
        self._rate_limiter = asyncio.Semaphore(settings.max_concurrent_requests)
        self._initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the AI client with proper authentication"""
        if self._initialized:
            return True
            
        try:
            # Initialize Vertex AI client
            self._client = genai.Client(
                vertexai=True,
                project=settings.project_id,
                location=settings.location
            )
            
            # Test the connection
            await self._test_connection()
            self._initialized = True
            logger.info("✅ AI client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI client: {e}")
            return False
    
    async def _test_connection(self) -> None:
        """Test AI client connection with a simple request"""
        test_prompt = "Respond with: 'connection_test_successful'"
        response = await self.generate_text(
            prompt=test_prompt,
            temperature=0.0,
            max_tokens=50
        )
        if "connection_test_successful" not in response.get("content", ""):
            raise Exception("AI client connection test failed")
    
    @asynccontextmanager
    async def _rate_limited(self):
        """Rate limiting context manager"""
        async with self._rate_limiter:
            yield
    
    async def generate_text(
        self,
        prompt: str,
        temperature: float = None,
        max_tokens: int = None,
        response_format: str = "json",
        agent_name: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Generate text using AI with professional error handling
        
        Args:
            prompt: The input prompt
            temperature: AI creativity level (0.0-1.0)
            max_tokens: Maximum response tokens
            response_format: Expected response format ("json" or "text")
            agent_name: Calling agent name for logging
            
        Returns:
            Dict containing the AI response and metadata
        """
        if not self._initialized:
            await self.initialize()
            
        if not self._client:
            return {"error": "AI client not available", "content": None}
        
        # Use defaults if not specified
        temperature = temperature or settings.conservative_temperature
        max_tokens = max_tokens or settings.max_tokens
        
        start_time = time.time()
        
        async with self._rate_limited():
            try:
                logger.info(f"🤖 Generating response for {agent_name} (temp: {temperature})")
                
                response = await asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    self._sync_generate_text,
                    prompt,
                    temperature,
                    max_tokens,
                    response_format
                )
                
                processing_time = int((time.time() - start_time) * 1000)
                logger.info(f"✅ Response generated in {processing_time}ms for {agent_name}")
                
                return {
                    "content": response,
                    "processing_time_ms": processing_time,
                    "model_used": settings.text_model,
                    "temperature": temperature,
                    "error": None
                }
                
            except Exception as e:
                processing_time = int((time.time() - start_time) * 1000)
                logger.error(f"❌ Text generation failed for {agent_name}: {e}")
                
                return {
                    "error": str(e),
                    "content": None,
                    "processing_time_ms": processing_time,
                    "agent_name": agent_name
                }
    
    def _sync_generate_text(
        self,
        prompt: str,
        temperature: float,
        max_tokens: int,
        response_format: str
    ) -> str:
        """Synchronous text generation for executor"""
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json" if response_format == "json" else "text/plain"
        )
        
        response = self._client.models.generate_content(
            model=settings.text_model,
            contents=[types.Content(role="user", parts=[types.Part(text=prompt)])],
            config=config
        )
        
        return response.text
    
    async def generate_images(
        self,
        prompts: List[str],
        agent_name: str = "unknown"
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple images concurrently
        
        Args:
            prompts: List of image generation prompts
            agent_name: Calling agent name for logging
            
        Returns:
            List of generation results
        """
        if not self._initialized:
            await self.initialize()
            
        if not self._client:
            return [{"error": "AI client not available", "image_data": None} for _ in prompts]
        
        logger.info(f"🎨 Generating {len(prompts)} images for {agent_name}")
        start_time = time.time()
        
        # Create tasks for concurrent generation
        tasks = []
        for i, prompt in enumerate(prompts):
            task = self._generate_single_image(prompt, i + 1, len(prompts))
            tasks.append(task)
        
        # Wait for all images to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        successful_generations = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"❌ Image {i+1} generation failed: {result}")
                processed_results.append({
                    "error": str(result),
                    "image_data": None,
                    "step_number": i + 1
                })
            else:
                processed_results.append(result)
                if result.get("image_data"):
                    successful_generations += 1
        
        total_time = int((time.time() - start_time) * 1000)
        logger.info(f"✅ Generated {successful_generations}/{len(prompts)} images in {total_time}ms")
        
        return processed_results
    
    async def _generate_single_image(
        self,
        prompt: str,
        step_number: int,
        total_steps: int
    ) -> Dict[str, Any]:
        """Generate a single image with error handling"""
        async with self._rate_limited():
            try:
                # Add small delay between generations to avoid rate limits
                if step_number > 1:
                    await asyncio.sleep(1)
                
                result = await asyncio.get_event_loop().run_in_executor(
                    self._executor,
                    self._sync_generate_image,
                    prompt
                )
                
                logger.info(f"✅ Generated image {step_number}/{total_steps}")
                
                return {
                    "image_data": result,
                    "step_number": step_number,
                    "prompt": prompt,
                    "error": None
                }
                
            except Exception as e:
                logger.error(f"❌ Image {step_number} generation failed: {e}")
                return {
                    "error": str(e),
                    "image_data": None,
                    "step_number": step_number,
                    "prompt": prompt
                }
    
    def _sync_generate_image(self, prompt: str) -> bytes:
        """Synchronous image generation for executor"""
        response = self._client.models.generate_images(
            model=settings.image_model,
            prompt=prompt,
            config={'number_of_images': 1}
        )
        
        if not response.generated_images:
            raise Exception("No images generated")
            
        return response.generated_images[0].image.image_bytes
    
    async def parallel_text_generation(
        self,
        prompts: List[Dict[str, Any]],
        agent_name: str = "unknown"
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple text responses in parallel
        
        Args:
            prompts: List of prompt configurations with keys: 'prompt', 'temperature', 'max_tokens'
            agent_name: Calling agent name
            
        Returns:
            List of generation results
        """
        logger.info(f"🔄 Running {len(prompts)} parallel text generations for {agent_name}")
        
        tasks = []
        for i, prompt_config in enumerate(prompts):
            task = self.generate_text(
                prompt=prompt_config.get("prompt"),
                temperature=prompt_config.get("temperature"),
                max_tokens=prompt_config.get("max_tokens"),
                response_format=prompt_config.get("response_format", "json"),
                agent_name=f"{agent_name}_task_{i+1}"
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "error": str(result),
                    "content": None,
                    "task_number": i + 1
                })
            else:
                processed_results.append({**result, "task_number": i + 1})
        
        return processed_results
    
    async def close(self):
        """Cleanup resources"""
        if self._executor:
            self._executor.shutdown(wait=True)
        logger.info("🧹 AI client resources cleaned up")


# Global client instance
_ai_client: Optional[AsyncAIClient] = None


async def get_ai_client() -> AsyncAIClient:
    """Get the global AI client instance, initializing if necessary"""
    global _ai_client
    
    if _ai_client is None:
        _ai_client = AsyncAIClient()
        await _ai_client.initialize()
    
    return _ai_client


async def call_ai_with_validation(
    prompt: str,
    expected_model: type,
    agent_name: str = "unknown",
    temperature: float = None,
    max_retries: int = None
) -> Dict[str, Any]:
    """
    Call AI with automatic response validation using Pydantic models
    
    Args:
        prompt: The AI prompt
        expected_model: Pydantic model class for validation
        agent_name: Calling agent name
        temperature: AI temperature
        max_retries: Maximum retry attempts
        
    Returns:
        Validated response or error information
    """
    client = await get_ai_client()
    max_retries = max_retries or settings.max_retry_attempts
    
    for attempt in range(max_retries):
        try:
            # Generate response
            response = await client.generate_text(
                prompt=prompt,
                temperature=temperature,
                agent_name=agent_name
            )
            
            if response.get("error"):
                raise Exception(response["error"])
            
            # Parse and validate JSON
            content = response.get("content", "")
            parsed_data = json.loads(content)
            
            # Validate with Pydantic model
            validated_data = expected_model(**parsed_data)
            
            return {
                "success": True,
                "data": validated_data,
                "raw_response": response,
                "attempt": attempt + 1
            }
            
        except json.JSONDecodeError as e:
            logger.warning(f"⚠️ JSON parsing failed on attempt {attempt + 1}: {e}")
        except Exception as e:
            logger.warning(f"⚠️ Validation failed on attempt {attempt + 1}: {e}")
        
        if attempt < max_retries - 1:
            await asyncio.sleep(1)  # Brief pause before retry
    
    return {
        "success": False,
        "error": f"Failed after {max_retries} attempts",
        "data": None
    }