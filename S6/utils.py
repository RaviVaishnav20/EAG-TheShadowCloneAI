import re
import json


def extract_function_call(response: str) -> dict:
    """
    Extracts the FUNCTION_CALL part from an LLM response string.

    Args:
        response (str): Full LLM response containing THINK, VERIFY, FUNCTION_CALL sections.

    Returns:
        dict: Parsed FUNCTION_CALL dictionary with 'name' and 'args'.
    """
    # Match FUNCTION_CALL followed by optional spaces/newlines and then the JSON block
    match = re.search(r'FUNCTION_CALL:\s*\n?\s*(\{.*\})', response, re.DOTALL)
    if match:
        json_str = match.group(1).strip()
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid FUNCTION_CALL JSON format:\n{json_str}") from e
    else:
        raise ValueError("No FUNCTION_CALL found in the response.")