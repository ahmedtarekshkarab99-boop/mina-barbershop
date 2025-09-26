import os
import sqlite3
import shutil
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any


APP_DIR = os.path.join(os.getcwd(), "mina_al_arabi")
DATA_DIR = os.path.join(APP_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "mina.db")
BACKUPS_DIR = os.path.join(DATA_DIR, "backups")
RECEIPTS_DIR = os.path.join(DATA_DIR, "receipts")


class Database:
    def __init__(self, path: str = DB_PATH):
        self.path = path
        os.makedirs(DATA_DIR, exist_ok=True)
        os.makedirs(BACKUPS_DIR, exist_ok=True)
        os.makedirs(RECEIPTS_DIR, exist_ok=True)

    def connect(self):
        return sqlite3.connect(self.path)

    def ensure_schema(self):
        with self.connect() as conn:
            c = conn.cursor()

            # Employees
            c.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
            """)

            # Services
            c.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                price REAL NOT NULL
            )
            """)

            # Products (Inventory)
            c.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                price REAL NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 0
            )
            """)

            # Sales
            c.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                employee_id INTEGER,
                customer_name TEXT,
                is_shop INTEGER NOT NULL DEFAULT 0, -- 1 if buyer is shop
                total REAL NOT NULL,
                discount_percent INTEGER NOT NULL DEFAULT 0,
                type TEXT NOT NULL, -- 'service' or 'product'
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            )
            """)

            c.execute("""
            CREATE TABLE IF NOT EXISTS sale_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                unit_price REAL NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY(sale_id) REFERENCES sales(id)
            )
            """)

            # Expenses
            c.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                note TEXT
            )
            """)

            # Attendance
            c.execute("""
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                check_in TEXT,
                check_out TEXT,
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            )
            """)

            # Loans
            c.execute("""
            CREATE TABLE IF NOT EXISTS loans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                note TEXT,
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            )
            """)
            conn.commit()

    # General helpers
    def backup(self) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = os.path.join(BACKUPS_DIR, f"mina_backup_{ts}.db")
        shutil.copyfile(self.path, dest)
        return dest

    # Employees
    def add_employee(self, name: str):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO employees(name) VALUES (?)", (name,))
            conn.commit()

    def list_employees(self) -> List[Tuple[int, str]]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT id, name FROM employees ORDER BY name")
            return c.fetchall()

    # Services
    def add_service(self, name: str, price: float):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO services(name, price) VALUES (?, ?)", (name, price))
            conn.commit()

    def list_services(self) -> List[Tuple[int, str, float]]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, price FROM services ORDER BY name")
            return c.fetchall()

    # Products
    def add_product(self, name: str, price: float, quantity: int):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT OR IGNORE INTO products(name, price, quantity) VALUES (?, ?, ?)",
                (name, price, quantity)
            )
            conn.commit()

    def update_product_qty(self, product_id: int, delta: int):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("UPDATE products SET quantity = quantity + ? WHERE id = ?", (delta, product_id))
            conn.commit()

    def list_products(self) -> List[Tuple[int, str, float, int]]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, price, quantity FROM products ORDER BY name")
            return c.fetchall()

    def get_product_by_name(self, name: str) -> Optional[Tuple[int, str, float, int]]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, price, quantity FROM products WHERE name = ?", (name,))
            return c.fetchone()

    # Sales and items
    def create_sale(self, date: str, employee_id: Optional[int], customer_name: Optional[str],
                    is_shop: int, total: float, discount_percent: int, sale_type: str) -> int:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO sales(date, employee_id, customer_name, is_shop, total, discount_percent, type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (date, employee_id, customer_name, is_shop, total, discount_percent, sale_type))
            sale_id = c.lastrowid
            conn.commit()
            return sale_id

    def add_sale_item(self, sale_id: int, item_name: str, unit_price: float, quantity: int = 1):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO sale_items(sale_id, item_name, unit_price, quantity)
            VALUES (?, ?, ?, ?)
            """, (sale_id, item_name, unit_price, quantity))
            conn.commit()

    def list_sale_items(self, sale_id: int) -> List[Tuple[int, int, str, float, int]]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT id, sale_id, item_name, unit_price, quantity FROM sale_items WHERE sale_id = ?", (sale_id,))
            return c.fetchall()

    # Expenses
    def add_expense(self, category: str, amount: float, note: Optional[str] = None, date: Optional[str] = None):
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO expenses(date, category, amount, note)
            VALUES (?, ?, ?, ?)
            """, (date, category, amount, note))
            conn.commit()

    def list_expenses(self) -> List[Tuple[int, str, str, float, Optional[str]]]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT id, date, category, amount, note FROM expenses ORDER BY date DESC")
            return c.fetchall()

    # Attendance
    def check_in(self, employee_id: int):
        now = datetime.now().strftime("%Y-%m-%d")
        time = datetime.now().strftime("%H:%M:%S")
        with self.connect() as conn:
            c = conn.cursor()
            # If entry exists for today, update check_in
            c.execute("""
            INSERT INTO attendance(employee_id, date, check_in)
            VALUES (?, ?, ?)
            """, (employee_id, now, time))
            conn.commit()

    def check_out(self, employee_id: int):
        now = datetime.now().strftime("%Y-%m-%d")
        time = datetime.now().strftime("%H:%M:%S")
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            UPDATE attendance
            SET check_out = ?
            WHERE employee_id = ? AND date = ?
            """, (time, employee_id, now))
            conn.commit()

    def add_loan(self, employee_id: int, amount: float, note: Optional[str] = None):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO loans(employee_id, date, amount, note)
            VALUES (?, ?, ?, ?)
            """, (employee_id, now, amount, note))
            conn.commit()

    def list_attendance_for_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            SELECT a.date, e.name, a.check_in, a.check_out
            FROM attendance a
            JOIN employees e ON e.id = a.employee_id
            WHERE substr(a.date,1,4) = ? AND substr(a.date,6,2) = ?
            ORDER BY a.date DESC
            """, (str(year), f"{month:02d}"))
            rows = c.fetchall()
            return [{"date": r[0], "employee": r[1], "check_in": r[2], "check_out": r[3]} for r in rows]