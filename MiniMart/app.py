"""
app.py
-------
Main Flask application for the MiniMart Inventory Management System.

This file only handles ROUTING and request/response logic.
Database work lives in database.py, and login/authentication helpers
live in auth.py, so this file stays easy to read.
"""

import os
import uuid

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.utils import secure_filename

import database
from auth import (
    login_required, create_user, username_exists, email_exists,
    get_user_by_login, verify_password
)

app = Flask(__name__)
app.secret_key = "minimart-college-project-secret-key"  # fine for a local school project

UPLOAD_FOLDER = os.path.join("static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

CATEGORIES = database.CATEGORIES


def allowed_file(filename):
    """Check the file extension is one of the allowed image types."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_image(file):
    """Safely save an uploaded image and return its stored filename.
    Returns None if no valid file was provided."""
    if file and file.filename and allowed_file(file.filename):
        safe_name = secure_filename(file.filename)
        # Prefix with a short unique id so two products can't overwrite
        # each other's images if they happen to have the same filename.
        unique_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], unique_name))
        return unique_name
    return None


def delete_image_file(filename):
    """Remove an image from static/uploads/ if it exists."""
    if not filename:
        return
    path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass  # not critical if this fails


# ---------------------------------------------------------------------
# Home
# ---------------------------------------------------------------------

@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# ---------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []

        if not full_name or not username or not email or not password or not confirm_password:
            errors.append("Please fill in all fields.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if username and username_exists(username):
            errors.append("Username already exists.")
        if email and email_exists(email):
            errors.append("Email already exists.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("signup.html", full_name=full_name,
                                    username=username, email=email)

        create_user(full_name, username, email, password)
        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        user = get_user_by_login(identifier)

        if user and verify_password(user, password):
            session["user_id"] = user["id"]
            session["full_name"] = user["full_name"]
            return redirect(url_for("dashboard"))

        flash("Invalid username/email or password.", "error")
        return render_template("login.html", identifier=identifier)

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# ---------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():
    stats = database.get_dashboard_stats()
    sales_data = database.get_sales_last_7_days()
    category_data = database.get_products_by_category()
    return render_template(
        "dashboard.html",
        stats=stats,
        sales_data=sales_data,
        category_data=category_data,
    )


# ---------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------

@app.route("/products")
@login_required
def products():
    search = request.args.get("search", "").strip()
    category = request.args.get("category", "").strip()
    products_list = database.get_all_products(search=search or None, category=category or None)
    return render_template(
        "products.html",
        products=products_list,
        categories=CATEGORIES,
        search=search,
        selected_category=category,
    )


@app.route("/products/add", methods=["GET", "POST"])
@login_required
def add_product():
    if request.method == "POST":
        product_id = request.form.get("product_id", "").strip()
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        price_raw = request.form.get("price", "").strip()
        stock_raw = request.form.get("stock", "").strip()
        threshold_raw = request.form.get("low_stock_threshold", "5").strip()
        image_file = request.files.get("image")

        errors = []

        if not product_id or not name or not category or not price_raw or not stock_raw:
            errors.append("Please fill in all required fields.")

        price = stock = threshold = None
        try:
            price = float(price_raw)
            if price < 0:
                errors.append("Price cannot be negative.")
        except ValueError:
            errors.append("Price must be a valid number.")

        try:
            stock = int(stock_raw)
            if stock < 0:
                errors.append("Stock cannot be negative.")
        except ValueError:
            errors.append("Stock must be a whole number.")

        try:
            threshold = int(threshold_raw) if threshold_raw else 5
        except ValueError:
            threshold = 5

        if product_id and database.product_id_exists(product_id):
            errors.append("Product ID already exists.")

        if image_file and image_file.filename and not allowed_file(image_file.filename):
            errors.append("Please select a valid image file (png, jpg, jpeg, gif, webp).")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("add_product.html", categories=CATEGORIES, form=request.form)

        image_filename = save_uploaded_image(image_file)
        database.add_product(product_id, name, category, price, stock, threshold, image_filename)
        flash(f'Product "{name}" was added successfully.', "success")
        return redirect(url_for("products"))

    return render_template("add_product.html", categories=CATEGORIES, form={})


@app.route("/products/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_product(id):
    product = database.get_product_by_id(id)
    if product is None:
        flash("Product not found.", "error")
        return redirect(url_for("products"))

    if request.method == "POST":
        product_id = request.form.get("product_id", "").strip()
        name = request.form.get("name", "").strip()
        category = request.form.get("category", "").strip()
        price_raw = request.form.get("price", "").strip()
        stock_raw = request.form.get("stock", "").strip()
        threshold_raw = request.form.get("low_stock_threshold", "5").strip()
        image_file = request.files.get("image")

        errors = []

        if not product_id or not name or not category or not price_raw or not stock_raw:
            errors.append("Please fill in all required fields.")

        price = stock = threshold = None
        try:
            price = float(price_raw)
            if price < 0:
                errors.append("Price cannot be negative.")
        except ValueError:
            errors.append("Price must be a valid number.")

        try:
            stock = int(stock_raw)
            if stock < 0:
                errors.append("Stock cannot be negative.")
        except ValueError:
            errors.append("Stock must be a whole number.")

        try:
            threshold = int(threshold_raw) if threshold_raw else 5
        except ValueError:
            threshold = 5

        if product_id and database.product_id_exists(product_id, exclude_id=id):
            errors.append("Product ID already exists.")

        if image_file and image_file.filename and not allowed_file(image_file.filename):
            errors.append("Please select a valid image file (png, jpg, jpeg, gif, webp).")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("edit_product.html", product=product, categories=CATEGORIES)

        new_image_filename = None
        if image_file and image_file.filename:
            new_image_filename = save_uploaded_image(image_file)
            if new_image_filename:
                delete_image_file(product["image_filename"])

        database.update_product(id, product_id, name, category, price, stock,
                                 threshold, image_filename=new_image_filename)
        flash(f'Product "{name}" was updated successfully.', "success")
        return redirect(url_for("products"))

    return render_template("edit_product.html", product=product, categories=CATEGORIES)


@app.route("/products/delete/<int:id>", methods=["POST"])
@login_required
def delete_product(id):
    product = database.get_product_by_id(id)
    if product is None:
        flash("Product not found.", "error")
        return redirect(url_for("products"))

    delete_image_file(product["image_filename"])
    database.delete_product(id)
    flash(f'Product "{product["name"]}" was deleted.', "success")
    return redirect(url_for("products"))


@app.route("/products/<int:id>")
@login_required
def product_details(id):
    product = database.get_product_by_id(id)
    if product is None:
        flash("Product not found.", "error")
        return redirect(url_for("products"))
    return render_template("product_details.html", product=product)


# ---------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------

@app.route("/inventory")
@login_required
def inventory():
    products_list = database.get_all_products()
    return render_template("inventory.html", products=products_list)


# ---------------------------------------------------------------------
# Sales / POS
# ---------------------------------------------------------------------

@app.route("/sales")
@login_required
def sales():
    return render_template("sales.html")


@app.route("/api/products/search")
@login_required
def api_products_search():
    q = request.args.get("q", "").strip()
    results = database.search_products_for_sale(q)
    return jsonify(results)


@app.route("/sales/checkout", methods=["POST"])
@login_required
def checkout():
    data = request.get_json(silent=True) or {}
    cart = data.get("cart", [])

    try:
        transaction_id = database.create_transaction(cart)
        return jsonify({"success": True, "transaction_id": transaction_id})
    except ValueError as e:
        return jsonify({"success": False, "message": str(e)}), 400
    except Exception:
        return jsonify({"success": False, "message": "Something went wrong while processing the sale."}), 500


# ---------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------

@app.route("/transactions")
@login_required
def transactions():
    transactions_list = database.get_all_transactions()
    return render_template("transactions.html", transactions=transactions_list)


@app.route("/transactions/<transaction_id>")
@login_required
def transaction_details(transaction_id):
    transaction = database.get_transaction_by_id(transaction_id)
    if transaction is None:
        flash("Transaction not found.", "error")
        return redirect(url_for("transactions"))

    items = database.get_transaction_items(transaction_id)
    return render_template("transaction_details.html", transaction=transaction, items=items)


# ---------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------

if __name__ == "__main__":
    database.init_db()
    app.run(debug=True)
