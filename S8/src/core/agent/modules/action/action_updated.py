from typing import Tuple, Any, Dict, List, Union
from pydantic import BaseModel
from mcp import ClientSession
from pathlib import Path
import sys
import json

ROOT = Path(__file__).parent.parent.parent.resolve()  # This gets /Users/ravi/EAG-TheShadowCloneAI/S8

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))


from src.common.logger.logger import get_logger
logger = get_logger()

class ToolCallResult(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]
    result: Union[str, list, dict]
    raw_response: Any


def parse_function_call(response: str, tools_result: Dict[str, Any]) -> Tuple[str, dict]:
    """
    Parses a FUNCTION_CALL LLM response and validates it against available tools.
    
    Args:
        response (str): Raw string from the LLM starting with FUNCTION_CALL:
        tools_result (Dict[str, Any]): Dictionary mapping function names to Tool objects
    
    Returns:
        Tuple[str, dict]: (func_name, validated arguments dict)
    
    Raises:
        ValueError: If parsing fails, tool not found, or args invalid.
    """
    
    # Step 1: Extract and parse JSON from response
    prefix = "FUNCTION_CALL:"
    if not response.startswith(prefix):
        error_msg = "Response must start with FUNCTION_CALL:"
        logger.error(f"Tool execution failed: {error_msg}", exc_info=True)
        raise ValueError(error_msg)

    try:
        # Clean up possible formatting issues in JSON
        json_str = response[len(prefix):].strip()
        # Fix common issues that might be in the JSON
        json_str = json_str.replace("'", '"')
        json_str = json_str.replace("None", "null")
        json_str = json_str.replace("True", "true")
        json_str = json_str.replace("False", "false")
        
        payload = json.loads(json_str)
    except json.JSONDecodeError as e:
        error_msg = f"Malformed JSON in FUNCTION_CALL: {e}"
        logger.error(f"Tool execution failed: {error_msg}", exc_info=True)
        raise ValueError(error_msg)

    # Step 2: Basic field checks
    func_name = payload.get("name")
    args = payload.get("args")
    if not func_name or not isinstance(args, dict):
        error_msg = "FUNCTION_CALL must include 'name' and 'args'."
        logger.error(f"Tool execution failed: {error_msg}", exc_info=True)
        raise ValueError(error_msg)

    # Step 3: Find tool in tools_result
    if func_name not in tools_result:
        error_msg = f"Function '{func_name}' not found in available tools."
        logger.error(f"Tool execution failed for '{func_name}': {error_msg}", exc_info=True)
        raise ValueError(error_msg)
    
    tool = tools_result[func_name]['tool']  # Access the tool from the nested structure

    # Step 4: Extract input schema definition and adapt arguments to match schema
    schema: Dict[str, Any] = tool.inputSchema
    
    # Transform the args to match the expected schema
    if schema and "properties" in schema:
        if "path" in schema.get("required", []) and "input_path" in args:
            # Adapt the argument structure to match what's expected
            return func_name, {"path": {"input_path": args["input_path"]}}
    
    # Default case - pass args as-is
    return func_name, args


def _matches_type(value: Any, expected_type: str) -> bool:
    """Helper function to check if a value matches a JSON schema type."""
    if expected_type is None:
        return True
        
    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "object": dict,
        "boolean": bool,
        "array": list,
    }
    py_type = type_map.get(expected_type)
    if py_type is None:
        return True  # Can't validate unknown types
    return isinstance(value, py_type)
 

async def execute_tool(session: ClientSession, tools: list[any], response: str) -> ToolCallResult:
    """Execute FUNCTION_CALL vie MCP tool session"""
    try:
        tool_name, arguments = parse_function_call(response, tools)
        logger.info(f"Calling tool {tool_name} with arguments: {arguments}")
        
        result = await session.call_tool(tool_name, arguments=arguments)

        if hasattr(result, 'content'):
            if isinstance(result.content, list):
                out = [getattr(item, 'text', str(item)) for item in result]
            else:
                out = getattr(result.content, 'text', str(result.content))
        else:
            out = str(result)
        
        logger.info(f"tool, {tool_name} result: {out}")

        return ToolCallResult(
            tool_name = tool_name,
            arguments=arguments,
            result=out,
            raw_response=result
        )
    except Exception as e:
        logger.error(f"tool, Execution failed for '{response}' {e}", exc_info=True)
        raise