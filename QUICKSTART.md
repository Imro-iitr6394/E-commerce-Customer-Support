# Quick Start Guide

## Installation

```bash
# 1. Activate virtual environment
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize database
python setup_db.py
```

## Running the Web UI

```bash
# Terminal 1: Start MCP Server (port 8000)
python mcp_server.py

# Terminal 2: Start Agent API (port 8001)
python agent_api.py

# Terminal 3: Launch Streamlit (port 8501)
streamlit run streamlit_app.py
```

Streamlit will automatically open at: **http://localhost:8501**

## Running the CLI

```bash
# Terminal 1: Start MCP Server
python mcp_server.py

# Terminal 2: Run CLI Agent
python agent.py
```

## Architecture Overview

```
Streamlit UI (8501)
    ↓ HTTP POST /chat
Agent API (8001)
    ↓ SSE
MCP Server (8000)
    ↓ SQL Queries
SQLite Database (ecommerce.db)
```

## File Descriptions

| File | Purpose |
|------|---------|
| `mcp_server.py` | Exposes 5 e-commerce tools via MCP protocol |
| `agent_api.py` | FastAPI REST wrapper around LangGraph agent |
| `streamlit_app.py` | Web UI for conversations |
| `agent.py` | LangGraph state machine with intent routing |
| `tools.py` | Business logic (deterministic, no LLM) |
| `memory.py` | File-backed conversation history |
| `disk_checkpointer.py` | LangGraph checkpoint persistence |
| `setup_db.py` | Database initialization from CSVs |

## Example Queries

```
"What's the price of product 90K0C1fIyQUf?"
"Check order Axfy13Hk4PIk status"
"Can I return my order?"
"Show my purchase history"
"Recommend products for me"
```

## Troubleshooting

### Port already in use?
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Find process using port 8001
netstat -ano | findstr :8001

# Kill process (replace PID)
taskkill /PID <PID> /F
```

### Streamlit not connecting to API?
- Check API is running (should see log: "Agent API listening at http://127.0.0.1:8001")
- Check Streamlit sidebar shows ✅ API status
- Verify both are running on localhost

### Database errors?
- Ensure `train/` directory has CSV files
- Verify file paths in `setup_db.py`
- Delete `ecommerce.db` and run `python setup_db.py` again

## API Endpoints

```bash
# Send message
curl -X POST http://127.0.0.1:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!", "thread_id": "user_1"}'

# Check health
curl http://127.0.0.1:8001/health

# Clear conversation
curl -X DELETE http://127.0.0.1:8001/thread/user_1
```

## Performance Notes

- LLM calls (Gemini) take 3-10 seconds
- Database queries are instant
- Streamlit shows spinner while waiting for response
- All conversation history is persisted
