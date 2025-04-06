import asyncio
from functools import lru_cache
from google import genai
from llm_utils import generate_with_timeout

class OptimizedLLM:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.pending_requests = []
        
    @lru_cache(maxsize=100)
    async def cached_generate(self, prompt, timeout=8):
        return await generate_with_timeout(self.client, prompt, timeout)
        
    async def batch_generate(self, prompts, timeout=10):
        tasks = [self.cached_generate(prompt, timeout) for prompt in prompts]
        return await asyncio.gather(*tasks, return_exceptions=True)