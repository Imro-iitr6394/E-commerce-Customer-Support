# E-commerce Customer Support Assistant

A production-ready MCP-based system that combines a FastMCP server with a LangGraph agent to provide intelligent e-commerce customer support through natural language conversations. Includes both CLI and web UI interfaces.

## Overview

This project demonstrates a clean separation of concerns between:

- **MCP Server** (`mcp_server.py`): Exposes deterministic e-commerce tools via HTTP/SSE
- **Agent API** (`agent_api.py`): REST API wrapper around the LangGraph agent
- **Streamlit UI** (`https://e-commerce-customer-support-ixiwt9skdg7ygdce6gyfbp.streamlit.app/`): Modern web interface for conversations
- **Database** (`ecommerce.db`): SQLite database with product, order, and customer data

The agent uses Google's Gemini API for intent classification and response generation, while tools provide reliable, structured access to business data.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                      │
│                                                               │
│  ┌──────────────────┐          ┌──────────────────────────┐ │
│  │  CLI (agent.py)  │          │  Web UI (Streamlit)      │ │
│  │  Interactive     │          │  Browser-based           │ │
│  └────────┬─────────┘          └──────────┬───────────────┘ │
│           │                                │                  │
└───────────┼────────────────────────────────┼──────────────────┘
            │                                │
            │         HTTP                  │ HTTP
            │         (SSE)                  │ (REST)
            │                                │
┌───────────▼────────────────────────────────▼──────────────────┐
│                  Server Layer                                  │
│                                                                │
│  ┌──────────────────────┐       ┌──────────────────────────┐ │
│  │   MCP Server         │       │   Agent API              │ │
│  │   Port :8000         │       │   Port :8001             │ │
│  │   - product_info     │       │   POST /chat             │ │
│  │   - order_status     │       │   DELETE /thread/{id}    │ │
│  │   - return_request   │       │   GET /health            │ │
│  │   - customer_history │       │                          │ │
│  │   - recommend        │       │   Manages LangGraph      │ │
│  │                      │       │   state & memory         │ │
│  └──────────┬───────────┘       └──────────┬───────────────┘ │
│             │                              │                  │
│             └──────────────────┬───────────┘                  │
│                                │                              │
└────────────────────────────────┼──────────────────────────────┘
                                 │
                 ┌───────────────▼─────────────┐
                 │  SQLite Database            │
                 │  - products                 │
                 │  - orders                   │
                 │  - order_items              │
                 │  - customers                │
                 └─────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.10+
- Google Gemini API key
- CSV data files in `train/` directory

### Installation

1. Clone and navigate to the project:
   ```bash
   cd Faclon
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up your Gemini API key in `.env`:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

4. Initialize the database from CSV files:
   ```bash
   python setup_db.py
   ```

### Running the System

#### Option 1: Web UI (Recommended)

**Terminal 1** - Start the MCP server:
```bash
python mcp_server.py
```

**Terminal 2** - Start the Agent API:
```bash
python agent_api.py
```

**Terminal 3** - Launch Streamlit:
```bash
streamlit run streamlit_app.py
```

Streamlit will open automatically at `http://localhost:8501`

#### Option 2: CLI Mode

**Terminal 1** - Start the MCP server:
```bash
python mcp_server.py
```

**Terminal 2** - Run the CLI agent:
```bash
python agent.py
```

#### Option 3: Automated Startup (Web UI)

Create a PowerShell script `run_all.ps1`:
```powershell
# Start MCP Server
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "mcp_server.py"

# Start Agent API
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "agent_api.py"

# Wait for servers to start
Start-Sleep -Seconds 3

# Start Streamlit
Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m streamlit run streamlit_app.py"
```

Then run:
```bash
.\run_all.ps1
```

## Web UI Features

The Streamlit interface provides:

- **💬 Real-time Chat**: Clean conversation interface with message history
- **🔄 Thread Management**: Separate conversations per user ID
- **📋 Quick Actions**: Pre-filled example queries
- **✅ Server Status**: Live monitoring of API availability
- **🗑️ Clear History**: Reset conversation with one click
- **📱 Responsive Design**: Works on desktop and mobile

### Supported Queries

```
"What's the price of product 90K0C1fIyQUf?"
"Check the status of order Axfy13Hk4PIk"
"Can I return order Axfy13Hk4PIk?"
"Show my purchase history"
"Recommend products for customer hCT0x9JiGXBQ"
"Hello, what can you help me with?"
```

