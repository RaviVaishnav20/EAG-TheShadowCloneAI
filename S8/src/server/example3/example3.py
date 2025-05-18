from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from PIL import Image as PILImage
import math
import sys
import mcp
import json
import re
import json 
import faiss
import numpy as np
import time
from pathlib import Path
import requests
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]  # This gets /Users/ravi/EAG-TheShadowCloneAI/S8

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.server.example3.schema.models import *
from src.common.logger.logger import get_logger

logger = get_logger()
mcp = FastMCP("RAG")

# Configuration
EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
print(f"ROOT: {ROOT}")

# ROOT = Path(__file__).parent.resolve()
INDEX_CACHE = ROOT / "resources" / "faiss_index"
INDEX_FILE = INDEX_CACHE /  "index.bin"
METADATA_FILE = INDEX_CACHE / "metadata.json"
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class SearchQuery(BaseModel):
    query: str

class SearchResult(BaseModel):
    chunk: str
    url: Optional[str] = None


class SearchResponse(BaseModel):
    results: List[SearchResult]

def get_embedding(text: str):
    """Get embedding for text using local Ollama API"""
    try:
        response = requests.post(EMBED_URL, json={"model": EMBED_MODEL, "prompt": text})
        response.raise_for_status()
        return np.array(response.json()["embedding"], dtype=np.float32)
    except Exception as e:
        logger.error(f"Error getting embedding: {e}")
        raise

def load_index_and_metadata():
    """Load existing FAISS index and metadata"""
    if not INDEX_FILE.exists() or not METADATA_FILE.exists():
        logger.error(f"Search index not found at: {INDEX_FILE}")
        return None, None
    
    try:
        metadata = json.loads(METADATA_FILE.read_text())
        index = faiss.read_index(str(INDEX_FILE))
        return index, metadata
    except Exception as e:
        logger.error(f"Error loading index or metadata: {e}")
        return None, None

def extract_url_from_doc_id(doc_id: str) -> Optional[str]:
    """Extract URL from doc_id if it appears to be a URL"""
    url_pattern = re.compile(r'^https?://\S+$')
    if url_pattern.match(doc_id):
        return doc_id
    return None
 

@mcp.tool()
def vector_search(query_params: SearchQuery) -> SearchResponse:
    """
    Search for documents similar to the query using vector similarity.
    
    This tool searches through a vector index of documents and returns the most similar
    results to the provided query, ranked by similarity score.
    """
    # Get the input parameters from the query object
    # input_data = query.query
    # top_k = 5
    # include_context = True
    # min_score = 0.0
    # query = input_data.query
    try:
        # Load index and metadata
        if not INDEX_FILE.exists() or not METADATA_FILE.exists():
            logger.error("Search index files not found")
            return SearchResponse(
                results=[]
            )
        
        try:
            # Load metadata
            metadata = json.loads(METADATA_FILE.read_text())
            # Load index
            index = faiss.read_index(str(INDEX_FILE))
            
            logger.info(f"Successfully loaded index with {index.ntotal} vectors and {len(metadata)} metadata entries")
            
            if index.ntotal == 0:
                logger.warning("Index exists but contains no vectors")
                return SearchResponse(results=[], query=query_params.query, total_results=0)
                
        except Exception as e:
            logger.error(f"Error loading index or metadata: {e}")
            return SearchResponse(
                results=[]
            )
        
        # Get embedding for query
        try:
            query_embedding = get_embedding(query_params.query)
            query_embedding = np.array([query_embedding], dtype=np.float32)
        except Exception as e:
            logger.error(f"Error getting query embedding: {e}")
            return SearchResponse(
                results=[]
            )
        
        # Search
        top_k = 3
        k = min(top_k * 2, index.ntotal)  # Fetch more results than needed for filtering
        D, I = index.search(query_embedding, k)
        
        logger.info(f"Search returned {len(I[0])} initial results")
        logger.info(f"Raw distances: {D[0]}")  # Log the raw distances for debugging
        
        results = []
        for i, (distance, idx) in enumerate(zip(D[0], I[0])):
            if idx >= len(metadata) or idx < 0:
                logger.warning(f"Invalid index {idx} found in search results (metadata length: {len(metadata)})")
                continue
            
            # Convert distance to similarity score (higher is better)
            # Using a different formula for score calculation
            # score = float(1.0 / (1.0 + distance))
            
            # logger.info(f"Result {i}: distance={distance}, score={score}, min_score={query_params.min_score}")
            # effective_min_score = 0.0  # Temporarily disable score filtering for testing
            # if score < effective_min_score:
            #     logger.info(f"Skipping result {i} due to low score: {score} < {effective_min_score}")
                # continue
            # Extract metadata for this result
            result_meta = metadata[idx].copy()
            print("Extract metadata for this result")
            print(result_meta)

            doc_id = result_meta.get("doc_id", "")

            # Include chunk text if requested
            result = {
                "chunk": result_meta.get("chunk", "")
            }

            url = None
            if 'http' in doc_id or 'https' in doc_id:
                url = doc_id
                result['url'] = url

            results.append(result)
 
        # Sort by score and limit to requested number
        # results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]
        
        logger.info(f"Returning {len(results)} final filtered results")
        
        return SearchResponse(
            results=results
        )
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        return SearchResponse(
            results=[]
        )
    
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



# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: TextContent) -> TextContent:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"

# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: CodeInput) -> TextContent:
    print("CALLED: review_code(code: str) -> str:")
    return f"Please review this code:\n\n{code}"

@mcp.prompt()
def debug_error(error: ErrorInput) -> DebugOutput:
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

