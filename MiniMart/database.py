"""
database.py
------------
All SQLite database logic for the MiniMart Inventory Management System.

Keeping every database function in this one file makes it easy to see
exactly how the app talks to the database, and keeps app.py focused on
routing instead of raw SQL.
"""

import sqlite3
import uuid
from datetime import datetime, timedelta

DB_NAME = "database.db"


# ---------------------------------------------------------------------
# Connection / setup
# ---------------------------------------------------------------------

def get_db_connection():
    """Open a new connection to the SQLite database.

    row_factory = sqlite3.Row lets us access columns by name,
    e.g. row["name"] instead of row[1].
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they do not already exist.

    This is safe to call every time the app starts: it will NOT delete
    or recreate existing tables/data. It only fills in sample products
    the very first time the products table is empty.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            low_stock_threshold INTEGER NOT NULL DEFAULT 5,
            image_filename TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT UNIQUE NOT NULL,
            total_amount REAL NOT NULL,
            transaction_date TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaction_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            product_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (transaction_id) REFERENCES transactions (transaction_id)
        )
    """)

    conn.commit()

    # Seed sample products only the very first time (table is empty)
    cursor.execute("SELECT COUNT(*) FROM products")
    product_count = cursor.fetchone()[0]

    if product_count == 0:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sample_products = [
            ("P001", "Coca-Cola", "Beverages", 25, 50, 5, now, now),
            ("P002", "Lucky Me Canton", "Food", 15, 40, 5, now, now),
            ("P003", "Piattos", "Snacks", 25, 30, 5, now, now),
            ("P004", "Bear Brand", "Beverages", 15, 25, 5, now, now),
            ("P005", "Safeguard Soap", "Personal Care", 30, 20, 5, now, now),
        ]
        cursor.executemany("""
            INSERT INTO products
                (product_id, name, category, price, stock, low_stock_threshold, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_products)
        conn.commit()

    conn.close()


# ---------------------------------------------------------------------
# Product helpers
# ---------------------------------------------------------------------

CATEGORIES = [
    "Beverages",
    "Food",
    "Snacks",
    "Personal Care",
    "Household",
    "School Supplies",
    "Other",
]


def get_all_products(search=None, category=None):
    """Return all products, optionally filtered by a search term
    (matches product_id or name) and/or an exact category."""
    conn = get_db_connection()

    query = "SELECT * FROM products WHERE 1=1"
    params = []

    if search:
        query += " AND (product_id LIKE ? OR name LIKE ? OR category LIKE ?)"
        like_term = f"%{search}%"
        params.extend([like_term, like_term, like_term])

    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY name ASC"

    products = conn.execute(query, params).fetchall()
    conn.close()
    return products


def get_product_by_id(id):
    """Look up a product by its internal auto-increment id."""
    conn = get_db_connection()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (id,)).fetchone()
    conn.close()
    return product


def product_id_exists(product_id, exclude_id=None):
    """Check whether a human-facing product_id (e.g. 'P006') is already used.
    exclude_id lets us ignore the product's own row when editing."""
    conn = get_db_connection()
    if exclude_id:
        row = conn.execute(
            "SELECT id FROM products WHERE product_id = ? AND id != ?",
            (product_id, exclude_id)
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id FROM products WHERE product_id = ?", (product_id,)
        ).fetchone()
    conn.close()
    return row is not None


def add_product(product_id, name, category, price, stock, low_stock_threshold, image_filename):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO products
            (product_id, name, category, price, stock, low_stock_threshold,
             image_filename, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (product_id, name, category, price, stock, low_stock_threshold,
          image_filename, now, now))
    conn.commit()
    conn.close()


def update_product(id, product_id, name, category, price, stock, low_stock_threshold, image_filename=None):
    """Update a product. If image_filename is None, the existing image
    (if any) is kept unchanged."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()

    if image_filename is not None:
        conn.execute("""
            UPDATE products
            SET product_id = ?, name = ?, category = ?, price = ?, stock = ?,
                low_stock_threshold = ?, image_filename = ?, updated_at = ?
            WHERE id = ?
        """, (product_id, name, category, price, stock, low_stock_threshold,
              image_filename, now, id))
    else:
        conn.execute("""
            UPDATE products
            SET product_id = ?, name = ?, category = ?, price = ?, stock = ?,
                low_stock_threshold = ?, updated_at = ?
            WHERE id = ?
        """, (product_id, name, category, price, stock, low_stock_threshold,
              now, id))

    conn.commit()
    conn.close()


def delete_product(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (id,))
    conn.commit()
    conn.close()


def search_products_for_sale(query):
    """Used by the POS page to look up products to add to the cart.
    Only returns products that currently have stock > 0."""
    conn = get_db_connection()
    like_term = f"%{query}%"
    rows = conn.execute("""
        SELECT id, product_id, name, category, price, stock, image_filename
        FROM products
        WHERE (product_id LIKE ? OR name LIKE ?) AND stock > 0
        ORDER BY name ASC
        LIMIT 20
    """, (like_term, like_term)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------
# Dashboard statistics
# ---------------------------------------------------------------------

def get_dashboard_stats():
    conn = get_db_connection()

    total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]

    total_stock = conn.execute("SELECT COALESCE(SUM(stock), 0) FROM products").fetchone()[0]

    low_stock = conn.execute(
        "SELECT COUNT(*) FROM products WHERE stock <= low_stock_threshold AND stock > 0"
    ).fetchone()[0]

    today = datetime.now().strftime("%Y-%m-%d")
    todays_sales = conn.execute("""
        SELECT COALESCE(SUM(total_amount), 0) FROM transactions
        WHERE transaction_date LIKE ?
    """, (f"{today}%",)).fetchone()[0]

    conn.close()

    return {
        "total_products": total_products,
        "total_stock": total_stock,
        "low_stock": low_stock,
        "todays_sales": round(todays_sales, 2),
    }


def get_sales_last_7_days():
    """Return sales totals for each of the last 7 days (oldest first),
    calculated from real transaction data in the database."""
    conn = get_db_connection()

    labels = []
    data = []

    for i in range(6, -1, -1):
        day = datetime.now() - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        label = day.strftime("%a")  # Mon, Tue, ...

        total = conn.execute("""
            SELECT COALESCE(SUM(total_amount), 0) FROM transactions
            WHERE transaction_date LIKE ?
        """, (f"{day_str}%",)).fetchone()[0]

        labels.append(label)
        data.append(round(total, 2))

    conn.close()
    return {"labels": labels, "data": data}


def get_products_by_category():
    """Return the number of products in each category, from real data."""
    conn = get_db_connection()

    labels = []
    data = []

    for cat in CATEGORIES:
        count = conn.execute(
            "SELECT COUNT(*) FROM products WHERE category = ?", (cat,)
        ).fetchone()[0]
        labels.append(cat)
        data.append(count)

    conn.close()
    return {"labels": labels, "data": data}


# ---------------------------------------------------------------------
# Sales / transactions
# ---------------------------------------------------------------------

def create_transaction(cart):
    """Process a completed sale.

    `cart` is a list of dicts like:
        [{"id": 1, "quantity": 2}, {"id": 3, "quantity": 1}]

    This function:
      1. Checks every item has enough stock.
      2. Creates the transaction row.
      3. Creates one transaction_items row per cart item.
      4. Deducts stock from each product.
    All of this happens in a single SQLite transaction, so if anything
    goes wrong, nothing is saved (the database stays consistent).
    """
    if not cart:
        raise ValueError("Cart is empty.")

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        total_amount = 0
        line_items = []

        for item in cart:
            product = cursor.execute(
                "SELECT * FROM products WHERE id = ?", (item["id"],)
            ).fetchone()

            if product is None:
                raise ValueError("A product in your cart no longer exists.")

            quantity = int(item["quantity"])

            if quantity <= 0:
                raise ValueError(f"Invalid quantity for {product['name']}.")

            if quantity > product["stock"]:
                raise ValueError(
                    f"Not enough stock for {product['name']} "
                    f"(only {product['stock']} left)."
                )

            subtotal = round(product["price"] * quantity, 2)
            total_amount += subtotal

            line_items.append({
                "product_id": product["product_id"],
                "product_name": product["name"],
                "quantity": quantity,
                "price": product["price"],
                "subtotal": subtotal,
                "internal_id": product["id"],
            })

        transaction_id = "TXN-" + uuid.uuid4().hex[:10].upper()
        transaction_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO transactions (transaction_id, total_amount, transaction_date)
            VALUES (?, ?, ?)
        """, (transaction_id, round(total_amount, 2), transaction_date))

        for line in line_items:
            cursor.execute("""
                INSERT INTO transaction_items
                    (transaction_id, product_id, product_name, quantity, price, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (transaction_id, line["product_id"], line["product_name"],
                  line["quantity"], line["price"], line["subtotal"]))

            cursor.execute("""
                UPDATE products SET stock = stock - ?, updated_at = ?
                WHERE id = ?
            """, (line["quantity"], transaction_date, line["internal_id"]))

        conn.commit()
        return transaction_id

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_all_transactions():
    conn = get_db_connection()
    transactions = conn.execute(
        "SELECT * FROM transactions ORDER BY transaction_date DESC"
    ).fetchall()
    conn.close()
    return transactions


def get_transaction_by_id(transaction_id):
    conn = get_db_connection()
    transaction = conn.execute(
        "SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,)
    ).fetchone()
    conn.close()
    return transaction


def get_transaction_items(transaction_id):
    conn = get_db_connection()
    items = conn.execute(
        "SELECT * FROM transaction_items WHERE transaction_id = ?", (transaction_id,)
    ).fetchall()
    conn.close()
    return items
