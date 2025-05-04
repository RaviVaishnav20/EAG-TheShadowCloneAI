import asyncio
import time 
import os
import datetime
from perception import extract_perception
from get_tools_description import get_description
from memory import MemoryManager, MemoryItem
from decision import generate_plan
from action import execute_tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from logger import get_logger

logger = get_logger()
max_steps = 5  # Increased to 3 for more flexibility but still limited

async def main(user_input: str, session_id: str):
    try:
        logger.info("[agent] Starting agent...")
        logger.info(f"[agent] Current working directory: {os.getcwd()}")

        servr_params = StdioServerParameters(
            command="python",
            args=[r"C:\Users\raviv\Documents\gitRepos\EAG-TheShadowCloneAI\S7\example3.py"]
        )

        try:
            async with stdio_client(servr_params) as (read, write):
                logger.info("Connection established, creating session...")
                try:
                    async with ClientSession(read, write) as session:
                        logger.info(f"[agent] Session created, initializing...")

                        try:
                            await session.initialize()
                            logger.info(f"[agent] MCP session initialized")

                            tools = await session.list_tools()
                            logger.info(f"Available tools: {[t.name for t in tools.tools]}")

                            logger.info("Generating tools description ...")
                            tools_result = tools.tools
                            tools_description = get_description(tools_result)
                            logger.info(f"[agent] {len(tools_result)} tools loaded")

                            # Initialize memory with external vector database
                            # You can configure these parameters based on your setup
                            memory = MemoryManager()
                            
                            session_id = session_id #f"session-{int(time.time())}"
                            original_query = user_input
                            query = user_input
                            step = 0
                            
                            # Store user query in memory
                            memory.add(MemoryItem(
                                text=user_input,
                                type="query",
                                timestamp=datetime.datetime.now().isoformat(),
                                user_query=user_input,
                                session_id=session_id,
                                tags=["user_query", "initial"]
                            ))
                            
                            # Track previous results and tool calls to prevent loops
                            previous_result = None
                            previous_tool_calls = set()
                            final_answer = None

                            while step < max_steps:
                                logger.info(f"loop, Step {step+1} started")

                                perception = await extract_perception(f"query: {query}\n\n available tools: {tools_description}")
                                logger.info(f"perception, Intent: {perception.intent}, Tool hint: {perception.tool_hint}")

                                # Store agent's perception in memory
                                memory.add(MemoryItem(
                                    text=f"Intent: {perception.intent}, Tool hint: {perception.tool_hint}",
                                    type="system",
                                    timestamp=datetime.datetime.now().isoformat(),
                                    session_id=session_id,
                                    tags=["perception", f"step-{step+1}"]
                                ))
                                
                                # Retrieve relevant memories from the vector database
                                retrieved = memory.retrieve(
                                    query=user_input, 
                                    top_k=2,  # Increased for better context 
                                    session_filter=session_id
                                )
                                logger.info(f"memory, Retrieved {len(retrieved)} relevant memories")

                                plan = await generate_plan(
                                    perception, 
                                    retrieved, 
                                    tool_description=tools_description,
                                    previous_result=previous_result,
                                    step_count=step+1
                                )
                                logger.info(f"plan, Plan generated: {plan}")
                                
                                # Store plan in memory
                                memory.add(MemoryItem(
                                    text=f"Plan: {plan}",
                                    type="system",
                                    timestamp=datetime.datetime.now().isoformat(),
                                    session_id=session_id,
                                    tags=["plan", f"step-{step+1}"]
                                ))

                                if plan.startswith("FINAL_ANSWER:"):
                                    # Store final answer in memory
                                    memory.add(MemoryItem(
                                        text=plan,
                                        type="system",
                                        timestamp=datetime.datetime.now().isoformat(),
                                        session_id=session_id,
                                        tags=["final_answer"]
                                    ))
                                    final_answer = plan  # Store the final answer
                                    logger.info(f"[agent], FINAL RESULT: {final_answer}")
                                    break 

                                if "FINAL_ANSWER:" in plan:
                                    # Store final answer in memory
                                    memory.add(MemoryItem(
                                        text=plan,
                                        type="system",
                                        timestamp=datetime.datetime.now().isoformat(),
                                        session_id=session_id,
                                        tags=["final_answer"]
                                    ))
                                    final_answer = plan  # Store the final answer
                                    logger.info(f"[agent], FINAL RESULT: {final_answer}")
                                    break    
                                
                                # Check if we're repeating the exact same tool call
                                if plan in previous_tool_calls:
                                    logger.warning(f"Detected repeating tool call: {plan}")
                                    # Force a final answer after detecting a loop
                                    final_answer = f"FINAL_ANSWER: Based on my analysis, " + \
                                                  f"I found that {perception.intent}. " + \
                                                  f"The available information suggests: {previous_result or 'No definitive answer found'}"
                                    
                                    # Store loop detection and final answer in memory
                                    memory.add(MemoryItem(
                                        text=f"Loop detected with plan: {plan}. Forcing final answer.",
                                        type="system",
                                        timestamp=datetime.datetime.now().isoformat(),
                                        session_id=session_id,
                                        tags=["loop_detection", f"step-{step+1}"]
                                    ))
                                    
                                    memory.add(MemoryItem(
                                        text=final_answer,
                                        type="system",
                                        timestamp=datetime.datetime.now().isoformat(),
                                        session_id=session_id,
                                        tags=["final_answer", "loop_forced"]
                                    ))
                                    
                                    logger.info(f"[agent], FINAL RESULT (after loop detection): {final_answer}")
                                    break
                                
                                # Add current plan to previous tool calls
                                previous_tool_calls.add(plan)
                                
                                try:
                                    result = await execute_tool(session, tools_result, plan)
                                    logger.info(f"tool, {result.tool_name} returned: {result.result}")
                                    
                                    # Store tool result in memory
                                    memory.add(MemoryItem(
                                        text=str(result.result),
                                        type="tool_output",
                                        timestamp=datetime.datetime.now().isoformat(),
                                        tool_name=result.tool_name,
                                        user_query=original_query,
                                        session_id=session_id,
                                        tags=["tool_result", f"step-{step+1}", result.tool_name]
                                    ))
                                    
                                    # Store this result for the next round
                                    previous_result = str(result.result)

                                    # Generate next query that includes the original task, 
                                    # tool result, and explicit instruction to either 
                                    # provide a final answer or try a different approach
                                    query = f"Original task: {original_query}\n" + \
                                           f"Previous steps: Step {step+1} used tool {result.tool_name} and got result: {result.result}\n" + \
                                           f"What should I do next? Consider carefully if you now have enough information to provide a final answer."
                                   
                                except Exception as e:
                                    error_msg = f"Tool execution failed: {e}"
                                    logger.error(error_msg)
                                    
                                    # Store error in memory
                                    memory.add(MemoryItem(
                                        text=error_msg,
                                        type="system",
                                        timestamp=datetime.datetime.now().isoformat(),
                                        session_id=session_id,
                                        tags=["error", f"step-{step+1}"]
                                    ))
                                    
                                    final_answer = "FINAL_ANSWER: I encountered an error while trying to solve this problem."
                                    
                                    memory.add(MemoryItem(
                                        text=final_answer,
                                        type="system",
                                        timestamp=datetime.datetime.now().isoformat(),
                                        session_id=session_id,
                                        tags=["final_answer", "error_forced"]
                                    ))
                                    
                                    logger.info(f"[agent], FINAL RESULT (after error): {final_answer}")
                                    break
                                
                                step += 1

                            # Return the final answer if we have one
                            logger.info(f"[agent], Agent session complete")
                            return final_answer

                        except Exception as e:
                            logger.error(f"[agent] Session initialization error: {str(e)}", exc_info=True)
                            return "FINAL_ANSWER: I encountered an error while initializing the session."
                except Exception as e:
                        logger.error(f"[agent] Session creation error: {str(e)}", exc_info=True)
                        return "FINAL_ANSWER: I encountered an error while creating the session."
        except Exception as e:
                logger.error(f"[agent] Connection error: {str(e)}", exc_info=True)
                return "FINAL_ANSWER: I encountered a connection error."
    except Exception as e:
            logger.error(f"[agent] Overall error: {str(e)}", exc_info=True)
            return "FINAL_ANSWER: I encountered an unexpected error."
    
    # Return a default final answer if we somehow get here
    return "FINAL_ANSWER: No response could be generated."

if __name__ == "__main__":
     query = input(" What do you want to solve today? ->")
     result = asyncio.run(main(query))
     print(f"Result: {result}")
