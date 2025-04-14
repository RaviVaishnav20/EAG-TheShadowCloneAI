# README: MCP Agent System for Mathematical and Visual Tasks

## Overview

This system combines mathematical computation capabilities with visual diagramming tools through an agent-based architecture. The system consists of two main components:

1. `example2.py` - The MCP server providing a suite of mathematical and visual tools
2. `talk2mcp.py` - The client application that communicates with the MCP server using a structured reasoning process

## Key Features

- **Dual Capability Agent**: Performs both mathematical computations and visual diagramming
- **Structured Reasoning Process**: Follows a strict THINK-VERIFY-ACT cycle
- **Tool Integration**: 20+ mathematical functions and Paint automation tools
- **Error Handling**: Built-in validation for both mathematical and visual tasks

## System Prompt Architecture

The core of the agent's intelligence is defined in the system prompt, which enforces a strict workflow:

### 1. Reasoning Structure

```text
1. THINK: Analyze the task requirements
   - For math: Identify formulas/theorems needed
   - For visuals: Determine diagram components

2. VERIFY: Validate parameters and workflow
   - Math: Check unit consistency and value ranges
   - Visual: Confirm coordinates are within bounds

3. ACT: Execute exactly ONE action per cycle
   - Math: FUNCTION_CALL with appropriate parameters
   - Visual: Initialize then draw components
```

### 2. Strict Rules

**Math-Specific:**
- Always include units in FINAL_ANSWER
- Validate input ranges (e.g., mass > 0)
- Use appropriate precision (3 decimal places)

**Visual-Specific:**
- Must call `open_paint` before any drawing
- Keep elements centered (x:100-900, y:300-700)
- Text must fit within shapes

**Universal:**
- One action per THINK-VERIFY-ACT cycle
- Final output must be FINAL_ANSWER
- Explicit error handling

### 3. Example Workflows

**Computation Example:**
```text
THINK: Need to calculate projectile range using R = (v₀² sin2θ)/g
VERIFY: Velocity=20m/s and angle=45° are valid inputs
FUNCTION_CALL: {"name": "horizontal_range", "args": {"v0": 20, "angle": 45}}  
FINAL_ANSWER: 40.8 meters
```

**Visual Task Example:**
```text
THINK: Need to diagram a 300×200 rectangle labeled "Projectile"
VERIFY: Coordinates (400,400)→(700,600) are within bounds
FUNCTION_CALL: {"name": "open_paint", "args": {}}
FUNCTION_CALL: {"name": "draw_rectangle", "args": {"x1":400,"y1":400,"x2":700,"y2":600}}
FUNCTION_CALL: {"name": "add_text_in_paint", "args": {"text":"Projectile","x":550,"y":500}}
FINAL_ANSWER: Diagram complete
```

## Available Tools

The system provides numerous tools including:

**Mathematical Functions:**
- Basic operations (add, subtract, multiply, divide)
- Advanced math (power, roots, logarithms)
- Physics calculations (kinematics, projectile motion, energy)
- Special functions (Fibonacci sequence, ASCII conversions)

**Visual Tools:**
- Paint automation (open, draw rectangles, add text)
- Image processing (thumbnail creation)

## Usage

1. Configure your environment variables with `GEMINI_API_KEY`
2. Run the MCP server: `python example2.py dev`
3. Execute the client: `python talk2mcp.py`

Sample queries you can try:
- "A 0.5 kg ball is thrown at 20 m/s at a 30° angle. What is its kinetic energy at launch and its maximum horizontal range?"
- "Open Microsoft Paint, draw a rectangle, and add the text 'AI Agent Demo' inside the rectangle."
- "Calculate the first 20 Fibonacci numbers."

## Error Handling

The system provides clear error messages for:
- Invalid parameters
- Missing initialization for visual tasks
- Out-of-bounds coordinates
- Unit inconsistencies in physics calculations