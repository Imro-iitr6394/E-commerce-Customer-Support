import os
import asyncio
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from agent import app as agent_graph

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent_api")

api = FastAPI(title="E-commerce Agent API", version="1.0")

# Request/Response models
class MessageRequest(BaseModel):
    """User message request."""
    message: str
    thread_id: str = "default_user"


class MessageResponse(BaseModel):
    """Agent response."""
    response: str
    thread_id: str
    status: str


@api.post("/chat", response_model=MessageResponse)
async def chat(request: MessageRequest):
    """Send a message to the agent and get a response.
    
    Maintains conversation history per thread_id.
    """
    try:
        logger.info(f"Chat request - thread_id={request.thread_id}, message={request.message[:50]}...")
        
        # Build the state input for the graph
        from langchain_core.messages import HumanMessage
        from memory import load_memory
        
        thread_id = request.thread_id
        cfg = {"configurable": {"thread_id": thread_id}}
        
        # Load previous messages
        mem = load_memory(thread_id, limit=20)
        messages = []
        for m in mem:
            role = m.get("role")
            content = m.get("content")
            if role == "user":
                from langchain_core.messages import HumanMessage
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=content))
            else:
                from langchain_core.messages import SystemMessage
                messages.append(SystemMessage(content=content))
        
        # Add current message
        messages.append(HumanMessage(content=request.message))
        inputs = {"messages": messages}
        
        # Run the agent
        async for event in agent_graph.astream(inputs, cfg, stream_mode="values"):
            pass
        
        # Get final response
        final_state = agent_graph.get_state(cfg)
        last_msg = final_state.values["messages"][-1].content
        
        # Persist to memory
        from memory import append_memory
        append_memory(thread_id, "user", request.message)
        append_memory(thread_id, "assistant", last_msg)
        
        return MessageResponse(
            response=last_msg,
            thread_id=thread_id,
            status="success"
        )
        
    except Exception as e:
        logger.exception(f"Error processing message: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@api.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "E-commerce Agent API"}


@api.delete("/thread/{thread_id}")
async def clear_thread(thread_id: str):
    """Clear conversation history for a thread."""
    try:
        from memory import save_thread_messages
        save_thread_messages(thread_id, [])
        logger.info(f"Cleared thread: {thread_id}")
        return {"status": "success", "message": f"Thread {thread_id} cleared"}
    except Exception as e:
        logger.exception(f"Error clearing thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting E-commerce Agent API")
    logger.info("Ensure MCP server is running on http://127.0.0.1:8000")
    logger.info("Agent API listening at http://127.0.0.1:8001")
    
    uvicorn.run(api, host="127.0.0.1", port=8001)
