from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import asyncio
import uvicorn
from typing import List, Dict, Any, Optional
import logging
from agent_wrapper import AgentEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Agent API", description="API for interacting with the Shadow Clone AI agent")

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    result: str
    steps: Optional[List[Dict[str, Any]]] = None

# Create a single instance of the agent engine
agent_engine = AgentEngine()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    await agent_engine.initialize()
    logger.info("Agent engine initialized")

@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest, background_tasks: BackgroundTasks):
    try:
        logger.info(f"Received query: {request.query}")
        
        # Use the singleton agent engine to process the query
        try:
            result = await asyncio.wait_for(
                agent_engine.process_query(request.query, request.session_id), 
                timeout=60.0  # 60 second timeout
            )
            
            # Return the response
            response = QueryResponse(
                result=result.get("result", "No response from agent"),
                steps=result.get("steps", [])
            )
            
            return response
        
        except asyncio.TimeoutError:
            logger.error("Agent processing timed out")
            raise HTTPException(status_code=504, detail="Processing timed out")
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok", "agent_initialized": agent_engine._initialized}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)