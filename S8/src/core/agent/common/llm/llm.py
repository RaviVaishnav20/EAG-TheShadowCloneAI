import json
import pprint
import httpx
import requests
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.resolve()  # This gets /Users/ravi/EAG-TheShadowCloneAI/S8

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.common.config.env_config import env_config
from src.core.agent.common.schema.custom_llm_payload import CustomPayload
from src.common.logger.logger import get_logger

logger = get_logger()

class CustomLLM:
    """
    A custom class to interact with Lambda Labs' AI layer API for invoking an LLM.

    This class sends a request to the AI API with configurable parameters such as
    max tokens, temperature, provider, top-p sampling, and additional prompts.
    """

    async def invoke(self, custom_payload: CustomPayload) -> str:
        """
        Asynchronously invokes the LLM with specified parameters and returns the response.

        Parameters:
        -----------
        kwargs : dict
            - max_tokens (int, optional): The maximum number of tokens to generate. Default is 1000.
            - temperature (float, optional): Sampling temperature for randomness. Default is 0.7.
            - provider (str, optional): Specifies the LLM provider. Default is "default".
            - top_p (float, optional): Nucleus sampling parameter (between 0 and 1). Default is 0.9.
            - domain (str, optional): The domain/context for the response. Default is "general".
            - addition_system_prompt (str, optional): Additional system prompt for the model. Default is "".

        Returns:
        --------
        str
            The response from the AI model as a JSON string.

        Raises:
        -------
        RuntimeError
            If the API request fails due to an HTTP error or JSON decoding issue.

        Example Usage:
        -------------
        ```python
        llm = CustomLLM()
        response = await llm.invoke(
            max_tokens=1000,
            temperature=0.7,
            provider="bedrock",
            top_p=0.9,
            domain="general",
            addition_system_prompt="",
        )
        print(response)
        ```
        """

        headers = {
            "username": env_config.AI_LAYER_API_USERNAME,
            "X-API-Key": env_config.AI_LAYER_API_KEY,
        }

        async with httpx.AsyncClient(timeout=20) as client:
            logger.info(f"Sending request to AI Layer-> model: '{custom_payload.provider}'  max_tokens: {custom_payload.max_tokens}  temperature: {custom_payload.temperature}  top_p: {custom_payload.top_p}  domain: '{custom_payload.domain}'")
            try:
                
                response = await client.post(
                    env_config.AI_LAYER_API_BASE_URL,
                    json=custom_payload.model_dump(),
                    headers=headers,
                )

                response.raise_for_status()
                # print(response.json()["generated_text"])
                return response.json()["generated_text"]
            except (httpx.HTTPError, json.JSONDecodeError) as e:
                raise RuntimeError(f"LLM Invoke Failed: {e}") from e
        return ""
    

if __name__=="__main__":
    import asyncio
    custom_payload = CustomPayload(
            prompt="Hi",
        )
    model = CustomLLM()
    result = asyncio.run(model.invoke(custom_payload))
    print(result)

