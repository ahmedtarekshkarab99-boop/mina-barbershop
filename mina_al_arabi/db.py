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
                quantity INTEGER NOT NULL DEFAULT 0,
                purchase_price REAL
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
                buyer_type TEXT NOT NULL DEFAULT 'customer',
                cleared INTEGER NOT NULL DEFAULT 0,
                material_deduction REAL NOT NULL DEFAULT 0,
                shift_id INTEGER,
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
                note TEXT,
                shift_id INTEGER
            )
            """)

            # Suppliers
            c.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                phone TEXT,
                notes TEXT
            )
            """)
            c.execute("""
            CREATE TABLE IF NOT EXISTS supplier_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                paid_amount REAL NOT NULL DEFAULT 0,
                FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
            )
            """)
            c.execute("""
            CREATE TABLE IF NOT EXISTS supplier_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                note TEXT,
                FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
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
                manual INTEGER NOT NULL DEFAULT 0,
                note TEXT,
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
                cleared INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            )
            """)

            # Shifts
            c.execute("""
            CREATE TABLE IF NOT EXISTS shifts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shift_number INTEGER NOT NULL,
                cashier_name TEXT NOT NULL,
                opened_at TEXT NOT NULL,
                closed_at TEXT,
                active INTEGER NOT NULL DEFAULT 1
            )
            """)

            # Migrations (idempotent)
            for stmt in [
                "ALTER TABLE sales ADD COLUMN buyer_type TEXT NOT NULL DEFAULT 'customer'",
                "ALTER TABLE sales ADD COLUMN cleared INTEGER NOT NULL DEFAULT 0",
                "ALTER TABLE loans ADD COLUMN cleared INTEGER NOT NULL DEFAULT 0",
                "ALTER TABLE sales ADD COLUMN material_deduction REAL NOT NULL DEFAULT 0",
                "ALTER TABLE sales ADD COLUMN shift_id INTEGER",
                "ALTER TABLE expenses ADD COLUMN shift_id INTEGER",
                "ALTER TABLE attendance ADD COLUMN manual INTEGER NOT NULL DEFAULT 0",
                "ALTER TABLE attendance ADD COLUMN note TEXT",
                "ALTER TABLE products ADD COLUMN purchase_price REAL",
            ]:
                try:
                    c.execute(stmt)
                except Exception:
                    pass

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

    def delete_employee_by_name(self, name: str):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM employees WHERE name = ?", (name,))
            conn.commit()

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

    def delete_service_by_name(self, name: str):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM services WHERE name = ?", (name,))
            conn.commit()

    def update_service_price(self, name: str, new_price: float):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("UPDATE services SET price = ? WHERE name = ?", (new_price, name))
            conn.commit()

    # Products
    def add_product(self, name: str, price: float, quantity: int, purchase_price: Optional[float] = None):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute(
                "INSERT OR IGNORE INTO products(name, price, quantity, purchase_price) VALUES (?, ?, ?, ?)",
                (name, price, quantity, purchase_price)
            )
            conn.commit()

    def update_product_qty(self, product_id: int, delta: int):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("UPDATE products SET quantity = quantity + ? WHERE id = ?", (delta, product_id))
            conn.commit()

    def update_product_price(self, product_id: int, new_price: float):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("UPDATE products SET price = ? WHERE id = ?", (new_price, product_id))
            conn.commit()

    def list_products(self) -> List[Tuple[int, str, float, int, Optional[float]]]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, price, quantity, purchase_price FROM products ORDER BY name")
            return c.fetchall()

    def get_product_by_name(self, name: str) -> Optional[Tuple[int, str, float, int, Optional[float]]]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, price, quantity, purchase_price FROM products WHERE name = ?", (name,))
            return c.fetchone()

    def delete_product(self, product_id: int):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM products WHERE id = ?", (product_id,))
            conn.commit()

    # Sales and items
    def _normalize_date_for_shift(self, date: str, shift_id: Optional[int]) -> str:
        """If a shift_id is provided, force the date's day to the shift's opened_at day, preserving time."""
        if not shift_id:
            return date
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT opened_at FROM shifts WHERE id = ?", (shift_id,))
            row = c.fetchone()
            if not row or not row[0]:
                return date
            opened_at = row[0]  # "YYYY-MM-DD HH:MM:SS"
            shift_day = opened_at[:10]
        # Preserve time component from provided date (if any)
        try:
            time_part = date.split(" ")[1]
        except Exception:
            time_part = "00:00:00"
        return f"{shift_day} {time_part}"

    def create_sale(self, date: str, employee_id: Optional[int], customer_name: Optional[str],
                    is_shop: int, total: float, discount_percent: int, sale_type: str,
                    buyer_type: str = "customer", material_deduction: float = 0.0,
                    shift_id: Optional[int] = None, cashier_name: Optional[str] = None) -> int:
        date = self._normalize_date_for_shift(date, shift_id)
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO sales(date, employee_id, customer_name, is_shop, total, discount_percent, type, buyer_type, material_deduction, shift_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (date, employee_id, customer_name, is_shop, total, discount_percent, sale_type, buyer_type, material_deduction, shift_id))
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

    def list_sales_by_employee_on_date(self, employee_id: int, date_str: str) -> List[Dict[str, Any]]:
        """Return sales (both services and products) by an employee on a specific YYYY-MM-DD date, excluding cleared entries."""
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            SELECT id, date, total, discount_percent, type, is_shop, buyer_type, material_deduction
            FROM sales
            WHERE employee_id = ? AND substr(date,1,10) = ? AND cleared = 0
            ORDER BY date ASC
            """, (employee_id, date_str))
            rows = c.fetchall()
            return [
                {
                    "id": r[0],
                    "date": r[1],
                    "total": r[2],
                    "discount_percent": r[3],
                    "type": r[4],
                    "is_shop": r[5],
                    "buyer_type": r[6],
                    "material_deduction": r[7],
                } for r in rows
            ]

    def list_sales_by_employee_in_month(self, employee_id: int, year: int, month: int) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            SELECT id, date, total, discount_percent, type, is_shop, buyer_type, material_deduction
            FROM sales
            WHERE employee_id = ? AND substr(date,1,4) = ? AND substr(date,6,2) = ? AND cleared = 0
            ORDER BY date ASC
            """, (employee_id, str(year), f"{month:02d}"))
            rows = c.fetchall()
            return [
                {
                    "id": r[0],
                    "date": r[1],
                    "total": r[2],
                    "discount_percent": r[3],
                    "type": r[4],
                    "is_shop": r[5],
                    "buyer_type": r[6],
                    "material_deduction": r[7],
                } for r in rows
            ]

    # Expenses
    def add_expense(self, category: str, amount: float, note: Optional[str] = None, date: Optional[str] = None, shift_id: Optional[int] = None):
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date = self._normalize_date_for_shift(date, shift_id)
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO expenses(date, category, amount, note, shift_id)
            VALUES (?, ?, ?, ?, ?)
            """, (date, category, amount, note, shift_id))
            conn.commit()

    # Shift helpers
    def get_active_shift(self) -> Optional[Tuple[int, int, str, str, Optional[str], int]]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            SELECT id, shift_number, cashier_name, opened_at, closed_at, active
            FROM shifts
            WHERE active = 1
            ORDER BY id DESC
            LIMIT 1
            """)
            row = c.fetchone()
            return row if row else None

    def open_shift(self, cashier_name: str) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.connect() as conn:
            c = conn.cursor()
            # Next shift number
            c.execute("SELECT COALESCE(MAX(shift_number), 0) FROM shifts")
            next_num = (c.fetchone()[0] or 0) + 1
            c.execute("""
            INSERT INTO shifts(shift_number, cashier_name, opened_at, active)
            VALUES (?, ?, ?, 1)
            """, (next_num, cashier_name, now))
            sid = c.lastrowid
            conn.commit()
            return sid

    def close_shift(self, shift_id: int) -> None:
        closed = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            UPDATE shifts SET closed_at = ?, active = 0 WHERE id = ?
            """, (closed, shift_id))
            conn.commit()

    def shift_summary(self, shift_id: int) -> Dict[str, Any]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT shift_number, cashier_name, opened_at, closed_at FROM shifts WHERE id = ?", (shift_id,))
            sh = c.fetchone()
            if not sh:
                return {}
            shift_number, cashier_name, opened_at, closed_at = sh
            # Treat shift as the day of opened_at regardless of midnight crossover
            shift_day = opened_at[:10]

            # Sales totals (visible discount effect and counts)
            c.execute("""
            SELECT COALESCE(SUM(total), 0), COALESCE(SUM(total * (discount_percent/100.0)), 0),
                   COALESCE(SUM(material_deduction), 0), COUNT(*)
            FROM sales
            WHERE substr(date,1,10) = ?
            """, (shift_day,))
            sum_total, sum_disc_amt, sum_mat_ded, inv_count = c.fetchone()
            total_after_discount = float(sum_total or 0) - float(sum_disc_amt or 0)

            # Expenses totals for the same day
            c.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE substr(date,1,10) = ?
            """, (shift_day,))
            exp_total = c.fetchone()[0] or 0

            # Duration
            try:
                dt_open = datetime.strptime(opened_at, "%Y-%m-%d %H:%M:%S")
                dt_close = datetime.strptime(closed_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
                delta = dt_close - dt_open
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60
                duration = f"{hours:02d}:{minutes:02d}"
            except Exception:
                duration = ""

            return {
                "shift_number": shift_number,
                "cashier_name": cashier_name,
                "opened_at": opened_at,
                "closed_at": closed_at,
                "duration": duration,
                "total_sales": float(total_after_discount or 0),
                "invoice_count": int(inv_count or 0),
                "customer_discounts": float(sum_disc_amt or 0),
                "material_deductions": float(sum_mat_ded or 0),
                "total_expenses": float(exp_total or 0),
            }

    def list_expenses(self) -> List[Tuple[int, str, str, float, Optional[str]]]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT id, date, category, amount, note FROM expenses ORDER BY date DESC")
            return c.fetchall()

    # Suppliers
    def add_supplier(self, name: str, phone: Optional[str] = None, notes: Optional[str] = None) -> int:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("INSERT OR IGNORE INTO suppliers(name, phone, notes) VALUES (?, ?, ?)", (name, phone, notes))
            # fetch id
            c.execute("SELECT id FROM suppliers WHERE name = ?", (name,))
            row = c.fetchone()
            conn.commit()
            return int(row[0]) if row else 0

    def list_suppliers(self) -> List[Tuple[int, str, Optional[str], Optional[str]]]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT id, name, phone, notes FROM suppliers ORDER BY name ASC")
            return c.fetchall()

    def add_supplier_invoice(self, supplier_id: int, total_amount: float, paid_amount: float = 0.0, date: Optional[str] = None) -> int:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO supplier_invoices(supplier_id, date, total_amount, paid_amount)
            VALUES (?, ?, ?, ?)
            """, (supplier_id, date, total_amount, paid_amount))
            inv_id = c.lastrowid
            conn.commit()
            return inv_id

    def add_supplier_payment(self, supplier_id: int, amount: float, note: Optional[str] = None, date: Optional[str] = None) -> int:
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO supplier_payments(supplier_id, date, amount, note)
            VALUES (?, ?, ?, ?)
            """, (supplier_id, date, amount, note))
            pay_id = c.lastrowid
            # Sync to expenses (category: دفعات الموردين)
            c.execute("""
            INSERT INTO expenses(date, category, amount, note, shift_id)
            VALUES (?, ?, ?, ?, NULL)
            """, (date, "دفعات الموردين", amount, f"مورد: {self.get_supplier_name(supplier_id)}" if supplier_id else note))
            conn.commit()
            return pay_id

    def get_supplier_name(self, supplier_id: int) -> Optional[str]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM suppliers WHERE id = ?", (supplier_id,))
            row = c.fetchone()
            return row[0] if row else None

    def supplier_summary(self, supplier_id: int) -> Dict[str, Any]:
        with self.connect() as conn:
            c = conn.cursor()
            # totals for invoices
            c.execute("""
            SELECT COALESCE(SUM(total_amount), 0), COALESCE(SUM(paid_amount), 0)
            FROM supplier_invoices WHERE supplier_id = ?
            """, (supplier_id,))
            inv_tot, inv_paid = c.fetchone()
            # totals for payments (installments)
            c.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM supplier_payments WHERE supplier_id = ?
            """, (supplier_id,))
            pay_tot = c.fetchone()[0] or 0
            total_invoices = float(inv_tot or 0)
            total_invoice_paid = float(inv_paid or 0)
            total_payments = float(pay_tot or 0)
            remaining = total_invoices - total_invoice_paid - total_payments
            return {
                "total_invoices": total_invoices,
                "total_invoice_paid": total_invoice_paid,
                "total_payments": total_payments,
                "remaining": remaining if remaining > 0 else 0.0,
            }

    def delete_expense_by_id(self, expense_id: int):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            conn.commit()

    def delete_all_expenses(self):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM expenses")
            conn.commit()

    # Attendance
    def check_in(self, employee_id: int):
        now_time = datetime.now().strftime("%H:%M:%S")
        # Attach to active shift start day if present
        sh = self.get_active_shift()
        if sh:
            shift_id = sh[0]
            opened_at = sh[3]  # "YYYY-MM-DD HH:MM:SS"
            shift_day = opened_at[:10]
            date_val = f"{shift_day}"
        else:
            shift_id = None
            date_val = datetime.now().strftime("%Y-%m-%d")
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO attendance(employee_id, date, check_in, manual, note)
            VALUES (?, ?, ?, 0, NULL)
            """, (employee_id, date_val, now_time))
            # Optionally store shift_id if column exists
            try:
                c.execute("ALTER TABLE attendance ADD COLUMN shift_id INTEGER")
            except Exception:
                pass
            try:
                c.execute("UPDATE attendance SET shift_id = ? WHERE id = (SELECT MAX(id) FROM attendance)")
            except Exception:
                pass
            conn.commit()

    def check_out(self, employee_id: int):
        # Count as same day as check-in even if after midnight:
        # We update the latest open record for this employee (no check_out yet)
        now_time = datetime.now().strftime("%H:%M:%S")
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            UPDATE attendance
            SET check_out = ?
            WHERE employee_id = ? AND check_out IS NULL
            ORDER BY date DESC, id DESC
            """, (now_time, employee_id))
            conn.commit()

    def delete_all_attendance(self):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM attendance")
            conn.commit()

    # Manual attendance and editing
    def add_manual_attendance(self, employee_id: int, date: str, check_in: str, check_out: Optional[str] = None, note: Optional[str] = None):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO attendance(employee_id, date, check_in, check_out, manual, note)
            VALUES (?, ?, ?, ?, 1, ?)
            """, (employee_id, date, check_in, check_out, note))
            conn.commit()

    def edit_attendance(self, record_id: int, check_in: Optional[str] = None, check_out: Optional[str] = None, note: Optional[str] = None, manual: Optional[int] = None):
        with self.connect() as conn:
            c = conn.cursor()
            fields = []
            params = []
            if check_in is not None:
                fields.append("check_in = ?")
                params.append(check_in)
            if check_out is not None:
                fields.append("check_out = ?")
                params.append(check_out)
            if note is not None:
                fields.append("note = ?")
                params.append(note)
            if manual is not None:
                fields.append("manual = ?")
                params.append(int(bool(manual)))
            if not fields:
                return
            params.append(record_id)
            c.execute(f"UPDATE attendance SET {', '.join(fields)} WHERE id = ?", params)
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

    def list_loans_by_employee_on_date(self, employee_id: int, date_str: str) -> List[Tuple[int, str, float, Optional[str]]]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            SELECT id, date, amount, note
            FROM loans
            WHERE employee_id = ? AND substr(date,1,10) = ? AND cleared = 0
            ORDER BY date ASC
            """, (employee_id, date_str))
            return c.fetchall()

    def list_loans_by_employee_in_month(self, employee_id: int, year: int, month: int) -> List[Tuple[int, str, float, Optional[str]]]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            SELECT id, date, amount, note FROM loans
            WHERE employee_id = ? AND substr(date,1,4) = ? AND substr(date,6,2) = ? AND cleared = 0
            ORDER BY date ASC
            """, (employee_id, str(year), f"{month:02d}"))
            return c.fetchall()

    def list_attendance_for_month(self, year: int, month: int) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            SELECT a.id, a.date, e.name, a.check_in, a.check_out, a.employee_id, a.manual, a.note
            FROM attendance a
            JOIN employees e ON e.id = a.employee_id
            WHERE substr(a.date,1,4) = ? AND substr(a.date,6,2) = ?
            ORDER BY a.date DESC, a.id DESC
            """, (str(year), f"{month:02d}"))
            rows = c.fetchall()
            return [{
                "id": r[0],
                "date": r[1],
                "employee": r[2],
                "check_in": r[3],
                "check_out": r[4],
                "employee_id": r[5],
                "manual": int(r[6] or 0),
                "note": r[7] or None
            } for r in rows]

    # Account clearing helpers
    def delete_sales_and_items_by_employee(self, employee_id: int):
        """Clear only employee deductions (sales where buyer_type='employee'), not service revenue."""
        with self.connect() as conn:
            c = conn.cursor()
            # Find all sales ids for this employee where the employee is the buyer (deductions)
            c.execute("SELECT id FROM sales WHERE employee_id = ? AND buyer_type = 'employee'", (employee_id,))
            sale_ids = [row[0] for row in c.fetchall()]
            if sale_ids:
                # Delete sale_items tied to those sales
                c.executemany("DELETE FROM sale_items WHERE sale_id = ?", [(sid,) for sid in sale_ids])
                # Delete those sales
                c.executemany("DELETE FROM sales WHERE id = ?", [(sid,) for sid in sale_ids])
            conn.commit()

    def delete_loans_by_employee(self, employee_id: int):
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("DELETE FROM loans WHERE employee_id = ?", (employee_id,))
            conn.commit()

    # Admin report helpers
    def sum_services_in_month(self, year: int, month: int) -> float:
        """Gross services total (before discount)."""
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            SELECT COALESCE(SUM(total), 0)
            FROM sales
            WHERE type = 'service' AND substr(date,1,4) = ? AND substr(date,6,2) = ?
            """, (str(year), f"{month:02d}"))
            val = c.fetchone()[0]
            return float(val or 0)

    def sum_services_net_in_month(self, year: int, month: int) -> float:
        """Net services total (after visible discount)."""
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            SELECT COALESCE(SUM(total * (1 - discount_percent/100.0)), 0)
            FROM sales
            WHERE type = 'service' AND substr(date,1,4) = ? AND substr(date,6,2) = ?
            """, (str(year), f"{month:02d}"))
            val = c.fetchone()[0]
            return float(val or 0)

    def sum_products_in_month(self, year: int, month: int) -> float:
        """Gross products total (before discount) for customer purchases."""
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            SELECT COALESCE(SUM(total), 0)
            FROM sales
            WHERE type = 'product' AND buyer_type = 'customer' AND substr(date,1,4) = ? AND substr(date,6,2) = ?
            """, (str(year), f"{month:02d}"))
            val = c.fetchone()[0]
            return float(val or 0)

    def sum_products_net_in_month(self, year: int, month: int) -> float:
        """Net products total (after visible discount) for customer purchases."""
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            SELECT COALESCE(SUM(total * (1 - discount_percent/100.0)), 0)
            FROM sales
            WHERE type = 'product' AND buyer_type = 'customer' AND substr(date,1,4) = ? AND substr(date,6,2) = ?
            """, (str(year), f"{month:02d}"))
            val = c.fetchone()[0]
            return float(val or 0)

    def sum_expenses_category_in_month(self, category: str, year: int, month: int) -> float:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM expenses
            WHERE category = ? AND substr(date,1,4) = ? AND substr(date,6,2) = ?
            """, (category, str(year), f"{month:02d}"))
            val = c.fetchone()[0]
            return float(val or 0)

    def sum_material_deductions_in_period(self, start_date: str, end_date: str) -> float:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            SELECT COALESCE(SUM(material_deduction), 0)
            FROM sales
            WHERE date BETWEEN ? AND ?
            """, (start_date, end_date))
            val = c.fetchone()[0]
            return float(val or 0)

    def sum_material_deductions_in_month(self, year: int, month: int) -> float:
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            SELECT COALESCE(SUM(material_deduction), 0)
            FROM sales
            WHERE substr(date,1,4) = ? AND substr(date,6,2) = ?
            """, (str(year), f"{month:02d}"))
            val = c.fetchone()[0]
            return float(val or 0)

    def list_shop_purchases_in_month(self, year: int, month: int):
        """Return rows of (date, item_name, unit_price, qty) for shop buyer product sales."""
        with self.connect() as conn:
            c = conn.cursor()
            c.execute("""
            SELECT s.date, si.item_name, si.unit_price, si.quantity
            FROM sales s
            JOIN sale_items si ON si.sale_id = s.id
            WHERE s.type = 'product' AND s.buyer_type = 'shop'
              AND substr(s.date,1,4) = ? AND substr(s.date,6,2) = ?
            ORDER BY s.date ASC
            """, (str(year), f"{month:02d}"))
            return c.fetchall()

    def delete_shop_data_in_month(self, year: int, month: int):
        """Delete shop buyer product sales and 'مشتريات للمحل' expenses for the month."""
        with self.connect() as conn:
            c = conn.cursor()
            # Delete expenses for shop purchases
            c.execute("""
            DELETE FROM expenses
            WHERE category = 'مشتريات للمحل' AND substr(date,1,4) = ? AND substr(date,6,2) = ?
            """, (str(year), f"{month:02d}"))

            # Find sales ids for shop buyer product sales
            c.execute("""
            SELECT id FROM sales
            WHERE type = 'product' AND buyer_type = 'shop'
              AND substr(date,1,4) = ? AND substr(date,6,2) = ?
            """, (str(year), f"{month:02d}"))
            sale_ids = [row[0] for row in c.fetchall()]
            if sale_ids:
                c.executemany("DELETE FROM sale_items WHERE sale_id = ?", [(sid,) for sid in sale_ids])
                c.executemany("DELETE FROM sales WHERE id = ?", [(sid,) for sid in sale_ids])
            conn.commit()