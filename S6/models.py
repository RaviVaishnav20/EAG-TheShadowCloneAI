from pydantic import BaseModel
from typing import List, Union, Optional


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

#Action
# Define generic classes for similar operations
class BinaryOperationInput(BaseModel):
    """Generic class for operations with two inputs of the same type"""
    a: Union[int, float]
    b: Union[int, float]

class UnaryOperationInput(BaseModel):
    """Generic class for operations with one input"""
    a: Union[int, float]

class OperationOutput(BaseModel):
    """Generic class for operation results"""
    result: Union[int, float]

class ListInput(BaseModel):
    """Generic class for operations with a list input"""
    values: List[Union[int, float]]

class ListOutput(BaseModel):
    """Generic class for operations with a list output"""
    result: Union[int, float, List[Union[int, float]]]

class StringInput(BaseModel):
    """Generic class for operations with string input"""
    text: str

class StringOutput(BaseModel):
    """Generic class for operations with string output"""
    result: str

class MessageOutput(BaseModel):
    """Generic class for operations that return a message"""
    message: str

# Paint operations
class RectangleInput(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int

class TextPositionInput(BaseModel):
    text: str
    x1: int
    y1: int

# Specific physics operation inputs
class DisplacementInput(BaseModel):
    v0: float
    a: float
    t: float

class ProjectileInput(BaseModel):
    v0: float
    angle: float
    g: float = 9.81

class KineticEnergyInput(BaseModel):
    m: float
    v: float

class ElectricalInput(BaseModel):
    V: float
    I: float

class DopplerShiftInput(BaseModel):
    f0: float
    vs: float
    v_sound: float = 343

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
