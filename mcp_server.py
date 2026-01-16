from mcp.server.fastmcp import FastMCP
from tools import (
    get_product_info,
    check_order_status,
    process_return_request,
    get_customer_history,
    recommend_products,
)
import logging
import sys
import json

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp_server")

mcp = FastMCP("E-commerce Assistant")


@mcp.tool()
def product_info(product_id: str) -> str:
    """Get product details: name, price, stock status, and description."""
    logger.info(f"product_info: {product_id}")
    result = get_product_info(product_id)
    return json.dumps(result)


@mcp.tool()
def order_status(order_id: str) -> str:
    """Check the status of an order (pending, shipped, delivered, cancelled)."""
    logger.info(f"order_status: {order_id}")
    result = check_order_status(order_id)
    return json.dumps(result)


@mcp.tool()
def return_request(order_id: str, reason: str) -> str:
    """Process a return request. Checks if order is within the 30-day return window."""
    logger.info(f"return_request: {order_id}")
    result = process_return_request(order_id, reason)
    return json.dumps(result)


@mcp.tool()
def customer_history(customer_id: str) -> str:
    """Get a customer's purchase history and previous orders."""
    logger.info(f"customer_history: {customer_id}")
    result = get_customer_history(customer_id)
    return json.dumps(result)


@mcp.tool()
def recommend(customer_id: str, limit: int = 5) -> str:
    """Recommend products for a customer based on purchase history."""
    logger.info(f"recommend: {customer_id}")
    result = recommend_products(customer_id, limit=limit)
    return json.dumps(result)


if __name__ == "__main__":
    try:
        logger.info("Starting MCP Server: E-commerce Assistant")
        logger.info("Waiting for MCP client (Claude / Cursor / mcp dev)...")
        logger.info(f"SSE server listening at http://{mcp.settings.host}:{mcp.settings.port}/sse")
        
        mcp.run(transport="sse")
        
    except KeyboardInterrupt:
        logger.info("MCP Server stopped by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"MCP Server error: {e}")
        sys.exit(1)
