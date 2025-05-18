#/src/core/agent.py

import asyncio
import yaml
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]#Path(__file__).parent.parent.resolve()  # This gets /Users/ravi/EAG-TheShadowCloneAI/S8

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.core.agent.common.session import MultiMCP
from src.core.agent.common.loop import AgentLoop
from src.common.logger.logger import get_logger
logger = get_logger()

async def main(user_input: str, session_id: str):
    print("🧠 Cortex-R Agent Ready")
    # user_input = input("🧑 What do you want to solve today? → ")

    #Load MCP server configs from profiles.yaml
    with open("src/common/config/profiles.yaml", "r") as f:
        profile = yaml.safe_load(f)
        mcp_servers = profile.get("mcp_servers", [])

    multi_mcp = MultiMCP(server_config=mcp_servers)
    print("Agent before initialize")
    await multi_mcp.initialize()
    # print(multi_mcp.tool_map)

    agent = AgentLoop(
        user_input=user_input,
        dispatcher=multi_mcp  # now uses dynamic MultiMCP
    )
    try:
        final_response = await agent.run()
        print("\n💡 Final Answer:\n", final_response.replace("FINAL_ANSWER:", "").strip())
        return final_response

    except Exception as e:
        logger.error(f"fatal,Agent failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
