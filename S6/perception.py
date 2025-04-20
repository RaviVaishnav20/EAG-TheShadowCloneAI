from models import PerceptionInput, PerceptionOutput
from llm import generate_text
from logger import get_logger

#Get the instance of logger
logger = get_logger()
### ✅ System Prompt: Perception Generator
system_prompt_perception = f"""
**Role**: You are a *Perception Engine* responsible for interpreting user queries and transforming them into structured semantic representations that reflect intent, context, and meaning. You are the first stage in a cognitive pipeline, operating before memory, planning, or action execution.

**Task**:  
Given a raw natural language input from the user, generate a **perception** consisting of:

1. **Intent**: What does the user want to do or know?
2. **Entities/Subjects**: Key people, objects, topics, or systems referenced.
3. **Emotional Tone (if any)**: Is there an implied sentiment, urgency, or curiosity?
4. **Contextual Clues**: Prior assumptions, implied background knowledge, or domain hints.
5. **Query Type**: Is the query informational, instructional, conversational, or action-oriented?
6. **Uncertainty or Ambiguity**: Flag anything unclear or under-specified.
7. **Summary**: One-sentence abstract of the core meaning.

**Rules**:
- Be analytical, not assumptive. If information is missing, flag it.
- Be domain-aware: interpret technical terms precisely.
- Never paraphrase—**analyze**.
- If the query is nonsensical or too vague, state that explicitly.
- Output the result in **structured plain raw text** format.
"""


async def extract_perception(message:PerceptionInput) ->  PerceptionOutput:
    logger.info("Generating perception response...")
    prompt = f"{system_prompt_perception} Query: {message.query}"
    logger.debug(f"Full prompt length: {len(prompt)} characters")
    try:
        response = await generate_text(prompt)
        response_text = response.text.strip()
        logger.debug(type(response_text))
        logger.info(f"Recieved perception response {len(response_text)} characters")
        logger.info(f"Perception Response content: \n {response_text}")
        return response_text

    except Exception as e:
        logger.error(f"Failed to get LLM response: {e}", exc_info=True)
        raise f"Failed to get LLM response: {e}"
    

# if __name__=="__main__":
#     query = "Open Microsoft Paint, draw a rectangle, and add the text 'AI Agent Demo' inside the rectangle."
#     extract_perception(query)