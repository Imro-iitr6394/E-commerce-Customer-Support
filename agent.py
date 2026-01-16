import os
import asyncio
import json
from typing import Annotated, List, TypedDict, Literal, Optional
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from disk_checkpointer import DiskBackedSaver
from memory import load_memory, append_memory, save_thread_messages
from pydantic import BaseModel, Field
from langchain_mcp_adapters.tools import load_mcp_tools

import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("agent")

load_dotenv()

# --- Models for Structured Output ---
class IntentClassification(BaseModel):
    intent: Literal["product_inquiry", "order_status", "returns", "customer_history", "general_chat"] = Field(
        description="The classified intent of the user query."
    )
    extracted_id: Optional[str] = Field(
        description="The extracted ID (product_id, order_id, or customer_id) if present."
    )

# --- State Definition ---
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], "The conversation history"]
    intent: Optional[str]
    extracted_id: Optional[str]
    tool_result: Optional[str]
    needs_more_info: bool
    final_response: Optional[str]

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", google_api_key=os.getenv("GEMINI_API_KEY"))
structured_llm = llm.with_structured_output(IntentClassification)

# --- MCP Tool Configuration ---
mcp_connection = {
    "transport": "sse",
    "url": "http://127.0.0.1:8000/sse"
}

# --- Nodes ---

async def initial_parse(state: AgentState):
    logger.info("--- Entering Graph: Initial Parse ---")
    return {"needs_more_info": False, "intent": None, "extracted_id": None, "tool_result": None}

async def classify_query(state: AgentState):
    logger.info("--- Node: Classify Query ---")
    messages = state["messages"]
    last_message = messages[-1].content
    
    # Build conversation context for better understanding
    context = "\n".join([f"{m.__class__.__name__.replace('Message', '')}: {m.content}" for m in messages[-5:]])
    
    prompt = f"""Given this conversation context:
{context}

Analyze the current user query and extract intent and any IDs mentioned in the conversation."""
    
    result = await structured_llm.ainvoke(prompt)
    
    return {
        "intent": result.intent,
        "extracted_id": result.extracted_id,
        "needs_more_info": result.intent != "general_chat" and not result.extracted_id
    }

async def execute_mcp_tool(state: AgentState):
    logger.info("--- Node: Execute MCP Tool ---")
    intent = state["intent"]
    eid = state["extracted_id"]
    
    if not eid:
        return {"tool_result": "Error: Missing required ID."}

    try:
        mcp_tools = await load_mcp_tools(None, connection=mcp_connection)
        
        tool_map = {
            "product_inquiry": "product_info",
            "order_status": "order_status",
            "returns": "return_request",
            "customer_history": "customer_history"
        }
        
        tool_name = tool_map.get(intent)
        target_tool = next((t for t in mcp_tools if t.name == tool_name), None)
        
        if not target_tool:
            return {"tool_result": f"Error: Tool {tool_name} not found on MCP server."}
        
        args = {"product_id": eid} if tool_name == "product_info" else \
               {"order_id": eid} if tool_name == "order_status" else \
               {"order_id": eid, "reason": "User requested via chat"} if tool_name == "return_request" else \
               {"customer_id": eid}
        
        logger.info(f"Executing MCP Tool: {tool_name}")
        tool_output = await target_tool.ainvoke(args)

        if isinstance(tool_output, tuple) and len(tool_output) == 2:
            result, artifact = tool_output
        else:
            result = tool_output
            artifact = None

        formatted_result = ""
        if isinstance(result, dict):
            try:
                formatted_result = json.dumps(result)
            except Exception:
                formatted_result = str(result)
        elif isinstance(result, list):
            for block in result:
                if isinstance(block, dict) and block.get("type") == "text":
                    formatted_result += block.get("text", "")
                else:
                    formatted_result += str(block)
        else:
            formatted_result = str(result)

        return {"tool_result": formatted_result, "tool_result_raw": result}
    except Exception as e:
        return {"tool_result": f"Error connecting to MCP server: {e}"}

def decide_next_step(state: AgentState):
    logger.info("--- Router: Deciding Next Step ---")
    if state["needs_more_info"]:
        return "ask_for_info"
    if state["intent"] == "general_chat":
        return "generate_response"
    return "execute_tool"

