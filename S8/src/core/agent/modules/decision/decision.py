from pathlib import Path
import sys
import datetime
ROOT = Path(__file__).resolve().parents[5] # This gets /Users/ravi/EAG-TheShadowCloneAI/S8

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.core.agent.modules.perception.perception import PerceptionResult
from src.core.agent.common.memory_store.memory import MemoryItem
from src.core.agent.common.llm.model_manager import ModelManager
from typing import List, Optional
from src.common.logger.logger import get_logger
logger = get_logger()

model = ModelManager()


async def generate_plan(
    perception: PerceptionResult,
    memory_items: List[MemoryItem],
    tool_descriptions: Optional[str] = None,
    step_num: int = 1,
    max_steps: int = 3
) -> str:
    """Generates the next step plan for the agent: either tool usage or final answer."""

    memory_texts = "\n".join(f"- {m.text}" for m in memory_items) or "None"
    tool_context = f"\nYou have access to the following tools:\n{tool_descriptions}" if tool_descriptions else ""

    prompt = f"""
You are a reasoning-driven AI agent with access to tools. Your job is to solve the user's request step-by-step by reasoning
through the problem, selecting a tool if needed, and continuing until the FINAL_ANSWER is produced. 

Always follow the loop:

1. Think step-by-step about the problem.
2. If a tool is needed, respond using the format:
    FUNCTION_CALL: {{"name": "function name", "args": {{}}}}  
    - Note: Validate the tools input from tools description
3. When the final answer is known, respond using:
    FINAL_ANSWER: [your final result]


🧠 Context:
- Step: {step_num} of {max_steps}

- Tool Context:
{tool_context}

- You can reference these relevant memories:
{memory_texts}

Guidelines:
- Respond using EXACTLY ONE of the formats above per step.
- Do NOT include extra text, explanation, or formatting.
- Use nested keys (e.g., input.string) and square brackets and lists.

Static Case:
- Atleast perform search_documents tool once before using web_search tool

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
        raw = (await model.generate_text(prompt)).strip()
        logger.info(f"plan, LLM output: {raw}")

        for line in raw.splitlines():
            if line.strip().startswith("FUNCTION_CALL:") or line.strip().startswith("FINAL_ANSWER:"):
                return line.strip()

        return "FINAL_ANSWER: [unknown]"

    except Exception as e:
        logger.error(f"plan, ⚠️ Planning failed: {e}", exc_info=True)
        return "FINAL_ANSWER: [unknown]"

