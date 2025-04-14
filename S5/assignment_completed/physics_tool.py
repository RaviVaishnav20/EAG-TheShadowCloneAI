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

# instantiate an MCP server client
mcp = FastMCP("Calculator")

# DEFINE TOOLS
### 1. **Kinematic Equations**
@mcp.tool()
def displacement(v0: float, a: float, t: float) -> float:
    """
    Calculates displacement for constant acceleration motion using the equation:
    s = v₀t + ½at². Useful for projectile motion, vehicle braking distance, 
    or any uniformly accelerated object.
    """
    return v0*t + 0.5*a*t**2




### 2. **Projectile Motion**
@mcp.tool()
def horizontal_range(v0: float, angle: float, g: float = 9.81) -> float:
    """
    Computes the horizontal distance traveled by a projectile launched at an angle,
    neglecting air resistance. Derived from the range equation:
    R = (v₀² sin(2θ)) / g. Applies to sports, artillery, and orbital mechanics.
    """
    from math import sin, radians
    return (v0**2 * sin(2*radians(angle))) / g




### 3. **Work-Energy Theorem**
@mcp.tool()
def kinetic_energy(m: float, v: float) -> float:
    """
    Calculates the translational kinetic energy of an object using KE = ½mv².
    Essential for collision analysis, energy conservation problems, and 
    understanding the energy requirements for acceleration.
    """
    return 0.5 * m * v**2




### 4. **Ohm's Law & Power**
@mcp.tool()
def power(V: float, I: float) -> float:
    """
    Determines electrical power dissipation using P = VI. Fundamental for circuit design,
    calculating energy consumption, and sizing electrical components like resistors.
    """
    return V * I




### 5. **Wave Physics**
@mcp.tool()
def doppler_shift(f0: float, vs: float, v_sound: float = 343) -> float:
    """
    Calculates the observed frequency change for a moving sound source approaching 
    the observer (Doppler effect). Used in radar, medical ultrasound, and astronomy.
    Formula: f_observed = f₀ * (v_sound / (v_sound - v_source)).
    """
    return f0 * (v_sound / (v_sound - vs))



if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution