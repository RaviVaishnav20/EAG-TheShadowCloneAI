import asyncio
from functools import lru_cache
from google import genai
from config import Config

class LLMClient:
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.model = "gemini-2.0-flash"
    
    @lru_cache(maxsize=100)
    async def generate(self, prompt, timeout=Config.LLM_TIMEOUT):
        try:
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: self.client.models.generate_content(
                        model=self.model,
                        contents=prompt
                    )
                ),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise TimeoutError("LLM generation timed out")
        except Exception as e:
            raise RuntimeError(f"LLM generation failed: {str(e)}")