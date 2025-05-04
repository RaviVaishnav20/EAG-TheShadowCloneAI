from perception import PerceptionResult
from memory import MemoryItem
from typing import List, Optional
from dotenv import load_dotenv
# from google import genai
from llm import CustomLLM, CustomPayload
import os
from logger import get_logger
logger = get_logger()


load_dotenv()

# client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

async def generate_plan(
        perception:PerceptionResult,
        memory_items: List[MemoryItem],
        tool_description: Optional[str] = None,
        previous_result: Optional[str] = None,
        step_count: int = 0
) -> str:
    """Generate a plan (tool call or final answer) using LLM based on structured perception and memory."""
    memory_texts = "\n".join(f"- {m.text}" for m in memory_items) or "None"

    tool_context = f"\n You have access to the following tools: \n{tool_description}" if tool_description else ""
    
    # Add information about previous result if available
    previous_result_context = ""
    if previous_result:
        previous_result_context = f"""
Previous tool output:
```
{previous_result}
```

The above is the result from your previous tool call. You should analyze this output and decide if:
1. You need to call another tool with different parameters
2. You have enough information to provide a FINAL_ANSWER
"""

    # Add step counter to encourage progression
    step_info = f"Current step: {step_count}/3. You must provide FINAL_ANSWER by step 3."

    prompt = f"""
You are a reasoning-driven AI agent with access to tools. Your job is to solve the user's request step-by-step by reasoning
through the problem, selecting a tool if needed, and continuing until the FINAL_ANSWER is produced. {tool_context}

{step_info}

Always follow the loop:

1. Think step-by-step about the problem.
2. If a tool is needed, respond using the format:
    FUNCTION_CALL: {{"name": "function name", "args": {{}}}}  
    - Note: Validate the tools input from tools description
3. When the final answer is known, respond using:
    FINAL_ANSWER: [your final result]

{previous_result_context}

Guidelines:
- Respond using EXACTLY ONE of the formats above per step.
- Do NOT include extra text, explanation, or formatting.
- Use nested keys (e.g., input.string) and square brackets and lists.
- You can reference these relevant memories:
{memory_texts}

Input Summary:
- User input: "{perception.user_input}"
- Intent: {perception.intent}
- Entities: {', '.join(perception.entities)}
- Tool hint: {perception.tool_hint or 'None'}

✅ Examples: 
- User asks: calculate projectile range Velocity=20m/s and angle=45°
- FUNCTION_CALL: {{"name": "horizontal_range", "args": {{"v0": 20, "angle": 45, "g": 9.8}}}}  
- FINAL_ANSWER: The projectile will travel approximately 40.8 meters horizontally.

✅ Examples:
- User asks: "What's the relationship between Cricket and Sachin Tendulkar"
  - FUNCTION_CALL: {{"name": "search_documents", "args": {{"query": "relationship between Cricket and Sachin Tendulkar"}}}}
  - [receives a detailed document]
  - FINAL_ANSWER: Sachin Tendulkar is widely regarded as the "God of Cricket" due to his exceptional skills, longevity, and impact on the sport in India. He is the leading run-scorer in both Test and ODI cricket, and the first to score 100 centuries in international cricket. His influence extends beyond his statistics, as he is seen as a symbol of passion, perseverance, and a national icon.

IMPORTANT:
- 🚫 Do NOT invent tools. Use only the tools listed below.
- 📄 If the question may relate to factual knowledge, use the 'search_documents' tool to look for the answer.
- 🧮 If the question is mathematical or needs calculation, use the appropriate math tool.
- 🤖 NEVER REPEAT THE SAME EXACT TOOL CALL. If you called a tool and got a result, either extract the answer from it or try a different tool/parameters.
- If the previous tool output already contains factual information, DO NOT search again. Instead, summarize the relevant facts and respond with: FINAL_ANSWER: [your answer]
- ❌ Do NOT output unstructured responses.
- 🧠 Think before each step. Verify intermediate results mentally before proceeding.
- 💥 If unsure or no tool fits, skip to FINAL_ANSWER: [unknown]
- ✅ You have only 3 attempts. Final attempt must be FINAL_ANSWER
"""
    
    try:
        # response = client.models.generate_content(
        #     model="gemini-2.0-flash",
        #     contents=prompt
        # )
        custom_payload = CustomPayload(
            prompt=prompt,
        )
        model = CustomLLM()
        response = await model.invoke(custom_payload)
        raw = response.strip()   #raw = response.text.strip()
        logger.info(f"plan, LLM output: {raw}")

        for line in raw.splitlines():
            if line.strip().startswith("FUNCTION_CALL:") or line.strip().startswith("FINAL_ANSWER:"):
                return line.strip()
        return raw.strip()
    
    except Exception as e:
        logger.error(f"plan, Decision generation failed: {e}", exc_info=True)
        return "FINAL_ANSWER: [unknown]"