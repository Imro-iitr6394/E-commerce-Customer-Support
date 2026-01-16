import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List

DB_PATH = "ecommerce.db"


def _validate_id(value: str) -> bool:
    """Validate that an ID is a non-empty string."""
    return isinstance(value, str) and bool(value.strip())


def _connect():
    """Get a connection to the e-commerce database."""
    return sqlite3.connect(DB_PATH)


def get_product_info(product_id: str) -> Dict[str, Any]:
    """Fetch product details by product_id.
    
    Returns structured dict with product info or error payload.
    """
    if not _validate_id(product_id):
        return {"status": "error", "code": "invalid_input", "message": "product_id is required"}

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT product_id, name, price, stock_status, description FROM products WHERE product_id = ?",
        (product_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"status": "error", "code": "not_found", "message": "Product not found", "product_id": product_id}

    return {
        "status": "ok",
        "product": {
            "product_id": row[0],
            "name": row[1],
            "price": float(row[2]) if row[2] is not None else None,
            "stock_status": row[3],
            "description": row[4],
        },
    }


def check_order_status(order_id: str) -> Dict[str, Any]:
    """Fetch order status and purchase timestamp by order_id."""
    if not _validate_id(order_id):
        return {"status": "error", "code": "invalid_input", "message": "order_id is required"}

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT order_status, order_purchase_timestamp FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"status": "error", "code": "not_found", "message": "Order not found", "order_id": order_id}

    return {"status": "ok", "order": {"order_id": order_id, "status": row[0], "purchase_timestamp": row[1]}}


def process_return_request(order_id: str, reason: str) -> Dict[str, Any]:
    """Process a return request. Checks eligibility within 30-day return window."""
    if not _validate_id(order_id):
        return {"status": "error", "code": "invalid_input", "message": "order_id is required"}

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute("SELECT order_purchase_timestamp FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"status": "error", "code": "not_found", "message": "Order not found", "order_id": order_id}

    purchase_date_str = row[0]
    try:
        purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d")
        except Exception:
            purchase_date = None

    current_date = datetime.now()

    if purchase_date and current_date - purchase_date <= timedelta(days=30):
        return {
            "status": "ok",
            "order_id": order_id,
            "eligible": True,
            "message": "Return request accepted. Please use the prepaid label for shipping.",
            "reason_recorded": reason,
        }
    else:
        return {"status": "ok", "order_id": order_id, "eligible": False, "message": "Order is outside the 30-day return window."}


def get_customer_history(customer_id: str, limit: int = 50) -> Dict[str, Any]:
    """Fetch purchase history for a customer with their orders and products."""
    if not _validate_id(customer_id):
        return {"status": "error", "code": "invalid_input", "message": "customer_id is required"}

    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT o.order_id, o.order_status, o.order_purchase_timestamp, oi.product_id, oi.price
        FROM orders o
        JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.customer_id = ?
        ORDER BY o.order_purchase_timestamp DESC
        LIMIT ?
    """,
        (customer_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()

    history: List[Dict[str, Any]] = []
    for row in rows:
        history.append({
            "order_id": row[0],
            "status": row[1],
            "timestamp": row[2],
            "product_id": row[3],
            "price": float(row[4]) if row[4] is not None else None,
        })

    return {"status": "ok", "customer_id": customer_id, "history": history}


def recommend_products(customer_id: str, limit: int = 5) -> Dict[str, Any]:
    """Simple recommendation: recommend frequently bought product categories excluding already-bought items."""
    hist = get_customer_history(customer_id, limit=100)
    if hist.get("status") != "ok":
        return {"status": "error", "code": "no_history", "message": "No customer history available"}

    purchased = {h["product_id"] for h in hist.get("history", [])}

    conn = _connect()
    cursor = conn.cursor()
    # Find products not yet purchased; prefer ones with a price and in-stock
    cursor.execute(
        "SELECT product_id, name, price, stock_status, description FROM products WHERE product_id NOT IN ({}) LIMIT ?".format(
            ",".join(["?" for _ in purchased]) if purchased else "''"
        ),
        tuple(purchased) + (limit,) if purchased else (limit,),
    )
    rows = cursor.fetchall()
    conn.close()

    recs = []
    for row in rows:
        recs.append({
            "product_id": row[0],
            "name": row[1],
            "price": float(row[2]) if row[2] is not None else None,
            "stock_status": row[3],
        })

    return {"status": "ok", "recommendations": recs}