async def ask_for_info(state: AgentState):
    logger.info("--- Node: Ask for Information ---")
    intent = state["intent"]
    msg = f"I understand you're asking about {intent.replace('_', ' ')}, but I need an ID (like an Order ID or Product ID) to help you. Could you please provide it?"
    return {"messages": [AIMessage(content=msg)]}

async def generate_final_response(state: AgentState):
    logger.info("--- Node: Generate Final Response ---")
    tool_result = state.get("tool_result")
    tool_raw = state.get("tool_result_raw")
    history = state["messages"]
    
    # Build full conversation context
    conversation_context = "\n".join([
        f"{m.__class__.__name__.replace('Message', '')}: {m.content}" 
        for m in history[-10:]
    ])
    
    if isinstance(tool_raw, dict) and tool_raw.get("status") == "error":
        msg = (
            "I couldn't retrieve the requested data from the backend. "
            "I'm escalating this issue to a human agent. Please provide more details."
        )
        return {"messages": [AIMessage(content=msg)]}

    if tool_result:
        prompt = f"""Based on the conversation history and system data, provide a helpful response:

CONVERSATION:
{conversation_context}

SYSTEM DATA FROM MCP SERVER:
{tool_result}

Provide a natural, conversational response that directly answers the user's question and refers back to the conversation context when relevant."""
    else:
        prompt = f"""Based on the conversation, provide a helpful response:

CONVERSATION:
{conversation_context}

Please provide a natural, conversational response that directly addresses the user's question and refers to previous context when relevant."""
        
    response = await llm.ainvoke(prompt)
    final_content = response.content
    if isinstance(final_content, list):
        final_content = "".join([m.get("text", "") if isinstance(m, dict) else str(m) for m in final_content])
        
    return {"messages": [AIMessage(content=final_content)]}

# --- Graph Construction ---
builder = StateGraph(AgentState)

builder.add_node("initial", initial_parse)
builder.add_node("classify", classify_query)
builder.add_node("tool_exec", execute_mcp_tool)
builder.add_node("ask_info", ask_for_info)
builder.add_node("respond", generate_final_response)

builder.set_entry_point("initial")
builder.add_edge("initial", "classify")

builder.add_conditional_edges(
    "classify",
    decide_next_step,
    {
        "ask_for_info": "ask_info",
        "generate_response": "respond",
        "execute_tool": "tool_exec"
    }
)

builder.add_edge("tool_exec", "respond")
builder.add_edge("ask_info", END)
builder.add_edge("respond", END)

# Memory: use disk-backed saver for checkpoint persistence
memory = DiskBackedSaver(filename="lg_checkpoint.pkl")
app = builder.compile(checkpointer=memory)

# --- Execution Helper ---
async def run_bot():
    """Interactive chat loop that maintains conversation history and invokes the agent graph."""
    print("--- E-commerce Agent (LangGraph + MCP) ---")
    thread_id = "user_456"
    config = {"configurable": {"thread_id": thread_id}}
    
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ['exit', 'quit']:
                break
            
            mem = load_memory(thread_id, limit=20)
            messages = []
            for m in mem:
                role = m.get("role")
                content = m.get("content")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
                else:
                    messages.append(SystemMessage(content=content))

            messages.append(HumanMessage(content=user_input))
            inputs = {"messages": messages}
            async for event in app.astream(inputs, config, stream_mode="values"):
                pass
                
            final_state = app.get_state(config)
            last_msg = final_state.values["messages"][-1].content
            print(f"Assistant: {last_msg}")

            append_memory(thread_id, "user", user_input)
            append_memory(thread_id, "assistant", last_msg)

            try:
                lg_messages = []
                for m in final_state.values.get("messages", []):
                    role = "assistant" if m.__class__.__name__ == "AIMessage" else "user" if m.__class__.__name__ == "HumanMessage" else "system"
                    lg_messages.append({"role": role, "content": m.content})
                save_thread_messages(thread_id, lg_messages)
            except Exception:
                pass
            
        except Exception as e:
            logger.error(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_bot())
