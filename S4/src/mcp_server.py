from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from win32api import GetSystemMetrics
import time
from pywinauto.application import Application
import win32gui
import win32con

mcp = FastMCP("Paint Operator")

@mcp.tool()
async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
    """Draw a rectangle in Paint from (x1,y1) to (x2,y2)"""
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Get primary monitor width to adjust coordinates
        primary_width = GetSystemMetrics(0)
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.2)
        
        # Click on the Rectangle tool using the correct coordinates for secondary screen
        paint_window.click_input(coords=(530, 82 ))
        time.sleep(0.2)
        
        # Get the canvas area
        canvas = paint_window.child_window(class_name='MSPaintView')
        
        # Draw rectangle - coordinates should already be relative to the Paint window
        # No need to add primary_width since we're clicking within the Paint window
        canvas.press_mouse_input(coords=(x1+2560, y1))
        canvas.move_mouse_input(coords=(x2+2560, y2))
        canvas.release_mouse_input(coords=(x2+2560, y2))
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error drawing rectangle: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def add_text_in_paint(text: str) -> dict:
    """Add text in Paint"""
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [
                    TextContent(
                        type="text",
                        text="Paint is not open. Please call open_paint first."
                    )
                ]
            }
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.5)
        
        # Click on the Rectangle tool
        paint_window.click_input(coords=(528, 92))
        time.sleep(0.5)
        
        # Get the canvas area
        canvas = paint_window.child_window(class_name='MSPaintView')
        
        # Select text tool using keyboard shortcuts
        paint_window.type_keys('t')
        time.sleep(0.5)
        paint_window.type_keys('x')
        time.sleep(0.5)
        
        # Click where to start typing
        canvas.click_input(coords=(810, 533))
        time.sleep(0.5)
        
        # Type the text passed from client
        paint_window.type_keys(text)
        time.sleep(0.5)
        
        # Click to exit text mode
        canvas.click_input(coords=(1050, 800))
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Text:'{text}' added successfully"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def open_paint() -> dict:
    """Open Microsoft Paint maximized on secondary monitor"""
    global paint_app
    try:
        paint_app = Application().start('mspaint.exe')
        time.sleep(0.2)
        
        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Get primary monitor width
        primary_width = GetSystemMetrics(0)
        
        # First move to secondary monitor without specifying size
        win32gui.SetWindowPos(
            paint_window.handle,
            win32con.HWND_TOP,
            primary_width + 1, 0,  # Position it on secondary monitor
            0, 0,  # Let Windows handle the size
            win32con.SWP_NOSIZE  # Don't change the size
        )
        
        # Now maximize the window
        win32gui.ShowWindow(paint_window.handle, win32con.SW_MAXIMIZE)
        time.sleep(0.2)
        
        return {
            "content": [
                TextContent(
                    type="text",
                    text="Paint opened successfully on secondary monitor and maximized"
                )
            ]
        }
    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error opening Paint: {str(e)}"
                )
            ]
        }

if __name__=="__main__":
    print("Starting paint server: ")
    mcp.run()