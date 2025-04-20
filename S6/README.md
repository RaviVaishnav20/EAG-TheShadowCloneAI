# The Shadow Clone AI - System 6 (Modular Architecture)

This project implements an AI agent capable of performing mathematical computations, physics calculations, and visual diagramming tasks through a modular, well-organized architecture.

## Project Structure

The system has been reorganized into clean, focused modules:

```
S6/
├── action.py            # Core action implementations and tool definitions
├── config.py            # Server configuration
├── decision_making.py   # Decision logic and LLM interaction
├── llm.py               # LLM client and generation utilities
├── logger.py            # Custom logging system with JSON output
├── main.py              # Main execution loop and agent orchestration
├── memory.py            # Short-term and long-term memory management
├── models.py            # Pydantic models for type safety
├── perception.py        # Query interpretation and analysis
├── universal_system_prompt.py  # Core agent instruction set
├── utils.py            # Utility functions (extract_function_call etc.)
└── tool_prompt.py      # Tool description generator
```

## Key Improvements from Previous Version

1. **Modular Architecture**:
   - Separated concerns into distinct components
   - Clear data flow between modules
   - Better type safety with Pydantic models

2. **Enhanced Capabilities**:
   - Added physics calculations (kinematics, energy, electricity)
   - Improved Paint integration with text and shapes
   - Advanced math operations (factorials, roots, trigonometry)

3. **Robust Infrastructure**:
   - Comprehensive logging system
   - Memory management (short-term and long-term)
   - Error handling and validation

## Core Components

### 1. Action Module (`action.py`)
- Contains all executable tools including:
  - Mathematical operations (basic and advanced)
  - Physics calculations (displacement, projectile motion, energy)
  - Paint integration (drawing, text)
  - Special utilities (Fibonacci, ASCII conversion)

### 2. Decision System (`decision_making.py`)
- Orchestrates the THINK-VERIFY-ACT cycle
- Interfaces with LLM for decision generation
- Manages tool selection and parameter validation

### 3. Memory System (`memory.py`)
- Short-term memory for operation context
- SQLite-backed long-term memory (commented out but available)
- Context preservation across iterations

### 4. LLM Integration (`llm.py`)
- Gemini API client with timeout handling
- Asynchronous generation support
- Configurable via environment variables

### 5. Utility Modules
- `tool_prompt.py`: Generates tool descriptions for LLM context
- `utils.py`: Contains helper functions like `extract_function_call`
- `logger.py`: Custom logging with both console and JSON output

## Usage

1. Configure the system by setting up your `.env` file with Gemini API key
2. Run the main agent:
   ```bash
   python main.py
   ```
3. The system will process the hardcoded query (can be modified in `main.py`)

## Example Workflows

### Physics Calculation:
```python
"A 1200 kg car braking at -8 m/s² for 3 seconds before hitting a barrier. 
What was its initial kinetic energy and how far did it travel during braking?"
```

### Visual Task:
```python
"Open Microsoft Paint, draw a rectangle, and add the text 'AI Agent Demo' above the rectangle."
```

## Configuration

Edit `config.py` to:
- Set server file path
- Configure command type

## Dependencies

- Python 3.8+
- Required packages:
  - `mcp`
  - `pywinauto`
  - `win32gui`
  - `Pillow`
  - `pydantic`
  - `google-generativeai`

Install with:
```bash
pip install -r requirements.txt
```

## Future Enhancements

1. Implement full long-term memory persistence
2. Add more physics and engineering calculations
3. Expand visual toolkit with additional shapes and effects
4. Implement interactive mode for user queries
```