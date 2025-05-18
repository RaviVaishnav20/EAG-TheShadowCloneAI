from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from pathlib import Path
import sys
import subprocess
import sqlite3

ROOT = Path(__file__).parent.parent.resolve()  # This gets /Users/ravi/EAG-TheShadowCloneAI/S8

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.server.programming_server.schema.programming_model import *

mcp = FastMCP("Programming")



def run_python_sandbox(input: PythonCodeInput) -> PythonCodeOutput:
    """Run math code in Python sandbox. Usage: run_python_sandbox|input={"code": "result = math.sqrt(49)"}"""
    import sys, io
    import math

    allowed_globals = {
        "__builtins__": __builtins__  # Allow imports like in executor.py
    }

    local_vars = {}

    # Capture print output
    stdout_backup = sys.stdout
    output_buffer = io.StringIO()
    sys.stdout = output_buffer

    try:
        exec(input.code, allowed_globals, local_vars)
        sys.stdout = stdout_backup
        result = local_vars.get("result", output_buffer.getvalue().strip() or "Executed.")
        return PythonCodeOutput(result=str(result))
    except Exception as e:
        sys.stdout = stdout_backup
        return PythonCodeOutput(result=f"ERROR: {e}")



@mcp.tool()
def run_shell_command(input: ShellCommandInput) -> PythonCodeOutput:
    """Run a safe shell command. Usage: run_shell_command|input={"command": "ls"}"""
    allowed_commands = ["ls", "cat", "pwd", "df", "whoami"]

    tokens = input.command.strip().split()
    if tokens[0] not in allowed_commands:
        return PythonCodeOutput(result="Command not allowed.")

    try:
        result = subprocess.run(
            input.command, shell=True,
            capture_output=True, timeout=3
        )
        output = result.stdout.decode() or result.stderr.decode()
        return PythonCodeOutput(result=output.strip())
    except Exception as e:
        return PythonCodeOutput(result=f"ERROR: {e}")


@mcp.tool()
def run_sql_query(input: PythonCodeInput) -> PythonCodeOutput:
    """Run safe SELECT-only SQL query. Usage: run_sql_query|input={"code": "SELECT * FROM users LIMIT 5"}"""
    if not input.code.strip().lower().startswith("select"):
        return PythonCodeOutput(result="Only SELECT queries allowed.")

    try:
        conn = sqlite3.connect("example.db")
        cursor = conn.cursor()
        cursor.execute(input.code)
        rows = cursor.fetchall()
        result = "\n".join(str(row) for row in rows)
        return PythonCodeOutput(result=result or "No results.")
    except Exception as e:
        return PythonCodeOutput(result=f"ERROR: {e}")


# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]