# # basic import 
# from mcp.server.fastmcp import FastMCP, Image
# from mcp.server.fastmcp.prompts import base
# from mcp.types import TextContent
# from mcp import types
# from PIL import Image as PILImage
# import math
# import sys
# from pywinauto.application import Application
# import win32gui
# import win32con
# import time
# from win32api import GetSystemMetrics

# # instantiate an MCP server client
# mcp = FastMCP("Calculator")

# # DEFINE TOOLS

# #addition tool
# @mcp.tool()
# def add(a: int, b: int) -> int:
#     """Add two numbers"""
#     print("CALLED: add(a: int, b: int) -> int:")
#     return int(a + b)

# @mcp.tool()
# def add_list(l: list) -> int:
#     """Add all numbers in a list"""
#     print("CALLED: add(l: list) -> int:")
#     return sum(l)

# # subtraction tool
# @mcp.tool()
# def subtract(a: int, b: int) -> int:
#     """Subtract two numbers"""
#     print("CALLED: subtract(a: int, b: int) -> int:")
#     return int(a - b)

# # multiplication tool
# @mcp.tool()
# def multiply(a: int, b: int) -> int:
#     """Multiply two numbers"""
#     print("CALLED: multiply(a: int, b: int) -> int:")
#     return int(a * b)

# #  division tool
# @mcp.tool() 
# def divide(a: int, b: int) -> float:
#     """Divide two numbers"""
#     print("CALLED: divide(a: int, b: int) -> float:")
#     return float(a / b)

# # power tool
# @mcp.tool()
# def power(a: int, b: int) -> int:
#     """Power of two numbers"""
#     print("CALLED: power(a: int, b: int) -> int:")
#     return int(a ** b)

# # square root tool
# @mcp.tool()
# def sqrt(a: int) -> float:
#     """Square root of a number"""
#     print("CALLED: sqrt(a: int) -> float:")
#     return float(a ** 0.5)

# # cube root tool
# @mcp.tool()
# def cbrt(a: int) -> float:
#     """Cube root of a number"""
#     print("CALLED: cbrt(a: int) -> float:")
#     return float(a ** (1/3))

# # factorial tool
# @mcp.tool()
# def factorial(a: int) -> int:
#     """factorial of a number"""
#     print("CALLED: factorial(a: int) -> int:")
#     return int(math.factorial(a))

# # log tool
# @mcp.tool()
# def log(a: int) -> float:
#     """log of a number"""
#     print("CALLED: log(a: int) -> float:")
#     return float(math.log(a))

# # remainder tool
# @mcp.tool()
# def remainder(a: int, b: int) -> int:
#     """remainder of two numbers divison"""
#     print("CALLED: remainder(a: int, b: int) -> int:")
#     return int(a % b)

# # sin tool
# @mcp.tool()
# def sin(a: int) -> float:
#     """sin of a number"""
#     print("CALLED: sin(a: int) -> float:")
#     return float(math.sin(a))

# # cos tool
# @mcp.tool()
# def cos(a: int) -> float:
#     """cos of a number"""
#     print("CALLED: cos(a: int) -> float:")
#     return float(math.cos(a))

# # tan tool
# @mcp.tool()
# def tan(a: int) -> float:
#     """tan of a number"""
#     print("CALLED: tan(a: int) -> float:")
#     return float(math.tan(a))

# # mine tool
# @mcp.tool()
# def mine(a: int, b: int) -> int:
#     """special mining tool"""
#     print("CALLED: mine(a: int, b: int) -> int:")
#     return int(a - b - b)

# @mcp.tool()
# def create_thumbnail(image_path: str) -> Image:
#     """Create a thumbnail from an image"""
#     print("CALLED: create_thumbnail(image_path: str) -> Image:")
#     img = PILImage.open(image_path)
#     img.thumbnail((100, 100))
#     return Image(data=img.tobytes(), format="png")

# @mcp.tool()
# def strings_to_chars_to_int(string: str) -> list[int]:
#     """Return the ASCII values of the characters in a word"""
#     print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
#     return [int(ord(char)) for char in string]

# @mcp.tool()
# def int_list_to_exponential_sum(int_list: list) -> float:
#     """Return sum of exponentials of numbers in a list"""
#     print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
#     return sum(math.exp(i) for i in int_list)

