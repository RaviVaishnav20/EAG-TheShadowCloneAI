from pydantic import BaseModel
from typing import Optional, List
import os
from dotenv import load_dotenv
# from google import genai
from llm import CustomLLM, CustomPayload
import re
from logger import get_logger

logger = get_logger()

load_dotenv()

# client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

class PerceptionResult(BaseModel):
    user_input: str
    intent: Optional[str]
    entities: List[str] = []
    tool_hint: Optional[str] = None

async def extract_perception(user_input: str) -> PerceptionResult:
    "Extract intent, entities, and tool hints using LLM"

    prompt = f""" 
                You are an AI that extracts structured facts from user input.

                Input: "{user_input}"

                Return the response as a Python dictionary with keys:
                - intent: (brief phrase about what the user wants)
                - entities: a list of strings representing keywords or values (e.g., ["INDIA", "ASCII"])
                - tool_hint: (name of the MCP tool that might be useful, if any else None)

                Output only the dictionary on a single line. Do NOT wrap it in ```json or other formatting. Ensure `entities` is a list of strings, not a dictionary.
            """
    try:
        # response = client.models.generate_content(
        #     model="gemini-2.0-flash",
        #     contents=prompt
        # )
        custom_payload = CustomPayload(
            prompt=prompt,
        )
        model = CustomLLM()
        response = await model.invoke(custom_payload)
        raw =response.strip()   #raw =response.text.strip()
        logger.info(f"Perception, LLM output: {raw}")

        clean = re.sub(r"^```json|```$","", raw.strip(), flags=re.MULTILINE).strip()

        try:
            parsed = eval(clean)
        except Exception as e:
            logger.error(f"Perception, ⚠️ Failed to parse cleaned output: {e}", exc_info=True)
            raise
        #Fix comman issues
        if isinstance(parsed.get("entities"), dict):
            parsed["entities"] = list(parsed["entities"].values())

        return PerceptionResult(user_input=user_input, **parsed)
    except Exception as e:
        logger.error(f"perception, ⚠️ Extraction failed: {e}", exc_info=True)
        return PerceptionResult(user_input=user_input)
