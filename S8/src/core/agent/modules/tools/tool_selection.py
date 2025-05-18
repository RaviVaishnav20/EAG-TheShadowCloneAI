from mcp import ClientSession
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[4] # This gets /Users/ravi/EAG-TheShadowCloneAI/S8

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))
from src.core.agent.tool_selection.get_tools_description import get_description
from src.core.agent.common.llm.llm import CustomLLM, CustomPayload
from src.common.logger.logger import get_logger
logger = get_logger()



def filtered_tools(all_tools, hint_text):
    """
    Extract tool names from the model's response and filter them against available tools.
    
    Args:
        all_tools (list): List of all available tool names
        hint_text (str): The model's response containing tool suggestions
        
    Returns:
        list: List of valid tool names mentioned in the hint
    """
    #clean and normalize the hint text
    clean_hint = hint_text.strip().lower()

    #Extract tool names - handle different possible formats
    tool_hints = []

    # If the response is formatted as JSON or with specific tags
    if "tools:" in clean_hint:
        #Extract from "tools: tool1, tool2, tool3" format
        tool_section = clean_hint.split("tools:")[1].strip()
        tool_hints = [t.strip() for t in tool_section.split(",")]
    elif "suggested tools:" in clean_hint:
        # Extract from "suggested tools: tool1, tool2, tool3" format
        tools_section = clean_hint.split("suggested tools:")[1].strip()
        tool_hints = [t.strip() for t in tools_section.split(",")]
    else:
        # Assume tools are simply listed with commas or linebreaks
        delimeters = [",","\n"]
        for delimeter in delimeters:
            if delimeter in clean_hint:
                tool_hints = [t.strip() for t in clean_hint.split(delimeter)]
                break
        else:
            # If no delimiter found, treat the whole text as one tool
            tool_hints = [clean_hint]
    # clean up any remaining punctuation or formatting
    cleaned_hints = []
    for hint in tool_hints:
        #Remove common punctuation and formatting characters
        for char in ['[',']','"',"'",'`','*','-']:
            hint = hint.replace(char, '')
        # Only add non-empty hints
        if hint.strip():
            cleaned_hints.append(hint.strip())
    # Filter against available tools
    valid_tools = [tool for tool in cleaned_hints if tool in all_tools]

    return valid_tools

async def get_tool_suggestions(session: ClientSession, user_input:str):
    """
    Get tool suggestions for a user query from the LLM.
    
    Args:
        user_input (str): The user's query
        tool_description (str): Description of available tools
        model: The LLM model instance
        
    Returns:
        list: List of suggested tool names
        """
    tools = await session.list_tools()
    logger.info("Generating tools description ...")
    all_tools_with_info = tools.tools
    all_tools = [t.name for t in all_tools_with_info]
    logger.info(f"Available tools: {all_tools}")
    tools_description = get_description(all_tools_with_info)
    logger.info(f"[agent] {len(all_tools_with_info)} tools loaded")
    # print(tools_description)
    prompt = f""" 
                Analyze the following user query and determine the most appropriate tools to help answer it. Return ONLY the tool names in this format:
                TOOLS: tool1, tool2, tool3
                Query: "{user_input}"
                Available tools:
                {tools_description}
                Important guidelines:

                Return ONLY the tool names prefixed with "TOOLS:" and separated by commas
                Do not include explanations or commentary
                Only suggest tools that directly address the query's needs
                For mathematical operations, identify the specific calculation required
                For information retrieval needs, suggest search tools
                For specialized domain questions, match to domain-specific tools
                Limit suggestions to 1-3 most relevant tools unless more are clearly needed
                If no tools are appropriate, respond with "TOOLS: none"

                Example responses:

                TOOLS: add, multiply
                TOOLS: vector_search
                TOOLS: kinetic_energy, power
                TOOLS: none
                """
    custom_payload = CustomPayload(
            prompt=prompt,
    )
    model = CustomLLM()
    hint = await model.invoke(custom_payload)
    hint =hint.strip()   #raw =response.text.strip()
    logger.info(f"Tool hint, LLM output: {hint}")

    tool_hints = filtered_tools(all_tools, hint)
    suggested_tools = [tool for tool in all_tools_with_info if tool.name.lower() in tool_hints]
    if suggested_tools:
        tools_description = get_description(suggested_tools)
    
    return suggested_tools, tool_hints, tools_description