# @mcp.tool()
# def fibonacci_numbers(n: int) -> list:
#     """Return the first n Fibonacci Numbers"""
#     print("CALLED: fibonacci_numbers(n: int) -> list:")
#     if n <= 0:
#         return []
#     fib_sequence = [0, 1]
#     for _ in range(2, n):
#         fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
#     return fib_sequence[:n]


# @mcp.tool()
# async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
#     """Draw a rectangle in Paint from (x1,y1) to (x2,y2)"""
#     global paint_app
#     try:
#         if not paint_app:
#             return {
#                 "content": [
#                     TextContent(
#                         type="text",
#                         text="Paint is not open. Please call open_paint first."
#                     )
#                 ]
#             }

#         # Get the Paint window
#         paint_window = paint_app.window(class_name='MSPaintApp')

#         # Ensure Paint window is active
#         if not paint_window.has_focus():
#             paint_window.set_focus()
#             time.sleep(0.2)

#         # Click on the Rectangle tool (updated coordinates from image)
#         paint_window.click_input(coords=(550, 90))
#         time.sleep(0.2)

#         # Get the canvas area
#         canvas = paint_window.child_window(class_name='MSPaintView')

#         # Draw rectangle on canvas
#         canvas.press_mouse_input(coords=(x1, y1))
#         canvas.move_mouse_input(coords=(x2, y2))
#         canvas.release_mouse_input(coords=(x2, y2))

#         return {
#             "content": [
#                 TextContent(
#                     type="text",
#                     text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
#                 )
#             ]
#         }

#     except Exception as e:
#         return {
#             "content": [
#                 TextContent(
#                     type="text",
#                     text=f"Error drawing rectangle: {str(e)}"
#                 )
#             ]
#         }


# @mcp.tool()
# async def add_text_in_paint(text: str, x1: int, y1: int) -> dict:
#     """Add text in Paint at a specific (x, y) location by drawing a text box."""
#     global paint_app
#     try:
#         if not paint_app:
#             return {
#                 "content": [
#                     TextContent(
#                         type="text",
#                         text="Paint is not open. Please call open_paint first."
#                     )
#                 ]
#             }
        
#         # Get Paint window
#         paint_window = paint_app.window(class_name='MSPaintApp')
        
#         # Ensure Paint window is active
#         if not paint_window.has_focus():
#             paint_window.set_focus()
#             time.sleep(0.5)
        
#         # Click on the Text Tool (A) - approximate toolbar position
#         paint_window.click_input(coords=(350, 98))
#         time.sleep(0.5)  # Allow tool selection

#         # Get canvas area
#         canvas = paint_window.child_window(class_name='MSPaintView')

#         # Define the size of the text box (e.g., 250x60 pixels)
#         box_width = 250
#         box_height = 60
#         x2 = x1 + box_width
#         y2 = y1 + box_height

#         # Draw a bounding text box using click-drag
#         canvas.press_mouse_input(coords=(x1, y1))
#         canvas.move_mouse_input(coords=(x2, y2))
#         canvas.release_mouse_input(coords=(x2, y2))
#         time.sleep(0.4)

#         # Type the text into the text box
#         paint_window.type_keys(text, with_spaces=True, pause=0.1)
#         time.sleep(0.5)

#         return {
#             "content": [
#                 TextContent(
#                     type="text",
#                     text=f"Text: '{text}' added at ({x1}, {y1})"
#                 )
#             ]
#         }

#     except Exception as e:
#         return {
#             "content": [
#                 TextContent(
#                     type="text",
#                     text=f"Error adding text: {str(e)}"
#                 )
#             ]
#         }




# @mcp.tool()
# async def open_paint() -> dict:
#     """Open Microsoft Paint maximized"""
#     global paint_app
#     try:
#         paint_app = Application().start(r'C:\Program Files\Classic Paint\mspaint1.exe')#'mspaint.exe')
#         time.sleep(0.2)

#         # Get the Paint window
#         paint_window = paint_app.window(class_name='MSPaintApp')

#         # Maximize the window
#         win32gui.ShowWindow(paint_window.handle, win32con.SW_MAXIMIZE)
#         time.sleep(0.2)

