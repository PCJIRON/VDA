"""
Qwen API client.

Uses OpenAI SDK with OAuth token (same as qwen-code's QwenContentGenerator).
OAuth token is used as API key with DashScope provider.
"""

from typing import Optional, AsyncGenerator, List, Dict, Any
from datetime import timedelta
import logging
import os

from openai import AsyncOpenAI

from qwen_desktop.config.settings import Settings
from qwen_desktop.auth.oauth_handler import OAuthHandler
from qwen_desktop.utils.rate_limiter import RateLimiter


logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    def __init__(self, message: str, wait_time: Optional[timedelta] = None):
        super().__init__(message)
        self.wait_time = wait_time


class APIClient:
    """Client for Qwen API using OpenAI SDK (same as qwen-code's QwenContentGenerator)."""

    # DashScope API endpoint (same as qwen-code)
    DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"

    def __init__(
        self,
        settings: Settings,
        oauth_handler: Optional[OAuthHandler] = None,
    ) -> None:
        """Initialize API client.
        
        Args:
            settings: Application settings.
            oauth_handler: OAuth handler for authentication.
        """
        self.settings = settings
        self.oauth_handler = oauth_handler
        
        # Rate limiter for OAuth free tier (1000 requests/day)
        self.rate_limiter = RateLimiter(max_requests=1000, period_seconds=86400)
        
        # Get OAuth token (same as qwen-code's getQwenOAuthClient)
        token = None
        endpoint = self.DASHSCOPE_BASE_URL
        
        if oauth_handler and oauth_handler.is_authenticated():
            logger.info("OAuth is authenticated, getting token...")
            if oauth_handler.refresh_token_if_needed():
                token = oauth_handler.token_manager.get_access_token()
                logger.info(f"Token obtained, length: {len(token) if token else 0}")
                
                # Get custom endpoint URL from OAuth credentials
                resource_url = oauth_handler.token_manager.credentials.get_resource_url()
                if resource_url:
                    if not resource_url.startswith("http"):
                        resource_url = f"https://{resource_url}"
                    if not resource_url.endswith("/v1"):
                        resource_url = f"{resource_url}/v1"
                    endpoint = resource_url
                    logger.info(f"Using OAuth resource URL: {endpoint}")
            else:
                logger.error("Token refresh failed!")
        else:
            logger.warning("OAuth not authenticated")
        
        if not token:
            logger.error("No OAuth token available!")
            # Fall back to environment variable
            token = os.getenv("DASHSCOPE_API_KEY", "sk-placeholder")
            logger.info(f"Using fallback API key")
        
        logger.info(f"Using token: {token[:20]}... (length: {len(token) if token else 0})")
        
        # Create OpenAI client with DashScope provider (same as qwen-code)
        self.client = AsyncOpenAI(
            api_key=token,
            base_url=endpoint,
            default_headers={
                "User-Agent": "Qwen-Desktop/0.4.0 (Windows; amd64)",
                "X-DashScope-AuthType": "qwen-oauth",
                "X-DashScope-CacheControl": "enable",
                "X-DashScope-UserAgent": "Qwen-Desktop/0.4.0 (Windows; amd64)",
            },
            timeout=settings.get("api_timeout", 60),
            max_retries=3,
        )
        
        logger.info(f"Qwen API client initialized with DashScope provider")
        logger.info(f"Base URL: {endpoint}")

    async def send_message(
        self,
        message: str,
        conversation_history: List[Dict[str, Any]],
        attachments: Optional[List] = None,
    ) -> AsyncGenerator[str, None]:
        """Send a message and stream the response (same as qwen-code).
        
        Args:
            message: User message.
            conversation_history: Previous messages.
            attachments: Optional file attachments.
            
        Yields:
            Response content chunks.
        """
        # Check rate limit
        if not self.rate_limiter.acquire():
            wait_time = self.rate_limiter.wait_time()
            raise RateLimitError(
                f"Rate limit exceeded (1000 requests/day). Wait {wait_time}",
                wait_time
            )
        
        try:
            # Get model from settings
            model = self.settings.get("api_model", "qwen-coder-plus")
            
            # Qwen OAuth endpoints require the specific 'coder-model' identifier
            if self.oauth_handler and self.oauth_handler.is_authenticated() and self.client.base_url:
                if "qwen.ai" in str(self.client.base_url):
                    model = "coder-model"
                    
            logger.info(f"Using model: {model}")
            
            # Build messages list
            messages = conversation_history.copy()
            messages.append({"role": "user", "content": message})
            
            logger.info(f"Sending {len(messages)} messages...")
            
            # Try sending request (with automatic refresh on 401)
            retry_count = 0
            max_retries = 1
            
            while retry_count <= max_retries:
                try:
                    # Stream response using OpenAI SDK (same as qwen-code)
                    stream = await self.client.chat.completions.create(
                        model=model,
                        messages=messages,
                        stream=True,
                        temperature=0.7,
                    )
                    
                    logger.info("Streaming response...")
                    chunk_count = 0
                    async for chunk in stream:
                        chunk_count += 1
                        if chunk.choices and len(chunk.choices) > 0:
                            delta = chunk.choices[0].delta
                            if getattr(delta, "content", None):
                                logger.info(f"Chunk {chunk_count}: {delta.content[:50]}...")
                                yield delta.content
                            elif getattr(delta, "reasoning_content", None):
                                # The model is thinking. We can log it but DO NOT yield it to the UI 
                                # to prevent spamming the user with internal monologue.
                                pass
                            else:
                                logger.info(f"Chunk {chunk_count} has no content/reasoning. Delta: {delta}")
                        else:
                            logger.info(f"Chunk {chunk_count} has no choices")
                    
                    logger.info(f"Response complete, total chunks: {chunk_count}")
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    error_message = str(e)
                    # Check if it's an auth error and we have an oauth handler
                    if ("401" in error_message or "invalid_api_key" in error_message) and self.oauth_handler and retry_count < max_retries:
                        logger.warning(f"Got 401 Unauthorized. Forcing token refresh (attempt {retry_count + 1})...")
                        # Force token refresh
                        success = self.oauth_handler.token_manager.refresh_access_token(
                            self.oauth_handler.client_id,
                            self.oauth_handler.client_secret,
                            self.oauth_handler.TOKEN_URL
                        )
                        
                        if success:
                            new_token = self.oauth_handler.token_manager.get_access_token()
                            new_resource_url = self.oauth_handler.token_manager.credentials.get_resource_url()
                            logger.info("Token explicitly refreshed. Updating client and retrying...")
                            
                            self.client.api_key = new_token
                            if new_resource_url:
                                if not new_resource_url.startswith("http"):
                                    new_resource_url = f"https://{new_resource_url}"
                                if not new_resource_url.endswith("/v1"):
                                    new_resource_url = f"{new_resource_url}/v1"
                                self.client.base_url = new_resource_url
                                if "qwen.ai" in new_resource_url:
                                    model = "coder-model"
                                    logger.info(f"Updated model identifier to {model} for Qwen endpoint")
                            
                            retry_count += 1
                        else:
                            logger.error("Failed to refresh token during 401 recovery loop.")
                            raise Exception("Authentication failed. Your session expired and could not be refreshed. Please restart and run /auth.")
                    else:
                        raise e
            
        except Exception as e:
            logger.error(f"API error: {e}", exc_info=True)
            error_message = str(e)
            
            if "401" in error_message or "Unauthorized" in error_message:
                yield "Error: Authentication failed (401). OAuth token may be expired. Please login again."
            elif "400" in error_message:
                yield f"Error: Bad request (400). {error_message}"
            else:
                yield f"Error: {error_message}"

    async def chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """Send chat request (wrapper for send_message).
        
        Args:
            messages: List of message dictionaries.
            model: Model to use.
            stream: Whether to stream responses.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens to generate.
            
        Yields:
            Response content chunks.
        """
        # Get last message as current message
        current_message = messages[-1]["content"] if messages else ""
        history = messages[:-1] if len(messages) > 1 else []
        
        async for chunk in self.send_message(current_message, history):
            yield chunk