## Client-Server Communication

### API Endpoints

#### POST `/chat`
Send a message and receive a response.

**Request:**
```json
{
  "message": "What's the price of product 90K0C1fIyQUf?",
  "thread_id": "user_123"
}
```

**Response:**
```json
{
  "response": "The product is priced at $49.99 and is currently in stock...",
  "thread_id": "user_123",
  "status": "success"
}
```

#### DELETE `/thread/{thread_id}`
Clear conversation history for a thread.

**Response:**
```json
{
  "status": "success",
  "message": "Thread user_123 cleared"
}
```

#### GET `/health`
Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "service": "E-commerce Agent API"
}
```

### Data Flow

1. **User Input** (Streamlit) → `POST /chat` request to Agent API
2. **Agent Processing** → Agent loads message history, invokes MCP tools as needed
3. **Tool Execution** → MCP server queries SQLite database
4. **Response Generation** → Gemini LLM formats the response
5. **API Response** → Agent API returns response to Streamlit
6. **Display** → Streamlit renders response in UI
7. **Persistence** → Both memory.json and checkpoint files updated

## MCP Tools

The server exposes five tools accessible to the agent:

### `product_info(product_id: str)`
Fetch product details by ID.

**Returns:**
```json
{
  "status": "ok",
  "product": {
    "product_id": "90K0C1fIyQUf",
    "name": "Electronics",
    "price": 49.99,
    "stock_status": "In Stock",
    "description": "A high-quality product in the Electronics category."
  }
}
```

### `order_status(order_id: str)`
Check the current status of an order.

**Returns:**
```json
{
  "status": "ok",
  "order": {
    "order_id": "Axfy13Hk4PIk",
    "status": "shipped",
    "purchase_timestamp": "2026-01-10 14:23:45"
  }
}
```

### `return_request(order_id: str, reason: str)`
Process a return request with eligibility validation (30-day window).

**Returns:**
```json
{
  "status": "ok",
  "order_id": "Axfy13Hk4PIk",
  "eligible": true,
  "message": "Return request accepted. Please use the prepaid label for shipping.",
  "reason_recorded": "Item damaged"
}
```

### `customer_history(customer_id: str, limit: int = 50)`
Retrieve a customer's purchase history.

**Returns:**
```json
{
  "status": "ok",
  "customer_id": "hCT0x9JiGXBQ",
  "history": [
    {
      "order_id": "Axfy13Hk4PIk",
      "status": "delivered",
      "timestamp": "2026-01-10 14:23:45",
      "product_id": "90K0C1fIyQUf",
      "price": 49.99
    }
  ]
}
```

### `recommend(customer_id: str, limit: int = 5)`
Get product recommendations based on customer history.

**Returns:**
```json
{
  "status": "ok",
  "recommendations": [
    {
      "product_id": "abc123",
      "name": "Accessories",
      "price": 19.99,
      "stock_status": "In Stock"
    }
  ]
}
```

## Agent Workflow

The agent follows a stateful graph-based workflow:

```
Initial Parse
    ↓
Classify Query
    ├─→ General Chat? ─→ Generate Response ─→ END
    │
    ├─→ Needs ID? ─→ Ask for Information ─→ END
    │
    └─→ Execute Tool ─→ Generate Response ─→ END
