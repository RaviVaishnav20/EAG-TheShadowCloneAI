from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from models import GetSTMemoryInput, UpdateSTMemoryInput, DECISION_INPUT, PerceptionInput
from utils import extract_function_call
import asyncio
from tool_prompt import get_tools_prompt
from universal_system_prompt import get_system_prompt
from memory import reset_short_term_memory, get_short_term_memory, update_short_term_memory, get_last_response
from decision_making import get_decision
from logger import get_logger
from perception import extract_perception
#Get the logger instance
logger = get_logger()

max_iterations = 5
# last_response = None
iteration = 0
iteration_response = []
user_id = "ravi123"



async def main():
    reset_short_term_memory()  # Reset at the start of main
    logger.info("Starting main execution...")
    try:
    # Create a single MCP server connection
        logger.info("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=[r"C:\Users\raviv\Documents\gitRepos\EAG-TheShadowCloneAI\S6\action.py"]
        )

        async with stdio_client(server_params) as (read, write):
            logger.info("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                logger.info("Session created, initializing...")
                await session.initialize()
                logger.info("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                logger.info(f"Successfully retrieved {len(tools)} tools")
                
                logger.info("Started creating tools discription prompt...")
                tools_description = get_tools_prompt(tools)
                logger.info("Created tools discription prompt...")
                
                # query = """Open Microsoft Paint, draw a rectangle, and add the text "AI Agent Demo" above the rectangle."""
                query = """A 1200 kg car braking at -8 m/s² for 3 seconds before hitting a barrier. What was its initial kinetic energy and how far did it travel during braking?"""
                query = await extract_perception(PerceptionInput(query=query))
                logger.info("Starting iteration loop...")

                global iteration     
                while iteration < max_iterations:
                    logger.info(f"\n--- Iteration {iteration + 1} ---")
        
                    chat_history = get_short_term_memory(GetSTMemoryInput(key=user_id))
                    last_response = get_last_response(GetSTMemoryInput(key=user_id))
                    
                    query =  query + "\n\n" + "last operation was:"+"\n\n" + last_response
                    input_decision = DECISION_INPUT(
                        query=query, 
                        chat_history=chat_history, 
                        tools_description=tools_description 
                    )
                    response_text = await get_decision(input_decision)

                    for line in response_text.split('\n'):
                        line = line.strip()
                        if line.startswith("FUNCTION_CALL:"):
                            response_text = line
                            break
                        elif line.startswith("FINAL_ANSWER:"):
                            logger.info("\n=== Agent Execution Complete ===")
                            logger.info(f"Final answer: {line.split('FINAL_ANSWER:')[1].strip()}")
                            # Exit the loop
                            iteration = max_iterations  # Force loop to end
                            break
                        
                    if response_text.startswith("FUNCTION_CALL:"):
                        # _, function_info = response_text.split(":", 1)
                        # parts = [p.strip() for p in function_info.split("|")]
                        # func_name, params = parts[0], parts[1:]
                        function_info = extract_function_call(response_text)
                        logger.debug(f"Extrected function info: {function_info}")
                        func_name = function_info['name']
                        params = list(function_info['args'].values())
                        logger.debug(f"Function name: {func_name}")
                        logger.debug(f"Raw parameters: {params}")
                        
                        try:
                            # Find the matching tool to get its input schema
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                logger.error(f"Unknown tool: {func_name}")
                                logger.debug(f"Available tools: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            logger.debug(f"Found tool: {tool.name}")
                            logger.debug(f"Tool schema: {tool.inputSchema}")

                            # Prepare arguments according to the tool's input schema
                            arguments = {}
                            schema_properties = tool.inputSchema.get('properties', {})
                            logger.debug(f"Schema properties: {schema_properties}")

                            for param_name, param_info in schema_properties.items():
                                if not params:  # Check if we have enough parameters
                                    logger.error(f"Not enough parameters provided for {func_name}")
                                    raise ValueError(f"Not enough parameters provided for {func_name}")
                                    
                                value = params.pop(0)  # Get and remove the first parameter
                                param_type = param_info.get('type', 'string')
                                
                                logger.debug(f"Converting parameter {param_name} with value {value} to type {param_type}")
                                
                                # Convert the value to the correct type based on the schema
                                if param_type == 'integer':
                                    arguments[param_name] = int(value)
                                elif param_type == 'number':
                                    arguments[param_name] = float(value)
                                elif param_type == 'array':
                                    arguments[param_name] = list(value)
                                else:
                                    arguments[param_name] = str(value)

                            logger.debug(f"Final arguments: {arguments}")
                            logger.info(f"Calling tool {func_name}")
                            
                            result = await session.call_tool(func_name, arguments=arguments)
                            logger.info(f"Raw result: {result}")
                            
                            # Get the full result content
                            if hasattr(result, 'content'):
                                logger.debug(f"Result has content attribute")
                                # Handle multiple content items
                                if isinstance(result.content, list):
                                    iteration_result = [
                                        item.text if hasattr(item, 'text') else str(item)
                                        for item in result.content
                                    ]
                                else:
                                    iteration_result = str(result.content)
                            else:
                                logger.debug(f"Result has no content attribute")
                                iteration_result = str(result)
                                
                            logger.debug(f"Final iteration result: {iteration_result}")
                            
                            # Format the response based on result type
                            if isinstance(iteration_result, list):
                                result_str = f"[{', '.join(iteration_result)}]"
                            else:
                                result_str = str(iteration_result)
                            
                            update_result =(
                                f"In the {iteration + 1} iteration you called {func_name} with {arguments} parameters, "
                                f"and the function returned {result_str}."
                            )
                            
                            update_short_term_memory(UpdateSTMemoryInput(key=user_id, value=update_result))

                        except Exception as e:
                            logger.error(f"Error in iteration {iteration + 1}: {str(e)}", exc_info=True)
                            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                            break

                    elif response_text.startswith("FINAL_ANSWER"):
                        logger.info("\n=== Agent Execution Complete ===")
                        
                        print(result.content[0].text)
                        break

                    iteration += 1

    except Exception as e:
        logger.error(f"Error in main execution: {e}", exc_info=True)
    finally:
        logger.info("Cleaning up and resetting memory")
        reset_short_term_memory()  # Reset at the end of main

        
    
if __name__ == "__main__":
    asyncio.run(main())
