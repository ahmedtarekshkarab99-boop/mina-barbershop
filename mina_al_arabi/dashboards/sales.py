from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QListWidget,
    QListWidgetItem, QMessageBox, QAbstractItemView, QScrollArea, QGridLayout, QComboBox, QRadioButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from datetime import datetime
from mina_al_arabi.db import Database, RECEIPTS_DIR
import os


def format_amount(amount: float) -> str:
    # Show whole numbers only
    return f"{int(round(amount))}"


def format_time_ar(dt: datetime) -> str:
    h = dt.strftime("%I")
    m = dt.strftime("%M")
    ampm = dt.strftime("%p")
    suffix = "ص" if ampm == "AM" else "م"
    return f"{h}:{m} {suffix}"


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

        # Top control row: refresh
        ctrl_row = QHBoxLayout()
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
        left.addWidget(self.products_area)

        # Right: Invoice area
        right = QVBoxLayout()
        title_invoice = QLabel("الفاتورة")
        title_invoice.setFont(self.header_font)
        right.addWidget(title_invoice)

        # Buyer selection - mutually exclusive
        buyer_layout = QHBoxLayout()

        self.customer_radio = QRadioButton("عميل")
        self.customer_radio.setChecked(True)
        self.store_radio = QRadioButton("المحل")
        self.employee_radio = QRadioButton("موظف")

        buyer_layout.addWidget(self.customer_radio)
        buyer_layout.addWidget(self.store_radio)
        buyer_layout.addWidget(self.employee_radio)

        buyer_layout.addWidget(QLabel("اسم العميل"))
        self.customer_input = QLineEdit()
        self.customer_input.setFont(self.body_font)
        buyer_layout.addWidget(self.customer_input)

        buyer_layout.addWidget(QLabel("الموظف"))
        self.employee_combo = QComboBox()
        self.employee_combo.setFont(self.body_font)
        buyer_layout.addWidget(self.employee_combo)

        # Link radios to enabling/disabling fields
        self.customer_radio.toggled.connect(self._update_buyer_fields)
        self.store_radio.toggled.connect(self._update_buyer_fields)
        self.employee_radio.toggled.connect(self._update_buyer_fields)

        right.addLayout(buyer_layout)

        self.invoice_list = QListWidget()
        self.invoice_list.setFont(self.body_font)
        right.addWidget(self.invoice_list)

        action_row = QHBoxLayout()
        remove_btn = QPushButton("حذف العنصر المحدد")
        remove_btn.setFont(self.body_font)
        remove_btn.clicked.connect(self.remove_selected_invoice_item)
        action_row.addWidget(remove_btn)
        right.addLayout(action_row)

        totals_layout = QHBoxLayout()
        self.total_label = QLabel("الإجمالي: 0 ج.م")
        self.total_label.setFont(self.body_font)
        totals_layout.addWidget(self.total_label)
        right.addLayout(totals_layout)

        print_btn = QPushButton("طباعة إيصال")
        print_btn.setFont(self.body_font)
        print_btn.clicked.connect(self.print_receipt)
        right.addWidget(print_btn)

        root.addLayout(left, 2)
        root.addLayout(right, 1)

        self._load_employees()
        self._update_buyer_fields()
        self.load_products()

    def _update_buyer_fields(self):
        # Only one active at a time: customer, store, employee
        is_customer = self.customer_radio.isChecked()
        is_store = self.store_radio.isChecked()
        is_employee = self.employee_radio.isChecked()

        self.customer_input.setEnabled(is_customer)
        self.employee_combo.setEnabled(is_employee)

    def _load_employees(self):
        self.employee_combo.clear()
        for eid, name in self.db.list_employees():
            self.employee_combo.addItem(name, eid)

    def load_products(self):
        # Clear grid
        while self.products_grid.count():
            item = self.products_grid.itemAt(0)
            w = item.widget()
            self.products_grid.removeItem(item)
            if w:
                w.setParent(None)
        # Add product buttons
        row, col = 0, 0
        for pid, name, price, qty in self.db.list_products():
            label_text = f"{name}\n{format_amount(price)} ج.م\nالمتوفر: {qty}"
            btn = QPushButton(label_text)
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
        self.invoice_list.addItem(inv_item)
        self._update_total()

    def remove_selected_invoice_item(self):
        for item in self.invoice_list.selectedItems():
            row = self.invoice_list.row(item)
            self.invoice_list.takeItem(row)
        self._update_total()

    def _update_total(self):
        total = 0.0
        for i in range(self.invoice_list.count()):
            pid, name, price, qty = self.invoice_list.item(i).data(Qt.UserRole)
            total += price * qty
        self.total_label.setText(f"الإجمالي: {format_amount(total)} ج.م")

    def print_receipt(self):
        if self.invoice_list.count() == 0:
            QMessageBox.warning(self, "تنبيه", "الفاتورة فارغة")
            return

        total = 0.0
        items = []
        for i in range(self.invoice_list.count()):
            pid, name, price, qty = self.invoice_list.item(i).data(Qt.UserRole)
            total += price * qty
            items.append((pid, name, price, qty))

        # Determine buyer type
        is_customer = self.customer_radio.isChecked()
        is_store = self.store_radio.isChecked()
        is_employee = self.employee_radio.isChecked()

        customer_name = self.customer_input.text().strip() if is_customer else None
        employee_id = self.employee_combo.currentData() if is_employee else None

        buyer_type = "customer"
        is_shop = 0
        if is_store:
            buyer_type = "shop"
            is_shop = 1
        elif is_employee:
            buyer_type = "employee"

        sale_id = self.db.create_sale(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            employee_id=employee_id,
            customer_name=customer_name if is_customer else None,
            is_shop=is_shop,
            total=total,
            discount_percent=0,
            sale_type="product",
            buyer_type=buyer_type
        )
        for pid, name, price, qty in items:
            self.db.add_sale_item(sale_id, name, price, qty)
            # Decrease inventory
            self.db.update_product_qty(pid, -qty)

        # If shop is buyer, record each item as expense with product name
        if is_store:
            for _, name, price, qty in items:
                self.db.add_expense(category=name, amount=price * qty, note=f"فاتورة رقم {sale_id}")

        ts = datetime.now()
        arabic_time = format_time_ar(ts)
        path = os.path.join(RECEIPTS_DIR, f"receipt_product_{sale_id}_{ts.strftime('%Y%m%d_%H%M%S')}.txt")
        lines = []
        lines.append("صالون مينا العربي")
        lines.append(f"التاريخ: {ts.strftime('%Y-%m-%d')} {arabic_time}")
        if is_store:
            lines.append("المشتري: المحل")
        elif is_employee:
            # Show employee name
            emp_name = self.employee_combo.currentText() or ""
            lines.append(f"المشتري: موظف - {emp_name}")
        else:
            lines.append(f"المشتري: {customer_name if customer_name else 'غير محدد'}")
        lines.append("-" * 30)
        for _, name, price, qty in items:
            lines.append(f"{name} x{qty} - {format_amount(price)} ج.م")
        lines.append("-" * 30)
        lines.append(f"الإجمالي: {format_amount(total)} ج.م")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        QMessageBox.information(self, "تم", f"تم حفظ الإيصال:\n{path}")
        self.invoice_list.clear()
        self.customer_input.clear()
        self.customer_radio.setChecked(True)
        self._update_total()
        self.load_products()