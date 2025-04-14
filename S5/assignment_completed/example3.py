from typing import Union, List, Tuple, Optional, Any
import math
import numpy as np
from scipy.optimize import fsolve
from sympy import symbols, Eq, solve
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
mcp = FastMCP("Mathmatic Tools")

# DEFINE TOOLS
@mcp.tool()
def solve_equation(equation_str: str, variable: str = 'x') -> Union[List[Union[float, complex]], str]:
    """
    Symbolically finds all solutions to algebraic equations, handling polynomials up to quartic
    and various transcendental equations. Can return both real and complex roots. Works with equations
    expressed as strings with standard Python mathematical syntax.
    """
    try:
        x = symbols(variable)
        lhs, rhs = equation_str.split('=')
        equation = Eq(eval(lhs), eval(rhs))
        solution = solve(equation, x)
        return [complex(sol) for sol in solution]  # Convert to complex to handle all cases
    except Exception as e:
        return f"Error solving equation: {str(e)}"

@mcp.tool()
def numerical_integration(function_str: str, a: float, b: float, n: int = 1000) -> Union[float, str]:
    """
    Computes definite integrals using the trapezoidal rule, approximating the area under curves
    for functions that may not have elementary antiderivatives. Particularly useful for
    oscillating functions or probability distributions where symbolic integration fails.
    """
    try:
        def f(x: float) -> float:
            return eval(function_str, {'math': math, 'x': x})
        
        if a > b:
            a, b = b, a  # Handle reverse bounds
        
        dx = (b - a) / n
        integral = 0.5 * (f(a) + f(b))
        for i in range(1, n):
            integral += f(a + i * dx)
        integral *= dx
        return float(integral)
    except Exception as e:
        return f"Error in numerical integration: {str(e)}"

@mcp.tool()
def solve_ode(dy_dx_str: str, y0: float, x_range: Tuple[float, float], 
              step_size: float = 0.1) -> Union[List[Tuple[float, float]], str]:
    """
    Numerically solves first-order ordinary differential equations using Euler's method,
    generating a series of (x,y) points that approximate the solution curve. Ideal for
    modeling exponential decay/growth, simple harmonic motion, and population dynamics.
    """
    try:
        def dy_dx(x: float, y: float) -> float:
            return eval(dy_dx_str, {'x': x, 'y': y})
        
        x_start, x_end = x_range
        if step_size <= 0:
            raise ValueError("Step size must be positive")
        
        x_values = np.arange(x_start, x_end + step_size, step_size)
        y_values = np.zeros(len(x_values))
        y_values[0] = y0
        
        for i in range(1, len(x_values)):
            y_values[i] = y_values[i-1] + dy_dx(x_values[i-1], y_values[i-1]) * step_size
        
        return list(zip(x_values.tolist(), y_values.tolist()))
    except Exception as e:
        return f"Error solving ODE: {str(e)}"

@mcp.tool()
def matrix_operations(matrix1: List[List[float]], 
                     matrix2: Optional[List[List[float]]], 
                     operation: str) -> Union[float, List[List[float]], str]:
    """
    Performs fundamental linear algebra operations including matrix arithmetic, inversion,
    and determinant calculation. Handles systems of linear equations and linear transformations
    essential for computer graphics, statistics, and machine learning applications.
    """
    try:
        np_matrix1 = np.array(matrix1, dtype=np.float64)
        
        if operation in ["multiplication", "addition"]:
            if matrix2 is None:
                raise ValueError("Second matrix required for this operation")
            np_matrix2 = np.array(matrix2, dtype=np.float64)
            
            if operation == "multiplication":
                return np.matmul(np_matrix1, np_matrix2).tolist()
            else:  # addition
                if np_matrix1.shape != np_matrix2.shape:
                    raise ValueError("Matrices must have same dimensions for addition")
                return (np_matrix1 + np_matrix2).tolist()
        
        elif operation == "inverse":
            return np.linalg.inv(np_matrix1).tolist()
        
        elif operation == "determinant":
            return float(np.linalg.det(np_matrix1))
        
        else:
            return "Unsupported operation"
    except Exception as e:
        return f"Error in matrix operation: {str(e)}"

@mcp.tool()
def find_root(function_str: str, initial_guess: Union[float, List[float]]) -> Union[float, List[float], str]:
    """
    Locates roots/zeros of nonlinear equations using advanced numerical methods, capable of
    finding intersections, equilibrium points, and solutions to transcendental equations.
    Robust against local minima/maxima through intelligent gradient-based searching.
    """
    try:
        def f(x: Union[float, List[float]]) -> float:
            if isinstance(x, (list, np.ndarray)):
                return eval(function_str, {f'x{i}': val for i, val in enumerate(x)})
            return eval(function_str, {'x': x})
        
        root = fsolve(f, initial_guess)
        return root[0] if len(root) == 1 else root.tolist()
    except Exception as e:
        return f"Error finding root: {str(e)}"

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
