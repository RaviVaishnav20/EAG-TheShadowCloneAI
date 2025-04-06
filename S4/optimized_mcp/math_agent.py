import asyncio
from llm_utils import LLMClient
from mcp_utils import pool, call_tool_with_retry
from config import Config

class MathAgent:
    SYSTEM_PROMPT = """You are a math agent solving problems in iterations. You have access to various mathematical tools.

Available tools:
{tools_description}

You must respond with EXACTLY ONE line in one of these formats (no additional text):
1. For function calls:
   FUNCTION_CALL: function_name|param1|param2|...
   
2. For final answers:
   FINAL_ANSWER: [number]

Important:
- When a function returns multiple values, you need to process all of them
- Only give FINAL_ANSWER when you have completed all necessary calculations
- Do not repeat function calls with the same parameters"""

    def __init__(self):
        self.llm = LLMClient()
        self.reset_state()
        
    def reset_state(self):
        self.iteration = 0
        self.context = []
        self.last_result = None
        
    async def get_tools(self):
        async with pool.get_session() as session:
            tools_result = await session.list_tools()
            return tools_result.tools
            
    def _build_tools_description(self, tools):
        descriptions = []
        for i, tool in enumerate(tools):
            params = tool.inputSchema.get('properties', {})
            param_desc = ", ".join([f"{name}: {info.get('type', 'any')}" 
                                  for name, info in params.items()])
            descriptions.append(f"{i+1}. {tool.name}({param_desc}) - {tool.description}")
        return "\n".join(descriptions)
        
    async def process_function_call(self, function_call, tools):
        try:
            _, call_info = function_call.split(":", 1)
            parts = [p.strip() for p in call_info.split("|")]
            func_name = parts[0]
            params = parts[1:]
            
            tool = next((t for t in tools if t.name == func_name), None)
            if not tool:
                raise ValueError(f"Unknown tool: {func_name}")
                
            arguments = {}
            schema = tool.inputSchema.get('properties', {})
            
            for param_name in schema:
                if not params:
                    raise ValueError("Not enough parameters")
                value = params.pop(0)
                param_type = schema[param_name].get('type', 'string')
                
                if param_type == 'integer':
                    arguments[param_name] = int(value)
                elif param_type == 'number':
                    arguments[param_name] = float(value)
                else:
                    arguments[param_name] = value
            
            result = await call_tool_with_retry(func_name, arguments)
            self.last_result = result
            return result
            
        except Exception as e:
            self.last_result = f"Error: {str(e)}"
            raise
            
    async def _handle_final_answer(self, answer):
        print(f"\nFinal Answer: {answer}")
        try:
            await call_tool_with_retry("open_paint", {})
            await asyncio.sleep(0.5)
            await call_tool_with_retry("add_text_in_paint", {"text": answer})
        except Exception as e:
            print(f"Error displaying answer: {e}")

    async def run(self, query):
        self.reset_state()
        tools = await self.get_tools()
        tools_desc = self._build_tools_description(tools)
        
        full_prompt = f"{self.SYSTEM_PROMPT.format(tools_description=tools_desc)}\n\nQuery: {query}"
        
        while self.iteration < Config.MAX_ITERATIONS:
            try:
                response = await self.llm.generate(full_prompt)
                response_text = response.text.strip()
                
                if response_text.startswith("FUNCTION_CALL:"):
                    result = await self.process_function_call(response_text, tools)
                    self.context.append(f"Iteration {self.iteration + 1} result: {str(result)}")
                    full_prompt += f"\nLast result: {str(result)}"
                    
                elif response_text.startswith("FINAL_ANSWER:"):
                    await self._handle_final_answer(response_text)
                    break
                    
            except Exception as e:
                print(f"Iteration {self.iteration + 1} failed: {str(e)}")
                self.context.append(f"Error: {str(e)}")
                
            self.iteration += 1

async def main():
    agent = MathAgent()
    await agent.run("Find the ASCII values of characters in INDIA and then return sum of exponentials of those values.")

if __name__ == "__main__":
    asyncio.run(main())