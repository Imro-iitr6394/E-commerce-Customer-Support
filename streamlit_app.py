import streamlit as st
import requests
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="E-commerce Support Assistant",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
    <style>
    .message-container {
        display: flex;
        margin: 10px 0;
        padding: 10px;
        border-radius: 8px;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 20%;
    }
    </style>
""", unsafe_allow_html=True)

# Configuration
API_URL = "http://127.0.0.1:8001"
CHAT_ENDPOINT = f"{API_URL}/chat"
HEALTH_ENDPOINT = f"{API_URL}/health"

# Sidebar
with st.sidebar:
    st.title("⚙️ Configuration")
    
    thread_id = st.text_input(
        "User/Thread ID",
        value="streamlit_user",
        help="Unique identifier for maintaining conversation history"
    )
    
    st.divider()
    
    # Server status
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=2)
        if response.status_code == 200:
            st.success("✅ Agent API is running")
        else:
            st.error("❌ Agent API error")
    except requests.exceptions.ConnectionError:
        st.error("❌ Agent API not running")
        st.info("Start the agent API with: `python agent_api.py`")
    except Exception as e:
        st.error(f"❌ Error checking API: {str(e)}")
    
    st.divider()
    
    if st.button("🔄 Clear Conversation", use_container_width=True):
        try:
            requests.delete(f"{API_URL}/thread/{thread_id}")
            st.session_state.messages = []
            st.success("Conversation cleared!")
            st.rerun()
        except Exception as e:
            st.error(f"Error clearing conversation: {str(e)}")
    
    st.divider()
    
    st.markdown("""
    ### 📋 How to Use
    
    1. **Ask Questions**: Type in the chat box below
    2. **Thread ID**: Each thread maintains separate history
    3. **Clear**: Use the button above to reset
    
    ### 🛠️ Supported Queries
    
    - Product info: "What's the price of product X?"
    - Order status: "Check order X"
    - Returns: "Can I return order X?"
    - History: "Show my purchase history"
    - Recommendations: "Recommend products for me"
    """)


# Main content
st.title("🛒 E-commerce Customer Support")
st.markdown("Powered by LangGraph + MCP Server")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
chat_container = st.container()
with chat_container:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Input area
if prompt := st.chat_input("Ask about products, orders, returns, or recommendations..."):
    # Add user message to session state
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Send to API and get response
    with st.spinner("🔄 Getting response..."):
        try:
            response = requests.post(
                CHAT_ENDPOINT,
                json={
                    "message": prompt,
                    "thread_id": thread_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                assistant_message = data.get("response", "No response received")
                
                # Add to session state
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_message
                })
                
                # Display assistant response
                with st.chat_message("assistant"):
                    st.markdown(assistant_message)
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                st.error(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ {error_msg}"
                })
                
        except requests.exceptions.ConnectionError:
            error = "Cannot connect to Agent API. Make sure it's running on port 8001."
            st.error(f"❌ {error}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ Connection Error: {error}"
            })
        except requests.exceptions.Timeout:
            error = "Request timed out. The agent may be processing a complex query."
            st.warning(f"⏱️ {error}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"⏱️ {error}"
            })
        except Exception as e:
            error = f"Unexpected error: {str(e)}"
            st.error(f"❌ {error}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ {error}"
            })

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8em;'>
    E-commerce Support Assistant | MCP Server Running on :8000 | Agent API on :8001
</div>
""", unsafe_allow_html=True)
