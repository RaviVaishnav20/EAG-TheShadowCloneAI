from pydantic import BaseModel
from typing import List, Union, Optional

# -------------------------------
# Core Models
# -------------------------------
class OperationOutput(BaseModel):
    result: Union[int, float]

class ListOutput(BaseModel):
    result: List[Union[int, float]]

class TextContent(BaseModel):
    text: str

# -------------------------------
# Math Operations
# -------------------------------
class AddInput(BaseModel):
    a: Union[int, float]
    b: Union[int, float]

class SubtractInput(BaseModel):
    a: Union[int, float]
    b: Union[int, float]

class MultiplyInput(BaseModel):
    a: Union[int, float]
    b: Union[int, float]

class DivideInput(BaseModel):
    a: Union[int, float]
    b: Union[int, float]

class PowerInput(BaseModel):
    a: Union[int, float]
    b: Union[int, float]

class RemainderInput(BaseModel):
    a: Union[int, float]
    b: Union[int, float]

class MineInput(BaseModel):
    a: Union[int, float]
    b: Union[int, float]

class AddListInput(BaseModel):
    values: List[Union[int, float]]

class ExponentialSumInput(BaseModel):
    values: List[Union[int, float]]

class SqrtInput(BaseModel):
    number: Union[int, float]

class CbrtInput(BaseModel):
    number: Union[int, float]

class FactorialInput(BaseModel):
    number: int

class LogInput(BaseModel):
    number: Union[int, float]

class SinInput(BaseModel):
    angle: Union[int, float]  # In radians

class CosInput(BaseModel):
    angle: Union[int, float]

class TanInput(BaseModel):
    angle: Union[int, float]

class FibonacciInput(BaseModel):
    n: int  # Number of terms

# -------------------------------
# Physics Operations
# -------------------------------
class DisplacementInput(BaseModel):
    v0: float  # Initial velocity (m/s)
    a: float   # Acceleration (m/s²)
    t: float   # Time (s)

class ProjectileInput(BaseModel):
    v0: float   # Initial velocity (m/s)
    angle: float  # Launch angle (degrees)
    g: float = 9.81  # Gravity (m/s²)

class KineticEnergyInput(BaseModel):
    m: float  # Mass (kg)
    v: float  # Velocity (m/s)

class ElectricalInput(BaseModel):
    V: float  # Voltage (V)
    I: float  # Current (A)

class DopplerShiftInput(BaseModel):
    f0: float      # Source frequency (Hz)
    vs: float      # Source velocity (m/s)
    v_sound: float = 343  # Speed of sound (m/s)

# -------------------------------
# Image/Visual Operations
# -------------------------------
class ImagePathInput(BaseModel):
    image_path: str

class RectangleInput(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int

class TextPositionInput(BaseModel):
    text: str
    x1: int
    y1: int

# -------------------------------
# System Models
# -------------------------------
#Perception
class PerceptionInput(BaseModel):
    query: str

class PerceptionOutput(BaseModel):
    result: str

#Memory
class GetSTMemoryInput(BaseModel):
    key: str

class GetSTMemoryOutput(BaseModel):
    result: str

class UpdateSTMemoryInput(BaseModel):
    key: str
    value: str

#Decision
class DECISION_INPUT(BaseModel):
    query: str
    chat_history: str
    tools_description: str

# Specific conversion operations
class StringToCharsInput(BaseModel):
    string: str

class CharsOutput(BaseModel):
    values: List[int]

# Image operations
class ImagePathInput(BaseModel):
    image_path: str

# Debug operations
class CodeInput(BaseModel):
    code: str

class ErrorInput(BaseModel):
    error: str

class DebugOutput(BaseModel):
    messages: List[dict]
