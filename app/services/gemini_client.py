import logging
import json
from typing import Optional, Dict, Any
from app.config import settings

logger = logging.getLogger("gemini_client")

# Optional import wrapper to safely handle environments before SDK is installed or initialized
try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError
    GENAI_AVAILABLE = True
except ImportError:
    genai = None
    types = None
    APIError = Exception
    GENAI_AVAILABLE = False


class GeminiClient:
    """Wrapper service for Google GenAI SDK (Gemini API)."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self._client = None

        if self.api_key and GENAI_AVAILABLE:
            try:
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Gemini Client: {e}")

    def is_configured(self) -> bool:
        """Check if Gemini Client is properly configured with an API key."""
        return bool(self.api_key and self.api_key != "your_gemini_api_key_here")

    def _get_client(self):
        """Lazy loader or validator for genai Client."""
        if not GENAI_AVAILABLE:
            raise RuntimeError("The google-genai library is not installed in the environment.")
        if not self.is_configured():
            raise ValueError(
                "Gemini API key is not configured. Please set GEMINI_API_KEY in your .env file or environment variables."
            )
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3,
        max_output_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text response from Gemini given a prompt and optional system instructions.
        Handles API errors, quota exhaustion, and timeouts gracefully.
        """
        client = self._get_client()
        try:
            config = None
            if types:
                config_kwargs: Dict[str, Any] = {"temperature": temperature}
                if system_instruction:
                    config_kwargs["system_instruction"] = system_instruction
                if max_output_tokens:
                    config_kwargs["max_output_tokens"] = max_output_tokens
                config = types.GenerateContentConfig(**config_kwargs)

            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )

            if response and response.text:
                return response.text.strip()
            return ""

        except APIError as api_err:
            logger.error(f"Google Gemini API error: {api_err}")
            raise RuntimeError(f"Gemini API request failed: {api_err.message if hasattr(api_err, 'message') else str(api_err)}")
        except Exception as e:
            logger.error(f"Unexpected error communicating with Gemini API: {e}")
            raise RuntimeError(f"Failed to generate response from Gemini: {str(e)}")

    def generate_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Generate a structured JSON response from Gemini.
        Requests application/json output and safely parses the result.
        """
        client = self._get_client()
        try:
            config = None
            if types:
                config_kwargs: Dict[str, Any] = {
                    "temperature": temperature,
                    "response_mime_type": "application/json"
                }
                if system_instruction:
                    config_kwargs["system_instruction"] = system_instruction
                config = types.GenerateContentConfig(**config_kwargs)

            response = client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )

            raw_text = response.text.strip() if response and response.text else "{}"
            # Clean markdown codeblocks if returned
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            if raw_text.startswith("```"):
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]

            return json.loads(raw_text.strip())

        except json.JSONDecodeError as json_err:
            logger.error(f"Failed to parse JSON from Gemini response: {json_err}. Raw text: {response.text}")
            raise ValueError("Gemini returned invalid JSON structure.")
        except APIError as api_err:
            logger.error(f"Google Gemini API error during JSON generation: {api_err}")
            raise RuntimeError(f"Gemini API request failed: {api_err.message if hasattr(api_err, 'message') else str(api_err)}")
        except Exception as e:
            logger.error(f"Unexpected error during structured Gemini call: {e}")
            raise RuntimeError(f"Failed to generate structured data from Gemini: {str(e)}")


# Singleton instance for application use
gemini_service = GeminiClient()
