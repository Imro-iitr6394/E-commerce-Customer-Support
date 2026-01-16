import pandas as pd
import sqlite3
import os

TRAIN_DIR = r"train"
DB_PATH = "ecommerce.db"


def setup_database():
    """Create and populate the e-commerce database from CSV files."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Loading datasets...")
    products_df = pd.read_csv(os.path.join(TRAIN_DIR, "df_Products.csv"))
    orders_df = pd.read_csv(os.path.join(TRAIN_DIR, "df_Orders.csv"))
    order_items_df = pd.read_csv(os.path.join(TRAIN_DIR, "df_OrderItems.csv"))
    customers_df = pd.read_csv(os.path.join(TRAIN_DIR, "df_Customers.csv"))

    print("Processing products...")
    product_prices = order_items_df.groupby('product_id')['price'].agg(
        lambda x: x.mode().iloc[0] if not x.mode().empty else x.mean()
    ).reset_index()
    unique_products = products_df[['product_id', 'product_category_name']]
    unique_products = unique_products.merge(product_prices, on='product_id', how='left')
    
    unique_products['stock_status'] = 'In Stock'
    unique_products['description'] = unique_products['product_category_name'].apply(
        lambda x: f"A high-quality product in the {x} category."
    )
    unique_products.rename(columns={'product_category_name': 'name'}, inplace=True)
    
    unique_products.to_sql('products', conn, index=False)

    print("Processing orders...")
    orders_needed = orders_df[['order_id', 'customer_id', 'order_status', 'order_purchase_timestamp']]
    orders_needed.to_sql('orders', conn, index=False)

    print("Processing order items...")
    order_items_needed = order_items_df[['order_id', 'product_id', 'price']]
    order_items_needed.to_sql('order_items', conn, index=False)

    print("Processing customers...")
    customers_needed = customers_df[['customer_id']]
    customers_needed.to_sql('customers', conn, index=False)

    conn.close()
    print(f"Database setup complete: {DB_PATH}")


if __name__ == "__main__":
    setup_database()
