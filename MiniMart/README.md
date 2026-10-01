# MiniMart Inventory Management System

A local Inventory Management + Point of Sale (POS) web app for a small
convenience store, built as a college programming project.

**Backend:** Python + Flask
**Database:** SQLite
**Frontend:** HTML, CSS, JavaScript, Chart.js

---

## Features

- User Signup / Login / Logout (hashed passwords, session-based auth)
- Product management (add, edit, delete, view, image upload)
- Inventory tracking with In Stock / Low Stock / Out of Stock status
- Point-of-Sale page: search products, build a cart, complete a sale
- Automatic stock deduction when a sale is completed
- Transaction history with itemized details
- Dashboard with live statistics and two Chart.js graphs
  (Sales Overview - last 7 days, Products by Category)
- Search and category filtering on the Products page

---

## Project Structure

```
MiniMart/
│
├── app.py              # Flask routes (the main application)
├── database.py         # All SQLite database logic
├── auth.py             # Login/signup helpers, @login_required decorator
├── database.db         # SQLite database (auto-created on first run)
├── requirements.txt
├── README.md
│
├── templates/           # HTML pages (Jinja2 templates)
└── static/
    ├── css/style.css
    ├── js/script.js
    └── uploads/          # Uploaded product images are stored here
```

---

## Installation

1. **Create a virtual environment** (recommended):

   ```bash
   python -m venv venv
   ```

2. **Activate it:**

   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS / Linux:
     ```bash
     source venv/bin/activate
     ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**

   ```bash
   python app.py
   ```

5. **Open your browser** and go to:

   ```
   http://127.0.0.1:5000
   ```

### Optional but recommended: make the dashboard graphs work offline

The Dashboard page uses Chart.js to draw its two graphs. By default the
app tries to load Chart.js from the internet, so as long as you have a
connection when you open the Dashboard, the graphs will work with no
extra steps.

If you want the graphs to work with **no internet connection at all**
(recommended before a presentation, in case the venue's Wi-Fi is
unreliable), do this once:

1. Open this link in your browser:
   `https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js`
2. Save the page (Ctrl+S / right-click → Save As) as `chart.umd.min.js`
3. Put that file in `static/js/chart.umd.min.js` (same folder as
   `script.js`)

After that, the Dashboard graphs will work every time, with or without
internet.

The SQLite database (`database.db`) and the `static/uploads/` folder
are created automatically the first time you run the app. Five sample
products are added automatically the first time the products table is
empty, so the app isn't blank on first launch.

---

## How to Use

### 1. Create an account
Go to `/signup`, fill in your full name, username, email, and password
(passwords are hashed with `werkzeug.security` before being stored -
they are never saved as plain text).

### 2. Log in
Go to `/login` and sign in with your username or email and password.
You'll be redirected to the Dashboard.

### 3. Add products
From **Products**, click **+ Add Product**. Fill in the Product ID,
name, category, price, stock, and low-stock threshold, and optionally
upload a product image (png, jpg, jpeg, gif, webp).

### 4. Edit products
Click **Edit** next to any product to update its details or replace
its image. If you don't choose a new image, the existing one is kept.

### 5. Manage inventory
The **Inventory** page shows current stock and status (In Stock, Low
Stock, Out of Stock) for every product, calculated as
`stock <= low_stock_threshold`.

### 6. Process a sale
Go to **Sales**. Search for a product, click it to add it to the cart,
adjust quantities with the +/- buttons, and click **Complete Sale**.
Stock is automatically deducted, and you can't sell more than what's
available.

### 7. View transactions
The **Transactions** page lists every completed sale. Click **View**
on any transaction to see its itemized products, quantities, and
subtotals.

### 8. View the dashboard
The **Dashboard** shows Total Products, Total Stock, Low Stock count,
and Today's Sales, plus two live charts built from real database data:
a 7-day Sales Overview line graph and a Products by Category bar graph.

### 9. Log out
Click **Logout** in the sidebar to end your session.

---

## Notes for Presentation

- All SQL queries use parameterized statements (`?` placeholders) to
  prevent SQL injection.
- Uploaded images are renamed with `secure_filename()` plus a short
  random prefix, and only image extensions are allowed.
- Selling a product runs inside a single SQLite transaction: if
  anything fails partway through, all changes are rolled back so the
  database never ends up inconsistent.
- The app checks for an existing `database.db` on startup and only
  creates missing tables - it never deletes or overwrites existing
  data.