#         return {
#             "content": [
#                 TextContent(
#                     type="text",
#                     text="Paint opened successfully and maximized"
#                 )
#             ]
#         }

#     except Exception as e:
#         return {
#             "content": [
#                 TextContent(
#                     type="text",
#                     text=f"Error opening Paint: {str(e)}"
#                 )
#             ]
#         }

# @mcp.tool()
# def displacement(v0: float, a: float, t: float) -> float:
#     """
#     Calculates displacement for constant acceleration motion using the equation:
#     s = v₀t + ½at². Useful for projectile motion, vehicle braking distance, 
#     or any uniformly accelerated object.
#     """
#     return v0*t + 0.5*a*t**2




# ### 2. **Projectile Motion**
# @mcp.tool()
# def horizontal_range(v0: float, angle: float, g: float = 9.81) -> float:
#     """
#     Computes the horizontal distance traveled by a projectile launched at an angle,
#     neglecting air resistance. Derived from the range equation:
#     R = (v₀² sin(2θ)) / g. Applies to sports, artillery, and orbital mechanics.
#     """
#     from math import sin, radians
#     return (v0**2 * sin(2*radians(angle))) / g




# ### 3. **Work-Energy Theorem**
# @mcp.tool()
# def kinetic_energy(m: float, v: float) -> float:
#     """
#     Calculates the translational kinetic energy of an object using KE = ½mv².
#     Essential for collision analysis, energy conservation problems, and 
#     understanding the energy requirements for acceleration.
#     """
#     return 0.5 * m * v**2




# ### 4. **Ohm's Law & Power**
# @mcp.tool()
# def power(V: float, I: float) -> float:
#     """
#     Determines electrical power dissipation using P = VI. Fundamental for circuit design,
#     calculating energy consumption, and sizing electrical components like resistors.
#     """
#     return V * I




# ### 5. **Wave Physics**
# @mcp.tool()
# def doppler_shift(f0: float, vs: float, v_sound: float = 343) -> float:
#     """
#     Calculates the observed frequency change for a moving sound source approaching 
#     the observer (Doppler effect). Used in radar, medical ultrasound, and astronomy.
#     Formula: f_observed = f₀ * (v_sound / (v_sound - v_source)).
#     """
#     return f0 * (v_sound / (v_sound - vs))

# # DEFINE RESOURCES

# # Add a dynamic greeting resource
# @mcp.resource("greeting://{name}")
# def get_greeting(name: str) -> str:
#     """Get a personalized greeting"""
#     print("CALLED: get_greeting(name: str) -> str:")
#     return f"Hello, {name}!"


# # DEFINE AVAILABLE PROMPTS
# @mcp.prompt()
# def review_code(code: str) -> str:
#     return f"Please review this code:\n\n{code}"
#     print("CALLED: review_code(code: str) -> str:")


# @mcp.prompt()
# def debug_error(error: str) -> list[base.Message]:
#     return [
#         base.UserMessage("I'm seeing this error:"),
#         base.UserMessage(error),
#         base.AssistantMessage("I'll help debug that. What have you tried so far?"),
#     ]

# if __name__ == "__main__":
#     # Check if running with mcp dev command
#     print("STARTING")
#     if len(sys.argv) > 1 and sys.argv[1] == "dev":
#         mcp.run()  # Run without transport for dev server
#     else:
#         mcp.run(transport="stdio")  # Run with stdio for direct execution



# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
from pywinauto.application import Application
import win32gui
import win32con
import time
from win32api import GetSystemMetrics
from models import *
# instantiate an MCP server client
mcp = FastMCP("Calculator")
paint_app = None

# DEFINE TOOLS

# Basic arithmetic operations
@mcp.tool()
def add(input_data: BinaryOperationInput) -> OperationOutput:
    """Add two numbers"""
    print("CALLED: add(a: int, b: int) -> int:")
    return OperationOutput(result=int(input_data.a + input_data.b))

@mcp.tool()
def add_list(input_data: ListInput) -> OperationOutput:
    """Add all numbers in a list"""
    print("CALLED: add_list(values: list) -> int:")
    return OperationOutput(result=sum(input_data.values))

@mcp.tool()
def subtract(input_data: BinaryOperationInput) -> OperationOutput:
    """Subtract two numbers"""
    print("CALLED: subtract(a: int, b: int) -> int:")
    return OperationOutput(result=int(input_data.a - input_data.b))

