from mcp.server.fastmcp import FastMCP
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3] # This gets /Users/ravi/EAG-TheShadowCloneAI/S8

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.server.math_server.schema.math_model import *

mcp = FastMCP("Calculator")
#Basic arithmetic operations
@mcp.tool()
def add(input_data: AddInput) -> OperationOutput:
    """Add two numbers"""
    return OperationOutput(result=int(input_data.a + input_data.b))

@mcp.tool()
def subtract(input_data: SubtractInput) -> OperationOutput:
    """Subtract two numbers"""
    return OperationOutput(result=int(input_data.a - input_data.b))

@mcp.tool()
def multiply(input_data: MultiplyInput) -> OperationOutput:
    """Multiply two numbers"""
    return OperationOutput(result=int(input_data.a * input_data.b))

@mcp.tool()
def divide(input_data: DivideInput) -> OperationOutput:
    """Divide two numbers"""
    return OperationOutput(result=float(input_data.a / input_data.b))

@mcp.tool()
def power(input_data: PowerInput) -> OperationOutput:
    """Power of two numbers"""
    print("CALLED: power(a: int, b: int) -> int:")
    return OperationOutput(result=int(input_data.a ** input_data.b))

@mcp.tool()
def remainder(input_data: RemainderInput) -> OperationOutput:
    """Remainder of two numbers division"""
    print("CALLED: remainder(a: int, b: int) -> int:")
    return OperationOutput(result=int(input_data.a % input_data.b))

@mcp.tool()
def mine(input_data: MineInput) -> OperationOutput:
    """Special mining tool"""
    print("CALLED: mine(a: int, b: int) -> int:")
    return OperationOutput(result=int(input_data.a - input_data.b - input_data.b))

# Unary math operations
@mcp.tool()
def sqrt(input_data: SqrtInput) -> OperationOutput:
    """Square root of a number"""
    print("CALLED: sqrt(a: int) -> float:")
    return OperationOutput(result=float(input_data.a ** 0.5))

@mcp.tool()
def cbrt(input_data: CbrtInput) -> OperationOutput:
    """Cube root of a number"""
    print("CALLED: cbrt(a: int) -> float:")
    return OperationOutput(result=float(input_data.a ** (1/3)))

@mcp.tool()
def factorial(input_data: FactorialInput) -> OperationOutput:
    """Factorial of a number"""
    print("CALLED: factorial(a: int) -> int:")
    return OperationOutput(result=int(math.factorial(input_data.a)))

@mcp.tool()
def log(input_data: LogInput) -> OperationOutput:
    """Log of a number"""
    print("CALLED: log(a: int) -> float:")
    return OperationOutput(result=float(math.log(input_data.a)))

# Trigonometric functions
@mcp.tool()
def sin(input_data: SinInput) -> OperationOutput:
    """Sin of a number"""
    print("CALLED: sin(a: int) -> float:")
    return OperationOutput(result=float(math.sin(input_data.a)))

@mcp.tool()
def cos(input_data: CosInput) -> OperationOutput:
    """Cos of a number"""
    print("CALLED: cos(a: int) -> float:")
    return OperationOutput(result=float(math.cos(input_data.a)))

@mcp.tool()
def tan(input_data: TanInput) -> OperationOutput:
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
def int_list_to_exponential_sum(input_data: ExponentialSumInput) -> OperationOutput:
    """Return sum of exponentials of numbers in a list"""
    print("CALLED: int_list_to_exponential_sum(int_list: list) -> float:")
    return OperationOutput(result=sum(math.exp(i) for i in input_data.values))

# Sequence operations
@mcp.tool()
def fibonacci_numbers(input_data: FibonacciInput) -> ListOutput:
    """Return the first n Fibonacci Numbers"""
    print("CALLED: fibonacci_numbers(n: int) -> list:")
    n = int(input_data.a)
    if n <= 0:
        return ListOutput(result=[])
    fib_sequence = [0, 1]
    for _ in range(2, n):
        fib_sequence.append(fib_sequence[-1] + fib_sequence[-2])
    return ListOutput(result=fib_sequence[:n])

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


if __name__ == "__main__":
    print("math_server.py starting")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
            mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
        print("\nShutting down...")
