# agents/bringo_chef_ai_assistant/shared/client.py
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
        self._initializing = False  # Prevent recursive initialization
        
    async def initialize(self) -> bool:
        """Initialize the AI client with proper authentication"""
        if self._initialized:
            return True
            
        if self._initializing:
            # Wait for ongoing initialization
            while self._initializing and not self._initialized:
                await asyncio.sleep(0.1)
            return self._initialized
            
        self._initializing = True
        
        try:
            # Initialize Vertex AI client
            self._client = genai.Client(
                vertexai=True,
                project=settings.project_id,
                location=settings.location
            )
            
            # Test the connection with direct API call (avoid recursion)
            await self._test_connection_direct()
            self._initialized = True
            logger.info("✅ AI client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI client: {e}")
            return False
        finally:
            self._initializing = False
    
    async def _test_connection_direct(self) -> None:
        """Test AI client connection with a direct API call"""
        if not self._client:
            raise Exception("Client not initialized")
            
        try:
            test_prompt = "Respond with: 'connection_test_successful'"
            
            # Direct API call without going through generate_text to avoid recursion
            config = types.GenerateContentConfig(
                temperature=0.0,
                max_output_tokens=50,
                response_mime_type="text/plain"
            )
            
            response = await asyncio.get_event_loop().run_in_executor(
                self._executor,
                lambda: self._client.models.generate_content(
                    model=settings.text_model,
                    contents=[types.Content(role="user", parts=[types.Part(text=test_prompt)])],
                    config=config
                )
            )
            
            response_text = response.text if response and hasattr(response, 'text') else ""
            
            if not response_text or "connection_test_successful" not in response_text:
                raise Exception("AI client connection test failed - unexpected response")
                
        except Exception as e:
            raise Exception(f"AI client connection test failed: {str(e)}")
    
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
        # Initialize if needed (but avoid recursive calls during initialization)
        if not self._initialized and not self._initializing:
            initialization_success = await self.initialize()
            if not initialization_success:
                return {
                    "error": "AI client initialization failed",
                    "content": None,
                    "processing_time_ms": 0,
                    "agent_name": agent_name
                }
            
        if not self._client:
            return {
                "error": "AI client not available", 
                "content": None,
                "processing_time_ms": 0,
                "agent_name": agent_name
            }
        
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
        try:
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
            
            if not response or not hasattr(response, 'text'):
                raise Exception("Invalid response from AI model")
                
            return response.text
            
        except Exception as e:
            logger.error(f"Sync text generation error: {e}")
            raise
    
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
        if not self._initialized and not self._initializing:
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
        async with self._rate_limiter:
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
        try:
            response = self._client.models.generate_images(
                model=settings.image_model,
                prompt=prompt,
                config={'number_of_images': 1}
            )
            
            if not response.generated_images:
                raise Exception("No images generated")
                
            return response.generated_images[0].image.image_bytes
            
        except Exception as e:
            logger.error(f"Sync image generation error: {e}")
            raise
    
    async def close(self):
        """Cleanup resources"""
        if self._executor:
            self._executor.shutdown(wait=True)
        self._initialized = False
        self._initializing = False
        logger.info("🧹 AI client resources cleaned up")


# Global client instance
_ai_client: Optional[AsyncAIClient] = None


async def get_ai_client() -> AsyncAIClient:
    """Get the global AI client instance, initializing if necessary"""
    global _ai_client
    
    if _ai_client is None:
        _ai_client = AsyncAIClient()
        # Don't auto-initialize here to avoid issues
        # Let the first call to generate_text handle initialization
    
    return _ai_client