@mcp.tool()
def multiply(input_data: BinaryOperationInput) -> OperationOutput:
    """Multiply two numbers"""
    print("CALLED: multiply(a: int, b: int) -> int:")
    return OperationOutput(result=int(input_data.a * input_data.b))

@mcp.tool() 
def divide(input_data: BinaryOperationInput) -> OperationOutput:
    """Divide two numbers"""
    print("CALLED: divide(a: int, b: int) -> float:")
    return OperationOutput(result=float(input_data.a / input_data.b))

@mcp.tool()
def power(input_data: BinaryOperationInput) -> OperationOutput:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return OperationOutput(result=int(input_data.a ** input_data.b))

@mcp.tool()
def remainder(input_data: BinaryOperationInput) -> OperationOutput:
    """Remainder of two numbers division"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return OperationOutput(result=int(input_data.a % input_data.b))

@mcp.tool()
def mine(input_data: BinaryOperationInput) -> OperationOutput:
    """Special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return OperationOutput(result=int(input_data.a - input_data.b - input_data.b))

# Unary math operations
@mcp.tool()
def sqrt(input_data: UnaryOperationInput) -> OperationOutput:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return OperationOutput(result=float(input_data.a ** 0.5))

@mcp.tool()
def cbrt(input_data: UnaryOperationInput) -> OperationOutput:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return OperationOutput(result=float(input_data.a ** (1/3)))

@mcp.tool()
def factorial(input_data: UnaryOperationInput) -> OperationOutput:
    """Factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return OperationOutput(result=int(math.factorial(input_data.a)))

@mcp.tool()
def log(input_data: UnaryOperationInput) -> OperationOutput:
    """Log of a number"""
    print("CALLED: log(a: int) -> float:")
    return OperationOutput(result=float(math.log(input_data.a)))

# Trigonometric functions
@mcp.tool()
def sin(input_data: UnaryOperationInput) -> OperationOutput:
    """Sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return OperationOutput(result=float(math.sin(input_data.a)))

