from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QListWidget,
    QListWidgetItem, QSpinBox, QLineEdit, QMessageBox, QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from datetime import datetime
import os

from mina_al_arabi.db import Database
from mina_al_arabi.printing import print_receipt


def format_amount(amount: float) -> str:
    return f"{int(round(amount))}"


def receipts_dir() -> str:
    base = os.path.join(os.path.dirname(__file__), "..", "data", "receipts")
    base = os.path.abspath(base)
    os.makedirs(base, exist_ok=True)
    return base


class CashierDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        root = QHBoxLayout(self)

        # Left: Services
        left = QVBoxLayout()
        title_services = QLabel("الخدمات المتاحة")
        title_services.setFont(self.header_font)
        left.addWidget(title_services)

        # Search bar
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("بحث:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث عن خدمة...")
        self.search_input.textChanged.connect(self._load_services)
        search_row.addWidget(self.search_input)
        left.addLayout(search_row)

        self.services_area = QScrollArea()
        self.services_area.setWidgetResizable(True)
        self.services_container = QWidget()
        self.services_grid = QGridLayout(self.services_container)
        self.services_grid.setSpacing(12)
        self.services_area.setWidget(self.services_container)
        left.addWidget(self.services_area)

        # Right: Invoice
        right = QVBoxLayout()
        title_invoice = QLabel("الفاتورة")
        title_invoice.setFont(self.header_font)
        right.addWidget(title_invoice)

        # Top bar for customer + employee selection
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("اسم العميل"))
        self.customer_input = QLineEdit()
        self.customer_input.setFont(self.body_font)
        top_bar.addWidget(self.customer_input)
        top_bar.addWidget(QLabel("اختر الموظف:"))
        self.employee_combo = QComboBox()
        top_bar.addWidget(self.employee_combo)
        right.addLayout(top_bar)

        self.invoice_list = QListWidget()
        self.invoice_list.setFont(self.body_font)
        right.addWidget(self.invoice_list)

        action_row = QHBoxLayout()
        remove_btn = QPushButton("حذف المحدد")
        remove_btn.clicked.connect(self.remove_selected_invoice_item)
        action_row.addWidget(remove_btn)
        right.addLayout(action_row)

        totals_layout = QVBoxLayout()
        self.total_before_label = QLabel("الإجمالي قبل الخصم: 0 ج.م")
        self.total_before_label.setFont(self.body_font)
        self.total_after_label = QLabel("الإجمالي بعد الخصم: 0 ج.م")
        self.total_after_label.setFont(self.body_font)

        discount_row = QHBoxLayout()
        discount_row.addWidget(QLabel("الخصم:"))
        self.discount_combo = QComboBox()
        self.discount_combo.addItems(["بدون خصم", "10%", "20%", "30%", "40%", "50%"])
        self.discount_combo.currentIndexChanged.connect(self._update_total)
        discount_row.addWidget(self.discount_combo)

        mat_row = QHBoxLayout()
        mat_row.addWidget(QLabel("خصم مواد (مخفي):"))
        self.material_deduction_input = QSpinBox()
        self.material_deduction_input.setMaximum(1000000)
        mat_row.addWidget(self.material_deduction_input)

        totals_layout.addWidget(self.total_before_label)
        totals_layout.addWidget(self.total_after_label)
        totals_layout.addLayout(discount_row)
        totals_layout.addLayout(mat_row)
        right.addLayout(totals_layout)

        print_btn = QPushButton("طباعة إيصال")
        print_btn.clicked.connect(self.print_receipt)
        right.addWidget(print_btn)

        # Assemble
        root.addLayout(left, 2)
        root.addLayout(right, 1)

        self._load_employees()
        self._load_services()

    def _load_employees(self):
        self.employee_combo.clear()
        try:
            rows = self.db.list_employees()
            for eid, name in rows:
                self.employee_combo.addItem(name, eid)
        except Exception:
            pass

    def _clear_services_grid(self):
        while self.services_grid.count():
            item = self.services_grid.itemAt(0)
            w = item.widget()
            self.services_grid.removeItem(item)
            if w:
                w.setParent(None)

    def _load_services(self):
        self._clear_services_grid()
        query = (self.search_input.text().strip() or "").lower()
        try:
            services = self.db.list_services()
        except Exception:
            services = []
        # Reverse order: newest first
        services = list(reversed(services))
        row, col = 0, 0
        for sid, name, price in services:
            if query and (query not in name.lower()):
                continue
            btn = QPushButton(f"{name}\n{format_amount(price)} ج.م")
            btn.setMinimumSize(160, 120)
            btn.setStyleSheet("QPushButton { background-color: #D4AF37; color: black; border-radius: 8px; font-size: 16px; } QPushButton:hover { background-color: #B8962D; }")
            btn.clicked.connect(lambda _, n=name, p=price: self.add_service_to_invoice(n, p))
            self.services_grid.addWidget(btn, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def add_service_to_invoice(self, name: str, price: float):
        inv_item = QListWidgetItem(f"{name} - {format_amount(price)} ج.م")
        inv_item.setData(Qt.UserRole, (name, price, 1))
        # Newest added first (top)
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
            name, price, qty = self.invoice_list.item(i).data(Qt.UserRole)
            total += price * qty
        discount_text = self.discount_combo.currentText()
        discount_percent = 0
        if discount_text.endswith("%") and discount_text != "بدون خصم":
            discount_percent = int(discount_text[:-1])
        total_after = total * (1 - discount_percent/100.0)
        self.total_before_label.setText(f"الإجمالي قبل الخصم: {format_amount(total)} ج.م")
        self.total_after_label.setText(f"الإجمالي بعد الخصم: {format_amount(total_after)} ج.م")

    def print_receipt(self):
        if self.invoice_list.count() == 0:
            QMessageBox.warning(self, "تنبيه", "الفاتورة فارغة")
            return

        employee_id = self.employee_combo.currentData() if self.employee_combo.currentIndex() >= 0 else None
        employee_name = self.employee_combo.currentText() if self.employee_combo.currentIndex() >= 0 else ""
        customer_name = (self.customer_input.text().strip() or "غير محدد")

        discount_text = self.discount_combo.currentText()
        discount_percent = 0
        if discount_text.endswith("%") and discount_text != "بدون خصم":
            discount_percent = int(discount_text[:-1])

        material_deduction = float(self.material_deduction_input.value())

        total = 0.0
        items = []
        for i in range(self.invoice_list.count()):
            name, price, qty = self.invoice_list.item(i).data(Qt.UserRole)
            total += price * qty
            items.append((name, price, qty))
        total_after = total * (1 - discount_percent/100.0)

        # Persist sale (service) and link to active shift if present
        try:
            sh = self.db.get_active_shift()
            shift_id = sh[0] if sh else None
        except Exception:
            shift_id = None

        try:
            sale_id = self.db.create_sale(
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                employee_id=employee_id,
                customer_name=customer_name,
                is_shop=0,
                total=total,
                discount_percent=discount_percent,
                sale_type="service",
                buyer_type="customer",
                material_deduction=material_deduction,
                shift_id=shift_id,
            )
            for name, price, qty in items:
                self.db.add_sale_item(sale_id, name, price, qty)
        except Exception:
            pass

        # Build customer-facing receipt (hide material deduction)
        ts = datetime.now()
        lines = []
        lines.append("صالون مينا العربي")
        lines.append(f"التاريخ: {ts.strftime('%Y-%m-%d %I:%M %p')}")
        lines.append(f"المشتري: {customer_name}")
        lines.append(f"الموظف: {employee_name}")
        lines.append("-" * 30)
        for name, price, qty in items:
            lines.append(f"{name} x{qty} - {format_amount(price)} ج.م")
        lines.append("-" * 30)
        lines.append(f"الإجمالي قبل الخصم: {format_amount(total)} ج.م")
        lines.append(f"الخصم: {discount_percent}%")
        lines.append(f"الإجمالي بعد الخصم: {format_amount(total_after)} ج.م")
        text = "\n".join(lines)

        path = os.path.join(receipts_dir(), f"receipt_service_{ts.strftime('%Y%m%d_%H%M%S')}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

        try:
            print_receipt(text)
            QMessageBox.information(self, "تم", f"تم حفظ وطباعة الإيصال.\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "تنبيه", f"تم حفظ الإيصال لكن فشلت الطباعة:\n{e}\n{path}")

        self.invoice_list.clear()
        self.customer_input.clear()
        self.material_deduction_input.setValue(0)
        self._update_total()