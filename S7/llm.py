import asyncio
from google import genai
from concurrent.futures import TimeoutError
import os
from dotenv import load_dotenv
from logger import get_logger

#Get the instance of logger
logger = get_logger()
# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")


async def generate_with_timeout(prompt, timeout=10):
    """Generate content with a timeout"""
    logger.info("Starting LLM generation...")
    try:
        client = genai.Client(api_key=api_key)
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        logger.debug(f"Using model: gemini-2.0-flash, prompt size: {len(prompt)} chars")
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        logger.info("LLM generation completed successfully")
        return response
    except TimeoutError:
        logger.error(f"LLM generation timed out after {timeout} seconds!")
        raise
    except Exception as e:
        logger.error(f"Error in LLM generation: {e}", exc_info=True)
        raise


async def generate_text(prompt):
    """Generate content """
    logger.info("Starting LLM generation...")
    try:
        client = genai.Client(api_key=api_key)
        logger.debug(f"Using model: gemini-2.0-flash, prompt size: {len(prompt)} chars")
        response =  client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            
        logger.info("LLM generation completed")
        return response
    except Exception as e:
        logger.error(f"Error in LLM generation: {e}", exc_info=True)
        raise