@mcp.tool()
def cos(input_data: UnaryOperationInput) -> OperationOutput:
    """Cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return OperationOutput(result=float(math.cos(input_data.a)))

@mcp.tool()
def tan(input_data: UnaryOperationInput) -> OperationOutput:
    """Tan of a number"""
    print("CALLED: tan(a: int) -> float:")
    return OperationOutput(result=float(math.tan(input_data.a)))

# String and character operations
@mcp.tool()
def strings_to_chars_to_int(input_data: StringToCharsInput) -> CharsOutput:
    """Return the ASCII values of the characters in a word"""
    print("CALLED: strings_to_chars_to_int(string: str) -> list[int]:")
    return CharsOutput(values=[int(ord(char)) for char in input_data.string])

@mcp.tool()
def int_list_to_exponential_sum(input_data: ListInput) -> OperationOutput:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return OperationOutput(result=sum(math.exp(i) for i in input_data.values))

# Sequence operations
@mcp.tool()
def fibonacci_numbers(input_data: UnaryOperationInput) -> ListOutput:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    n = int(input_data.a)
    if n <= 0:
        return ListOutput(result=[])
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return ListOutput(result=fib_sequence[:n])

# Image operations
@mcp.tool()
def create_thumbnail(input_data: ImagePathInput) -> Image:
    """Create a thumbnail from an image"""
    print("CALLED: create_thumbnail(image_path: str) -> Image:")
    img = PILImage.open(input_data.image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")

# Physics operations
@mcp.tool()
def displacement(input_data: DisplacementInput) -> OperationOutput:
    """
    Calculates displacement for constant acceleration motion using the equation:
    s = v₀t + ½at². Useful for projectile motion, vehicle braking distance, 
    or any uniformly accelerated object.
    """
    return OperationOutput(result=input_data.v0 * input_data.t + 0.5 * input_data.a * input_data.t**2)

@mcp.tool()
def horizontal_range(input_data: ProjectileInput) -> OperationOutput:
    """
    Computes the horizontal distance traveled by a projectile launched at an angle,
    neglecting air resistance. Derived from the range equation:
    R = (v₀² sin(2θ)) / g. Applies to sports, artillery, and orbital mechanics.
    """
    from math import sin, radians
    return OperationOutput(
        result=(input_data.v0**2 * sin(2*radians(input_data.angle))) / input_data.g
    )

@mcp.tool()
def kinetic_energy(input_data: KineticEnergyInput) -> OperationOutput:
    """
    Calculates the translational kinetic energy of an object using KE = ½mv².
    Essential for collision analysis, energy conservation problems, and 
    understanding the energy requirements for acceleration.
    """
    return OperationOutput(result=0.5 * input_data.m * input_data.v**2)

@mcp.tool()
def electrical_power(input_data: ElectricalInput) -> OperationOutput:
    """
    Determines electrical power dissipation using P = VI. Fundamental for circuit design,
    calculating energy consumption, and sizing electrical components like resistors.
    """
    return OperationOutput(result=input_data.V * input_data.I)

@mcp.tool()
def doppler_shift(input_data: DopplerShiftInput) -> OperationOutput:
    """
    Calculates the observed frequency change for a moving sound source approaching 
    the observer (Doppler effect). Used in radar, medical ultrasound, and astronomy.
    Formula: f_observed = f₀ * (v_sound / (v_sound - v_source)).
    """
    return OperationOutput(
        result=input_data.f0 * (input_data.v_sound / (input_data.v_sound - input_data.vs))
    )

# Paint operations
@mcp.tool()
async def draw_rectangle(input_data: RectangleInput) -> dict:
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

        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.2)

        # Click on the Rectangle tool (updated coordinates from image)
        paint_window.click_input(coords=(550, 90))
        time.sleep(0.2)

        # Get the canvas area
        canvas = paint_window.child_window(class_name='MSPaintView')

        # Draw rectangle on canvas
        canvas.press_mouse_input(coords=(input_data.x1, input_data.y1))
        canvas.move_mouse_input(coords=(input_data.x2, input_data.y2))
        canvas.release_mouse_input(coords=(input_data.x2, input_data.y2))

        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Rectangle drawn from ({input_data.x1},{input_data.y1}) to ({input_data.x2},{input_data.y2})"
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
async def add_text_in_paint(input_data: TextPositionInput) -> dict:
    """Add text in Paint at a specific (x, y) location by drawing a text box."""
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
        
        # Get Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')
        
        # Ensure Paint window is active
        if not paint_window.has_focus():
            paint_window.set_focus()
            time.sleep(0.5)
        
        # Click on the Text Tool (A) - approximate toolbar position
        paint_window.click_input(coords=(350, 98))
        time.sleep(0.5)  # Allow tool selection

        # Get canvas area
        canvas = paint_window.child_window(class_name='MSPaintView')

        # Define the size of the text box (e.g., 250x60 pixels)
        box_width = 250
        box_height = 60
        x2 = input_data.x1 + box_width
        y2 = input_data.y1 + box_height

        # Draw a bounding text box using click-drag
        canvas.press_mouse_input(coords=(input_data.x1, input_data.y1))
        canvas.move_mouse_input(coords=(x2, y2))
        canvas.release_mouse_input(coords=(x2, y2))
        time.sleep(0.4)

        # Type the text into the text box
        paint_window.type_keys(input_data.text, with_spaces=True, pause=0.1)
        time.sleep(0.5)

        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Text: '{input_data.text}' added at ({input_data.x1}, {input_data.y1})"
                )
            ]
        }

    except Exception as e:
        return {
            "content": [
                TextContent(
                    type="text",
                    text=f"Error adding text: {str(e)}"
                )
            ]
        }

@mcp.tool()
async def open_paint() -> dict:
    """Open Microsoft Paint maximized"""
    global paint_app
    try:
        paint_app = Application().start(r'C:\Program Files\Classic Paint\mspaint1.exe')
        time.sleep(0.2)

        # Get the Paint window
        paint_window = paint_app.window(class_name='MSPaintApp')

        # Maximize the window
        win32gui.ShowWindow(paint_window.handle, win32con.SW_MAXIMIZE)
        time.sleep(0.2)

        return {
            "content": [
                TextContent(
                    type="text",
                    text="Paint opened successfully and maximized"
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
    print("CALLED: review_code(code: str) -> str:")
    return f"Please review this code:\n\n{code}"

@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution

