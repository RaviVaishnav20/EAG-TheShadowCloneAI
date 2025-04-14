import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError
from functools import partial

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

max_iterations = 3
last_response = None
iteration = 0
iteration_response = []

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



async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
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
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

async def main():
    reset_state()  # Reset at the start of main
    print("Starting main execution...")
    try:
        # Create a single MCP server connection
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=[r"C:\Users\raviv\Documents\gitRepos\EAG-TheShadowCloneAI\S5\assignment_completed\example3.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt with available tools
                print("Creating system prompt...")
                print(f"Number of tools: {len(tools)}")
                
                try:
                    # First, let's inspect what a tool object looks like
                    # if tools:
                    #     print(f"First tool properties: {dir(tools[0])}")
                    #     print(f"First tool example: {tools[0]}")
                    
                    tools_description = []
                    for i, tool in enumerate(tools):
                        try:
                            # Get tool properties
                            params = tool.inputSchema
                            desc = getattr(tool, 'description', 'No description available')
                            name = getattr(tool, 'name', f'tool_{i}')
                            
                            # Format the input schema in a more readable way
                            if 'properties' in params:
                                param_details = []
                                for param_name, param_info in params['properties'].items():
                                    param_type = param_info.get('type', 'unknown')
                                    param_details.append(f"{param_name}: {param_type}")
                                params_str = ', '.join(param_details)
                            else:
                                params_str = 'no parameters'

                            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                            tools_description.append(tool_desc)
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")
                    
                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                print("Created system prompt...")
                
                # In talk2mcp.py, modify the system prompt:

                system_prompt = f"""You are a tool-using agent capable of performing both computational tasks and visual editing actions.

your task flow should follow these three-part reasoning and execution structure.

1. THINK: Before issuing any action, analyze the task.
   - Identify what kind of reasoning is required (e.g. arithmetic, spatial, logical)
   - Clearly articulate your reasoning in a single line beginning with THINK:.
   - Example: THINK: This is a spatial task requiring a rectangle and label.

2. VERIFY: Perform internal self-checks.
   - Ensure function parameters (e.g., coordinates, dimensions) are valid.
   - Validate logical order (e.g., initialization or opening paint before drawing)
   - Output a single line beginning with VERIFY:, VERIFY: Coordinates within bounds and correct sequence.

3. ACT: Respond with EXACTLY ONE action line, formatted as:
   - Respond with exactly one action in the following formats:  
   - For computational tasks:  
     - FUNCTION_CALL: {{"name": "function_name", "args": {{"param1": value, "param2": value}}}}  
     - FINAL_ANSWER: [result] 
   - For visual tasks:  
     - Initialize first: FUNCTION_CALL: {{"name": "open_editor", "args": {{}}}}  
     - Then perform actions (e.g., FUNCTION_CALL: {{"name": "draw_rectangle", "args": {{"x1": 100, "y1": 200, "x2": 300, "y2": 400}}}}).  
     - Optionally add text: FUNCTION_CALL: {{"name": "add_text", "args": {{"text": "Label", "x": 150, "y": 250}}}}.  

Available Tools  
  
{tools_description} 

Rules & Constraints  
✅ Strict Formatting:  
   - Only FUNCTION_CALL:, or FINAL_ANSWER: lines.  
   - One action per response (unless pre-validated with THINK/VERIFY). 
   - Last action response should be FINAL_ANSWER

✅ Visual Workflow:  
   - Always initialize (e.g., open_editor) before drawing.  
   - Use appropriate coordinate values (e.g., x between 100–900 and y between 300-700) and position text **inside shapes**


✅ Error Handling:  
   - If uncertain: THINK: I need clarification on [task].  
   - If invalid: FINAL_ANSWER: [error: invalid parameters].
   """



# Change the query to:
                # query = """Open Microsoft Paint, draw a rectangle, and add the text "AI Agent Demo" inside the rectangle."""
                # query = """fibonacci of 20"""
                # query = """What are the roots of the equation x squared minus 5x plus 6 equals zero?"""
                # query = """Find the area under the curve of e to the power of negative x squared between x equals 0 and 1.""" 
                # query = """Solve the differential equation dy/dx equals negative x times y with initial condition y(0)=1, from x=0 to x=2.""" 
                # query = """Multiply these two matrices for me: [[1,2],[3,4]] and [[5,6],[7,8]]."""
                query = """Find where the function x cubed minus x minus 2 crosses zero, starting with an initial guess of 1."""
                print("Starting iteration loop...")
                
                # Use global iteration variables
                global iteration, last_response
                
                while iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    if last_response is None:
                        current_query = query
                    else:
                        current_query = current_query + "\n\n" + " ".join(iteration_response)
                        current_query = current_query + "  What should I do next?"

                    # Get model's response with timeout
                    print("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    try:
                        response = await generate_with_timeout(client, prompt)
                        response_text = response.text.strip()
                        print(f"LLM Response: {response_text}")
                        
                        # Find the FUNCTION_CALL line in the response
                        
                        
                        for line in response_text.split('\n'):
                            line = line.strip()
                            if line.startswith("FUNCTION_CALL:"):
                                response_text = line
                                break
                        
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        break


                    if response_text.startswith("FUNCTION_CALL:"):
                        # _, function_info = response_text.split(":", 1)
                        # parts = [p.strip() for p in function_info.split("|")]
                        # func_name, params = parts[0], parts[1:]
                        function_info = extract_function_call(response_text)
                        print(function_info)
                        func_name = function_info['name']
                        params = list(function_info['args'].values())
                        print(f"\nDEBUG: Raw function info: {function_info}")
                        # print(f"DEBUG: Split parts: {parts}")
                        print(f"DEBUG: Function name: {func_name}")
                        print(f"DEBUG: Raw parameters: {params}")
                        
                        try:
                            # Find the matching tool to get its input schema
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                print(f"DEBUG: Available tools: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            print(f"DEBUG: Found tool: {tool.name}")
                            print(f"DEBUG: Tool schema: {tool.inputSchema}")

                            # Prepare arguments according to the tool's input schema
                            arguments = {}
                            schema_properties = tool.inputSchema.get('properties', {})
                            print(f"DEBUG: Schema properties: {schema_properties}")

                            for param_name, param_info in schema_properties.items():
                                if not params:  # Check if we have enough parameters
                                    raise ValueError(f"Not enough parameters provided for {func_name}")
                                    
                                value = params.pop(0)  # Get and remove the first parameter
                                param_type = param_info.get('type', 'string')
                                
                                print(f"DEBUG: Converting parameter {param_name} with value {value} to type {param_type}")
                                
                                # Convert the value to the correct type based on the schema
                                if param_type == 'integer':
                                    arguments[param_name] = int(value)
                                elif param_type == 'number':
                                    arguments[param_name] = float(value)
                                elif param_type == 'array':
                                    arguments[param_name] = list(value)
                                    # Handle array input
                                    # if isinstance(value, str):
                                    #     value = value.strip('[]').split(',')
                                    # arguments[param_name] = [int(x.strip()) for x in value]
                                else:
                                    arguments[param_name] = str(value)

                            print(f"DEBUG: Final arguments: {arguments}")
                            print(f"DEBUG: Calling tool {func_name}")
                            
                            result = await session.call_tool(func_name, arguments=arguments)
                            print(f"DEBUG: Raw result: {result}")
                            
                            # Get the full result content
                            if hasattr(result, 'content'):
                                print(f"DEBUG: Result has content attribute")
                                # Handle multiple content items
                                if isinstance(result.content, list):
                                    iteration_result = [
                                        item.text if hasattr(item, 'text') else str(item)
                                        for item in result.content
                                    ]
                                else:
                                    iteration_result = str(result.content)
                            else:
                                print(f"DEBUG: Result has no content attribute")
                                iteration_result = str(result)
                                
                            print(f"DEBUG: Final iteration result: {iteration_result}")
                            
                            # Format the response based on result type
                            if isinstance(iteration_result, list):
                                result_str = f"[{', '.join(iteration_result)}]"
                            else:
                                result_str = str(iteration_result)
                            
                            iteration_response.append(
                                f"In the {iteration + 1} iteration you called {func_name} with {arguments} parameters, "
                                f"and the function returned {result_str}."
                            )
                            last_response = iteration_result

                        except Exception as e:
                            print(f"DEBUG: Error details: {str(e)}")
                            print(f"DEBUG: Error type: {type(e)}")
                            import traceback
                            traceback.print_exc()
                            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                            break

                    elif response_text.startswith("FINAL_ANSWER:"):
                        print("\n=== Agent Execution Complete ===")
                        
                        print(result.content[0].text)
                        break

                    iteration += 1

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())
    
    