```

### State Transitions

1. **Initial Parse**: Reset state flags
2. **Classify Query**: Use Gemini to classify intent (product_inquiry, order_status, returns, customer_history, general_chat)
3. **Conditional Routing**:
   - If general_chat: Generate response without tools
   - If missing ID: Ask user for required information
   - Otherwise: Execute the appropriate MCP tool
4. **Generate Response**: Use tool results to craft a helpful response

## Design Decisions

### Why MCP Server?
- **Standardized Tool Interface**: MCP provides a protocol-based way for agents to invoke tools
- **HTTP/SSE Transport**: Allows agent and server to run independently
- **Separation of Concerns**: Business logic (tools) stays decoupled from reasoning (agent)

### Why LangGraph?
- **Explicit State Management**: Easy to understand flow and add breakpoints
- **Async Support**: Efficiently handles concurrent tool calls
- **Checkpointing**: Conversation state persists across restarts
- **Composability**: Easy to add new nodes/edges without refactoring

### Why FastAPI for Agent API?
- **REST Standard**: Easy for any client (web, mobile, desktop) to integrate
- **Async/Await**: Non-blocking operations for better performance
- **Built-in Validation**: Pydantic models ensure request/response integrity
- **Auto-generated Docs**: Swagger UI at `/docs`

### Why Streamlit for UI?
- **Rapid Development**: Build interactive UIs in pure Python
- **Zero Frontend Skills**: No JavaScript/HTML/CSS required
- **Session Management**: Built-in state management for conversations
- **Responsive**: Works on mobile and desktop

### Why SQLite + CSV?
- **Deterministic**: No AI-based data augmentation—tools return exactly what's in the database
- **Testable**: Easy to populate with real e-commerce data
- **Lightweight**: No external database dependencies

## File Structure

```
├── mcp_server.py         # MCP server with 5 tools (port :8000)
├── agent.py              # LangGraph agent workflow
├── agent_api.py          # FastAPI wrapper for agent (port :8001)
├── streamlit_app.py      # Streamlit web UI
├── tools.py              # Tool implementations (deterministic)
├── main.py               # CLI launcher script
├── setup_db.py           # Database initialization from CSVs
├── memory.py             # Conversation history (file-backed)
├── disk_checkpointer.py  # LangGraph checkpoint persistence
├── requirements.txt      # Python dependencies
├── .env                  # API key configuration
├── ecommerce.db          # SQLite database (auto-generated)
├── memory.json           # Conversation history (auto-generated)
├── lg_checkpoint.pkl     # LangGraph checkpoints (auto-generated)
├── train/                # CSV data files
│   ├── df_Products.csv
│   ├── df_Orders.csv
│   ├── df_OrderItems.csv
│   └── df_Customers.csv
└── README.md             # This file
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `mcp` | MCP protocol library |
| `fastapi` + `uvicorn` | HTTP servers for MCP/SSE and Agent API |
| `langgraph` | Agent workflow orchestration |
| `langchain-google-genai` | Gemini API integration |
| `langchain-mcp-adapters` | Bridges LangChain agents to MCP servers |
| `python-dotenv` | Environment variable loading |
| `pandas` | CSV processing for setup |
| `streamlit` | Web UI framework |
| `requests` | HTTP client for Streamlit ↔ Agent API communication |

## Testing & Validation

### 1. Test Database Setup
```bash
python setup_db.py
```
Should create `ecommerce.db` with 4 tables.

### 2. Test MCP Server
```bash
python mcp_server.py
```
Should log: `"SSE server listening at http://127.0.0.1:8000/sse"`

### 3. Test Agent API (requires MCP server running)
```bash
python agent_api.py
```
Should log: `"Agent API listening at http://127.0.0.1:8001"`

### 4. Test API Endpoint (in another terminal)
```bash
curl -X POST http://127.0.0.1:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "thread_id": "test_user"}'
```

### 5. Test Streamlit UI (with API running)
```bash
streamlit run streamlit_app.py
```
Should open browser at `http://localhost:8501`

## Troubleshooting

### MCP Server won't start
- Check if port 8000 is already in use: `netstat -ano | findstr :8000`
- Ensure CSV files exist in `train/` directory
- Check `.env` file has valid `GEMINI_API_KEY`

### Agent API won't start
- Ensure MCP server is running on port 8000
- Check if port 8001 is already in use: `netstat -ano | findstr :8001`

### Streamlit can't connect to API
- Check Agent API status in sidebar (should show ✅)
- Ensure API is running on `http://127.0.0.1:8001`
- Check firewall settings if running on different machine

### Agent takes too long to respond
- This is normal for LLM calls (3-10 seconds)
- Check Streamlit logs for specific errors
- Reduce `limit` parameter in `customer_history` call if querying large datasets

## Production Considerations

- **Scale**: For production, replace SQLite with PostgreSQL/MySQL
- **Auth**: Add API key validation to MCP server and Agent API
- **Logging**: Use structured logging (JSON) instead of console output
- **Caching**: Add Redis for frequently accessed queries
- **Rate Limiting**: Implement per-user/IP throttling
- **Monitoring**: Add Prometheus metrics and health checks
- **Deployment**: Use Docker to containerize services

## Contributing

To add a new tool:

1. Implement in `tools.py` with structured output
2. Register in `mcp_server.py` with `@mcp.tool()`
3. Update `tool_map` in `agent.py` to enable auto-routing
4. Add tool description for LLM intent classification

## License

This project is provided as-is for educational and technical demonstration purposes.
