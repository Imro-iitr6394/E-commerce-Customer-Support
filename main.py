import os
import asyncio
import subprocess
import time
import sys
from dotenv import load_dotenv

load_dotenv()


def start_mcp_server():
    """Start the MCP server in a background process."""
    print("=== Starting MCP Server ===")
    return subprocess.Popen(
        [sys.executable, "mcp_server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )


def run_mcp_agent():
    """Run the agent which connects to the MCP server."""
    print("\n=== Launching MCP Agent ===")
    import agent
    asyncio.run(agent.run_bot())


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="E-commerce Assistant")
    parser.add_argument("--agent", action="store_true", help="Run MCP-integrated agent")
    parser.add_argument("--with-server", action="store_true", help="Start MCP server before agent")
    args = parser.parse_args()
    
    if args.agent or args.with_server:
        if args.with_server:
            server_proc = start_mcp_server()
            time.sleep(2)
            print("MCP Server started. Agent connecting...")
        try:
            run_mcp_agent()
        except KeyboardInterrupt:
            print("\nAgent stopped.")
            if args.with_server:
                server_proc.terminate()
    else:
        print("Usage: python main.py [--agent] [--with-server]")
        print("  --agent: Run the MCP-integrated agent")
        print("  --with-server: Start the MCP server before running the agent")

if __name__ == "__main__":
    run_chatbot()
