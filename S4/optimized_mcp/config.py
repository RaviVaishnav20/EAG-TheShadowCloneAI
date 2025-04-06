import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MCP_SERVER_PATH = os.getenv("MCP_SERVER_PATH", "python server/paint_server.py")
    MAX_ITERATIONS = 3
    LLM_TIMEOUT = 8
    TOOL_TIMEOUT = 5