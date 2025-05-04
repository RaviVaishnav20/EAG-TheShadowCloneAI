from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
# -------------------------------
# RAG
# -------------------------------
# Define input and output models
# Define input model
# class SearchQueryInput(BaseModel):
#     """Search query parameters"""
#     query: str = Field(..., description="The search query text")
#     top_k: int = Field(5, description="Maximum number of results to return")
#     include_context: bool = Field(True, description="Whether to include text chunks in results")
#     min_score: float = Field(0.0, description="Minimum similarity score threshold")

# Wrapper model that follows the expected tool input format
# class SearchQuery(BaseModel):
#     input_data: SearchQueryInput

# Define output models
class SearchResult(BaseModel):
    """Single search result"""
    doc_id: str
    title: str
    chunk: str
    chunk_id: str
    score: float
    rank: int
    source_type: str
    url: Optional[str] = None

class SearchResponse(BaseModel):
    """Search response containing results"""
    results: List[SearchResult]
    query: str
    total_results: int
    
class SearchDocumentInput(BaseModel):
    query: str

# class SearchDocumentOutput(BaseModel):
#     result: List[str]
    
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


# -------------------------------
# System Models
# -------------------------------
#Perception

#Memory


#Decision


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
