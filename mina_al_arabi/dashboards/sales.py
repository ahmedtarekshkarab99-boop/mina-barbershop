from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget,
    QListWidgetItem, QMessageBox, QAbstractItemView, QScrollArea, QGridLayout, QComboBox, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from datetime import datetime
import os

from mina_al_arabi.db import Database, RECEIPTS_DIR
from mina_al_arabi.printing import print_receipt

def format_amount(amount: float) -> str:
    return f"{int(round(amount))}"

def receipts_dir() -> str:
    # Use central data directory from db.py to be consistent in frozen builds
    base = RECEIPTS_DIR
    try:
        os.makedirs(base, exist_ok=True)
    except Exception:
        pass
    return base


class SalesDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        root = QHBoxLayout(self)

        # Left: Products area (larger)
        left = QVBoxLayout()
        title_products = QLabel("المنتجات")
        title_products.setFont(self.header_font)
        left.addWidget(title_products)

        # Search + refresh
        ctrl_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث عن منتج...")
        self.search_input.textChanged.connect(self.load_products)
        ctrl_row.addWidget(self.search_input)
        refresh_btn = QPushButton("تحديث المنتجات")
        refresh_btn.setFont(self.body_font)
        refresh_btn.clicked.connect(self.load_products)
        ctrl_row.addWidget(refresh_btn)
        left.addLayout(ctrl_row)

        self.products_area = QScrollArea()
        self.products_area.setWidgetResizable(True)
        self.products_container = QWidget()
        self.products_grid = QGridLayout(self.products_container)
        self.products_grid.setSpacing(12)
        self.products_area.setWidget(self.products_container)
        # Prominence
        self.products_area.setMinimumHeight(500)
        left.addWidget(self.products_area)

        # Right: Invoice area
        right = QVBoxLayout()
        title_invoice = QLabel("الفاتورة")
        title_invoice.setFont(self.header_font)
        right.addWidget(title_invoice)

        # Invoice type selector
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("نوع الفاتورة:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["عميل", "للمحل", "للموظف"])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode_combo)
        right.addLayout(mode_row)

        buyer_layout = QHBoxLayout()
        buyer_layout.addWidget(QLabel("اسم العميل"))
        self.customer_input = QLineEdit()
        self.customer_input.setFont(self.body_font)
        buyer_layout.addWidget(self.customer_input)
        buyer_layout.addWidget(QLabel("الموظف"))
        self.employee_combo = QComboBox()
        buyer_layout.addWidget(self.employee_combo)
        right.addLayout(buyer_layout)

        self.invoice_list = QListWidget()
        self.invoice_list.setFont(self.body_font)
        self.invoice_list.setSelectionMode(QAbstractItemView.MultiSelection)
        right.addWidget(self.invoice_list)

        action_row = QHBoxLayout()
        remove_btn = QPushButton("حذف المحدد")
        remove_btn.setFont(self.body_font)
        remove_btn.clicked.connect(self.remove_selected_invoice_item)
        action_row.addWidget(remove_btn)
        right.addLayout(action_row)

        totals_layout = QVBoxLayout()
        self.total_label = QLabel("الإجمالي: 0 ج.م")
        self.total_label.setFont(self.body_font)
        totals_layout.addWidget(self.total_label)

        disc_row = QHBoxLayout()
        disc_row.addWidget(QLabel("الخصم:"))
        self.discount_combo = QComboBox()
        self.discount_combo.addItems(["بدون خصم", "10%", "20%", "30%", "40%", "50%"])
        self.discount_combo.currentIndexChanged.connect(self._update_total)
        disc_row.addWidget(self.discount_combo)

        mat_row = QHBoxLayout()
        mat_row.addWidget(QLabel("خصم مواد (مخفي):"))
        self.material_deduction_input = QSpinBox()
        self.material_deduction_input.setMaximum(1000000)
        mat_row.addWidget(self.material_deduction_input)

        totals_layout.addLayout(disc_row)
        totals_layout.addLayout(mat_row)
        right.addLayout(totals_layout)

        self.submit_btn = QPushButton("طباعة إيصال")
        self.submit_btn.setFont(self.body_font)
        self.submit_btn.clicked.connect(self._submit_invoice)
        right.addWidget(self.submit_btn)

        # Width ratio 3:1
        root.addLayout(left, 3)
        root.addLayout(right, 1)

        self._load_employees()
        self.load_products()
        self._on_mode_changed()

    def _on_mode_changed(self):
        mode = self.mode_combo.currentText()
        if mode == "للمحل":
            self.submit_btn.setText("تسجيل الفاتورة")
        else:
            self.submit_btn.setText("طباعة إيصال")

    def _load_employees(self):
        self.employee_combo.clear()
        try:
            rows = self.db.list_employees()
            for eid, name in rows:
                self.employee_combo.addItem(name, eid)
        except Exception:
            pass

    def _clear_products_grid(self):
        while self.products_grid.count():
            item = self.products_grid.itemAt(0)
            w = item.widget()
            self.products_grid.removeItem(item)
            if w:
                w.setParent(None)

    def load_products(self):
        self._clear_products_grid()
        query = (self.search_input.text().strip() or "").lower()
        try:
            products = self.db.list_products()
        except Exception:
            products = []
        products = list(reversed(products))
        row, col = 0, 0
        for row_data in products:
            # row_data may be (id, name, price, qty, purchase_price)
            pid = row_data[0]
            name = row_data[1]
            price = row_data[2]
            qty = row_data[3]
            if query and (query not in name.lower()):
                continue
            label_text = f"{name}\n{format_amount(price)} ج.م\nالمتوفر: {qty}"
            btn = QPushButton(label_text)
            # Smaller icons than services to fit more items
            btn.setMinimumSize(220, 160)
            btn.setStyleSheet("QPushButton { background-color: #D4AF37; color: black; border-radius: 8px; font-size: 16px; } QPushButton:hover { background-color: #B8962D; }")
            btn.clicked.connect(lambda _, p=pid, n=name, pr=price, q=qty: self.add_product_to_invoice(p, n, pr, q))
            self.products_grid.addWidget(btn, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def add_product_to_invoice(self, pid: int, name: str, price: float, qty_available: int):
        if qty_available <= 0:
            QMessageBox.warning(self, "تنبيه", f"المنتج {name} غير متوفر")
            return
        inv_item = QListWidgetItem(f"{name} - {format_amount(price)} ج.م")
        inv_item.setData(Qt.UserRole, (pid, name, price, 1))
        # Newest first
        self.invoice_list.insertItem(0, inv_item)
        self._update_total()

    def remove_selected_invoice_item(self):
        for item in self.invoice_list.selectedItems():
            row = self.invoice_list.row(item)
            self.invoice_list.takeItem(row)
        self._update_total()

    def _update_total(self):
        total = 0.0
        for i in range(self.invoice_list.count()):
            data = self.invoice_list.item(i).data(Qt.UserRole)
            if data is None:
                continue
            if len(data) == 3:
                name, price, qty = data
            else:
                pid, name, price, qty = data
            total += price * qty
        discount_text = self.discount_combo.currentText()
        discount_percent = 0
        if discount_text.endswith("%") and discount_text != "بدون خصم":
            discount_percent = int(discount_text[:-1])
        total_after = total * (1 - discount_percent/100.0)
        self.total_label.setText(f"الإجمالي: {format_amount(total_after)} ج.م")

    def _submit_invoice(self):
        if self.invoice_list.count() == 0:
            QMessageBox.warning(self, "تنبيه", "الفاتورة فارغة")
            return

        total = 0.0
        items = []
        for i in range(self.invoice_list.count()):
            pid, name, price, qty = self.invoice_list.item(i).data(Qt.UserRole)
            total += price * qty
            items.append((pid, name, price, qty))

        discount_text = self.discount_combo.currentText()
        discount_percent = 0
        if discount_text.endswith("%") and discount_text != "بدون خصم":
            discount_percent = int(discount_text[:-1])
        material_deduction = float(self.material_deduction_input.value())

        mode = self.mode_combo.currentText()
        customer_name = self.customer_input.text().strip() or "غير محدد"
        employee_id = self.employee_combo.currentData() if self.employee_combo.currentIndex() >= 0 else None

        # Link to active shift if present
        try:
            sh = self.db.get_active_shift()
            shift_id = sh[0] if sh else None
        except Exception:
            shift_id = None

        # Branch behavior by mode
        if mode == "عميل":
            # Normal customer sale -> employee should have no effect
            try:
                sale_id = self.db.create_sale(
                    date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    employee_id=None,  # ignore employee
                    customer_name=customer_name,
                    is_shop=0,
                    total=total,
                    discount_percent=discount_percent,
                    sale_type="product",
                    buyer_type="customer",
                    material_deduction=material_deduction,
                    shift_id=shift_id,
                )
                for pid, name, price, qty in items:
                    self.db.add_sale_item(sale_id, name, price, qty)
                    if pid:
                        try:
                            self.db.update_product_qty(pid, -qty)
                        except Exception:
                            pass
            except Exception:
                pass

            ts = datetime.now()
            basename = f"receipt_product_{ts.strftime('%Y%m%d_%H%M%S')}"
            txt_path = os.path.join(receipts_dir(), f"{basename}.txt")

            lines = [
                "صالون مينا العربي",
                f"التاريخ: {ts.strftime('%Y-%m-%d %I:%M %p')}",
                f"المشتري: {customer_name}",
                "-" * 30
            ]
            for _, name, price, qty in items:
                lines.append(f"{name} x{qty} - {format_amount(price)} ج.م")
            total_after = total * (1 - discount_percent/100.0)
            lines += ["-" * 30, f"الإجمالي: {format_amount(total_after)} ج.م"]
            receipt_text = "\n".join(lines)

            # Write receipt file and verify
            write_ok = False
            try:
                with open(txt_path, "w", encoding="utf-8") as ftxt:
                    ftxt.write(receipt_text)
                    ftxt.flush()
                write_ok = os.path.isfile(txt_path)
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"تعذر حفظ الإيصال:\n{e}\n{txt_path}")

            if write_ok:
                try:
                    print_receipt(receipt_text)
                    QMessageBox.information(self, "تم", f"تم حفظ وطباعة الإيصال.\n{txt_path}")
                except Exception as e:
                    QMessageBox.warning(self, "تنبيه", f"تم حفظ الإيصال لكن فشلت الطباعة:\n{e}\n{txt_path}")

        elif mode == "للمحل":
            # Internal shop usage:
            # 1) Create a sale with buyer_type='shop' so it reflects in admin totals
            # 2) Record expense under "مشتريات للمحل" with item name in note
            # 3) Deduct quantities from inventory
            saved_any = False
            try:
                sale_id = self.db.create_sale(
                    date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    employee_id=None,
                    customer_name="المحل",
                    is_shop=1,
                    total=total,
                    discount_percent=discount_percent,
                    sale_type="product",
                    buyer_type="shop",
                    material_deduction=0.0,
                    shift_id=shift_id,
                )
                for pid, name, price, qty in items:
                    # Add sale items
                    self.db.add_sale_item(sale_id, name, price, qty)
                    # Record expense entry for shop purchases
                    self.db.add_expense(category="مشتريات للمحل", amount=price * qty, note=name, shift_id=shift_id)
                    # Deduct from inventory
                    if pid:
                        try:
                            self.db.update_product_qty(pid, -qty)
                        except Exception:
                            pass
                saved_any = True
            except Exception:
                pass
            if saved_any:
                QMessageBox.information(self, "تم", "تم تسجيل فاتورة للمحل وخصم الكميات من المخزن وإضافتها للمصاريف.")
            else:
                QMessageBox.warning(self, "تنبيه", "تعذر تسجيل الاستخدام للمحل.")

        elif mode == "للموظف":
            # Record under employee for tracking, but not counted towards balance/commission
            if employee_id is None:
                QMessageBox.warning(self, "تنبيه", "اختر الموظف أولاً.")
                return
            try:
                sale_id = self.db.create_sale(
                    date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    employee_id=employee_id,
                    customer_name=None,
                    is_shop=0,
                    total=total,
                    discount_percent=discount_percent,
                    sale_type="product",
                    buyer_type="employee",  # used by reports to exclude from balance/commission
                    material_deduction=material_deduction,
                    shift_id=shift_id,
                )
                for pid, name, price, qty in items:
                    self.db.add_sale_item(sale_id, name, price, qty)
                    if pid:
                        try:
                            self.db.update_product_qty(pid, -qty)
                        except Exception:
                            pass
            except Exception:
                pass
            # Optionally save a text receipt (no business impact)
            ts = datetime.now()
            basename = f"receipt_employee_{ts.strftime('%Y%m%d_%H%M%S')}"
            txt_path = os.path.join(receipts_dir(), f"{basename}.txt")
            lines = [
                "صالون مينا العربي",
                f"التاريخ: {ts.strftime('%Y-%m-%d %I:%M %p')}",
                f"الموظف: {self.employee_combo.currentText()}",
                "-" * 30
            ]
            for _, name, price, qty in items:
                lines.append(f"{name} x{qty} - {format_amount(price)} ج.م")
            total_after = total * (1 - discount_percent/100.0)
            lines += ["-" * 30, f"الإجمالي: {format_amount(total_after)} ج.م"]
            receipt_text = "\n".join(lines)
            try:
                with open(txt_path, "w", encoding="utf-8") as ftxt:
                    ftxt.write(receipt_text)
            except Exception:
                pass

        # Reset common fields
        self.invoice_list.clear()
        self.customer_input.clear()
        self.material_deduction_input.setValue(0)
        self._update_total()
        self.load_products()