import asyncio
import time
import os
from typing import Dict, Any, List, Optional
import json
from pathlib import Path

from singleton import Singleton
from memory import MemoryManager, MemoryItem
from perception import extract_perception
from decision import generate_plan
from action import execute_tool
from get_tools_description import get_description
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from logger import get_logger

logger = get_logger()

@Singleton
class AgentEngine:
    """
    Singleton class that wraps the agent functionality.
    """
    def __init__(self):
        self.memory_manager = MemoryManager()
        self.tools_result = None
        self.tools_description = None
        self._initialized = False
        self.max_steps = 3
    
    async def initialize(self):
        """Initialize the agent engine if not already initialized."""
        if self._initialized:
            logger.info("Agent engine already initialized")
            return
        
        try:
            logger.info("[agent] Initializing agent engine...")
            
            server_params = StdioServerParameters(
                command="python",
                args=["example3.py"],
                cwd=str(Path.cwd())  # Use current working directory
            )
            
            # Initialize MCP and get tools
            async with stdio_client(server_params) as (read, write):
                logger.info("Connection established, creating session...")
                async with ClientSession(read, write) as session:
                    logger.info(f"[agent] Session created, initializing...")
                    await session.initialize()
                    logger.info(f"[agent] MCP session initialized")
                    
                    tools = await session.list_tools()
                    logger.info(f"Available tools: {[t.name for t in tools.tools]}")
                    
                    self.tools_result = tools.tools
                    self.tools_description = get_description(self.tools_result)
                    logger.info(f"[agent] {len(self.tools_result)} tools loaded")
            
            self._initialized = True
            logger.info("[agent] Agent engine initialized successfully")
        
        except Exception as e:
            logger.error(f"[agent] Initialization error: {str(e)}", exc_info=True)
            raise
    
    async def process_query(self, user_input: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a user query and return structured results."""
        if not self._initialized:
            await self.initialize()
        
        # Generate a session ID if not provided
        if not session_id:
            session_id = f"session-{int(time.time())}"
        
        query = user_input
        step = 0
        steps_data = []
        final_result = ""
        
        try:
            server_params = StdioServerParameters(
                command="python",
                args=["example3.py"],
                cwd=str(Path.cwd())  # Use current working directory
            )
            
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    if not self.tools_result:
                        tools = await session.list_tools()
                        self.tools_result = tools.tools
                        self.tools_description = get_description(self.tools_result)
                    
                    while step < self.max_steps:
                        step_data = {"step": step + 1}
                        logger.info(f"loop, Step {step+1} started")
                        
                        # Perception
                        perception = extract_perception(user_input)
                        logger.info(f"perception, Intent: {perception.intent}, Tool hint: {perception.tool_hint}")
                        step_data["perception"] = perception.dict()
                        
                        # Memory retrieval
                        retrieved = self.memory_manager.retrieve(query=user_input, top_k=3, session_filter=session_id)
                        logger.info(f"memory, Retrieved {len(retrieved)} relevant memories")
                        step_data["retrieved_memories"] = [mem.dict() for mem in retrieved]
                        
                        # Generate plan
                        plan = generate_plan(perception, retrieved, tool_description=self.tools_description)
                        logger.info(f"plan, Plan generated: {plan}")
                        step_data["plan"] = plan
                        
                        # Check if final answer
                        if plan.startswith("FINAL_ANSWER:"):
                            # Clean the final answer by removing the prefix and any debugging info
                            raw_answer = plan.replace("FINAL_ANSWER:", "").strip()
                            # Extract content between square brackets if present
                            if raw_answer.startswith("[") and raw_answer.endswith("]"):
                                final_result = raw_answer[1:-1].strip()  # Remove the brackets
                            else:
                                final_result = raw_answer
                            
                            step_data["result"] = final_result
                            steps_data.append(step_data)
                            break
                        
                        # Execute tool
                        try:
                            result = await execute_tool(session, self.tools_result, plan)
                            logger.info(f"tool, {result.tool_name} returned: {result.result}")
                            step_data["tool_result"] = result.dict()
                            
                            # Add to memory
                            self.memory_manager.add(MemoryItem(
                                text=f"Tool call: {result.tool_name} with {result.arguments}, got: {result.result}",
                                type="tool_output",
                                tool_name=result.tool_name,
                                user_query=user_input,
                                tags=[result.tool_name],
                                session_id=session_id
                            ))
                            
                            user_input = f"Original task: {query}\nPrevious output: {result.result}\nWhat should I do next?"
                        
                        except Exception as e:
                            logger.error(f"Tool execution failed: {e}")
                            step_data["error"] = str(e)
                            steps_data.append(step_data)
                            break
                        
                        steps_data.append(step_data)
                        step += 1
        
        except Exception as e:
            logger.error(f"[agent] Processing error: {str(e)}", exc_info=True)
            return {
                "result": f"Error: {str(e)}",
                "steps": steps_data
            }
        
        logger.info(f"[agent], Agent session complete with result: {final_result}")
        return {
            "result": final_result,
            "steps": steps_data
        }

# Create a wrapper function for compatibility with existing code
async def process_query(user_input: str) -> Dict[str, Any]:
    """Process a query using the agent engine singleton."""
    agent_engine = AgentEngine()
    await agent_engine.initialize()
    return await agent_engine.process_query(user_input)

# Keep the original main function for backwards compatibility
async def main(user_input: str) -> str:
    """Original main function, now using the singleton agent engine."""
    result = await process_query(user_input)
    return result.get("result", "No result available")