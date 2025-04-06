from dotenv import load_dotenv
from google import genai
import os
import asyncio
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

max_iteration = 3
last_response = None
iteration = 0
iteration_response = []

async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with timeout"""
    print("Starting LLM generation")

    try:
        loop = asyncio.get_event_loop()
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
        print("LLM generation completed")
        return response
    
    except TimeoutError:
        print("LLM generation timeout!")
        raise
    except Exception as e:
        print(f"Error in LL generation {e}")
        raise
