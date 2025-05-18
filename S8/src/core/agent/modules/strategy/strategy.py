# core/strategy.py → Planning Wrapper
# Role: Allows customization of agent strategy: reactive, multi-shot, confidence-based, etc.

# Responsibilities:

# Wraps around decision.generate_plan()

# Adds planning context: past failures, retries, agent profile

# Can implement logic like: “retry with different tool”, “skip if tool fails twice”, etc.

# Dependencies:

# modules/decision.py

# core/context.py (for prior steps)

# config/profiles.yaml (agent behavior/personality traits)

# Inputs: Perception + retrieved memory + prior steps

# Outputs: Structured plan: FUNCTION_CALL or FINAL_ANSWER

# core/strategy.py

from pathlib import Path
import sys
import datetime
ROOT = Path(__file__).resolve().parents[5] # This gets /Users/ravi/EAG-TheShadowCloneAI/S8

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))


from src.core.agent.modules.perception.perception import PerceptionResult
from src.core.agent.modules.decision.decision import generate_plan
from src.core.agent.common.memory_store.memory import MemoryItem
from src.core.agent.modules.tools.tools import summarize_tools, filter_tools_by_hint
from src.core.agent.common.context import AgentContext
from typing import Any

async def decide_next_action(
        context: AgentContext,
        perception: PerceptionResult,
        memory_items: list[Any],
        all_tools: list[Any],
        last_result: str = "",
) -> str:
    """
    Decides what to do next using the planning strategy defined in agent profile.
    Wraps around the `generate_plan()` logic with strategy-aware control.
    """
    strategy = context.agent_profile.strategy
    step = context.step +1
    max_steps = context.agent_profile.max_steps
    tool_hint = perception.tool_hint

    # print("In decision")
    # Step 1: Try hint-based filtered tools first
    filtered_tools = filter_tools_by_hint(all_tools, hint=tool_hint)
    # print(filtered_tools)
    filtered_summary = summarize_tools(filtered_tools)
    # print(filtered_summary)
    plan = await generate_plan(
        perception=perception,
        memory_items=memory_items,
        tool_descriptions=filtered_summary,
        step_num=step,
        max_steps=max_steps
    )
    print(plan)
    # Strategy enforcement
    if strategy == "conservative":
        return plan
    
    if strategy == "retry_once" and "unknown" in plan.lower():
        # Retry with all tools if hint-based filtering failed
        full_summary = summarize_tools(all_tools)
        return generate_plan(
            perception=perception,
            memory_items=memory_items,
            tool_descriptions=full_summary,
            step_num=step,
            max_steps=max_steps,
        )

    # Placeholder for future "explore_all" parallel planner
    return plan



