"""
auth.py
--------
Authentication helpers for the MiniMart Inventory Management System.

Passwords are never stored in plain text - werkzeug.security handles
the hashing and verification for us.
"""

from functools import wraps
from datetime import datetime

from flask import session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_db_connection


def login_required(f):
    """Decorator for routes that should only be reachable while logged in.

    Usage:
        @app.route("/dashboard")
        @login_required
        def dashboard():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def username_exists(username):
    conn = get_db_connection()
    row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return row is not None


def email_exists(email):
    conn = get_db_connection()
    row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row is not None


def create_user(full_name, username, email, password):
    """Hash the password and insert a new user row."""
    password_hash = generate_password_hash(password)
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO users (full_name, username, email, password_hash, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (full_name, username, email, password_hash, created_at))
    conn.commit()
    conn.close()


def get_user_by_login(identifier):
    """Find a user by username OR email - used on the login page,
    since the user can type either one."""
    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (identifier, identifier)
    ).fetchone()
    conn.close()
    return user


def verify_password(user, password):
    """Check a plain-text password against the stored hash."""
    return check_password_hash(user["password_hash"], password)
