from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from paint_manager import PaintManager

mcp = FastMCP("Optimized Paint Server")
paint = PaintManager()

@mcp.tool()
async def open_paint():
    paint.initialize()
    return {"content": [TextContent(text="Paint ready")]}

@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int):
    paint.execute_sequence([
        ('click', paint.TOOL_COORDINATES['rectangle']),
        ('press', (x1, y1)),
        ('move', (x2, y2)),
        ('release', (x2, y2))
    ])
    return {"content": [TextContent(text=f"Rectangle drawn")]}

@mcp.tool()
async def add_text_in_paint(text: str):
    paint.execute_sequence([
        ('click', paint.TOOL_COORDINATES['text']),
        ('type', 't'),
        ('type', 'x'),
        ('click', paint.TOOL_COORDINATES['canvas_click']),
        ('type', text),
        ('click', paint.TOOL_COORDINATES['canvas_exit'])
    ])
    return {"content": [TextContent(text=f"Text added")]}

if __name__ == "__main__":
    print("Server started")
    mcp.run()