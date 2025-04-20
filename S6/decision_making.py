from llm import generate_with_timeout
from models import DECISION_INPUT
from universal_system_prompt import get_system_prompt
from logger import get_logger

#Get the instance of logger
logger = get_logger()

async def get_decision(input:DECISION_INPUT):

    system_prompt = get_system_prompt(input.tools_description)
    # print(system_prompt)
    
    current_query = input.query + "\n\n"+"All previous operations:"+ "\n\n" + " ".join(input.chat_history)
    current_query = current_query + "  What should I do next?"
    
    # Get model's response with timeout
    logger.info("Generating decision response...")
    prompt = f"{system_prompt}\n\nQuery: {current_query}"
    logger.debug(f"Full prompt length: {len(prompt)} characters")

    try:
        response = await generate_with_timeout(prompt)
        response_text = response.text.strip()
        logger.debug(type(response_text))
        logger.info(f"Recieved decision response {len(response_text)} characters")
        logger.info(f"Decision Response content: \n {response_text}")
        return response_text

    except Exception as e:
        logger.error(f"Failed to get LLM response: {e}", exc_info=True)
        raise f"Failed to get LLM response: {e}"