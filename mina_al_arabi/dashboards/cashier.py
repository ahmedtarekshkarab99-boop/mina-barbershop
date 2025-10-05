from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QListWidget,
    QListWidgetItem, QSpinBox, QLineEdit, QDialog, QFormLayout, QDialogButtonBox, QMessageBox,
    QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from datetime import datetime
from mina_al_arabi.db import Database, RECEIPTS_DIR
import os


class AddServiceDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("إضافة خدمة")
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.price_input = QSpinBox()
        self.price_input.setMaximum(100000)
        self.price_input.setSuffix(" ج.م")
        layout.addRow("اسم الخدمة", self.name_input)
        layout.addRow("السعر", self.price_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.add)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def add(self):
        name = self.name_input.text().strip()
        price = float(self.price_input.value())
        if not name:
            QMessageBox.warning(self, "تنبيه", "من فضلك أدخل اسم الخدمة")
            return
        self.db.add_service(name, price)
        self.accept()


class AddEmployeeDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("إضافة موظف")
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        layout.addRow("اسم الموظف", self.name_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.add)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def add(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "من فضلك أدخل اسم الموظف")
            return
        self.db.add_employee(name)
        self.accept()


class CashierDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        # Fonts
        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        root = QHBoxLayout(self)

        # Left: Services (larger)
        left = QVBoxLayout()
        title_services = QLabel("الخدمات المتاحة")
        title_services.setFont(self.header_font)
        left.addWidget(title_services)

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

        self.invoice_list = QListWidget()
        self.invoice_list.setFont(self.body_font)
        right.addWidget(self.invoice_list)

        action_row = QHBoxLayout()
        remove_btn = QPushButton("حذف العنصر المحدد")
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
        self.discount_combo.addItems(["بدون خصم", "10%", "15%", "20%"])
        self.discount_combo.currentIndexChanged.connect(self._update_total)
        discount_row.addWidget(self.discount_combo)

        totals_layout.addWidget(self.total_before_label)
        totals_layout.addWidget(self.total_after_label)
        totals_layout.addLayout(discount_row)
        right.addLayout(totals_layout)

        print_btn = QPushButton("طباعة إيصال")
        print_btn.clicked.connect(self.print_receipt)
        right.addWidget(print_btn)

        # Assemble
        root.addLayout(left, 2)   # larger services area
        root.addLayout(right, 1)

        # Top bar for employee selection
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("اختر الموظف:"))
        self.employee_combo = QComboBox()
        top_bar.addWidget(self.employee_combo)
        refresh_emp_btn = QPushButton("تحديث")
        refresh_emp_btn.clicked.connect(self._load_employees)
        top_bar.addWidget(refresh_emp_btn)
        right.insertLayout(0, top_bar)

        self._load_employees()
        self._load_services()

    def _load_employees(self):
        self.employee_combo.clear()
        for eid, name in self.db.list_employees():
            self.employee_combo.addItem(name, eid)

    def _load_services(self):
        # Clear grid
        while self.services_grid.count():
            item = self.services_grid.itemAt(0)
            w = item.widget()
            self.services_grid.removeItem(item)
            if w:
                w.setParent(None)
        # Add service buttons
        row, col = 0, 0
        for sid, name, price in self.db.list_services():
            btn = QPushButton(f"{name}\n{price:.2f} ج.م")
            btn.setMinimumSize(160, 120)
            btn.setStyleSheet("QPushButton { background-color: #D4AF37; color: black; border-radius: 8px; font-size: 16px; } QPushButton:hover { background-color: #B8962D; }")
            btn.clicked.connect(lambda _, n=name, p=price: self.add_service_to_invoice(n, p))
            self.services_grid.addWidget(btn, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def add_service_to_invoice(self, name: str, price: float):
        inv_item = QListWidgetItem(f"{name} - {price:.2f} ج.م")
        inv_item.setData(Qt.UserRole, (name, price, 1))
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
            name, price, qty = self.invoice_list.item(i).data(Qt.UserRole)
            total += price * qty

        discount_text = self.discount_combo.currentText()
        discount_percent = 0
        if discount_text.endswith("%") and discount_text != "بدون خصم":
            discount_percent = int(discount_text[:-1])

        total_after = total * (1 - discount_percent/100.0)
        self.total_before_label.setText(f"الإجمالي قبل الخصم: {total:.2f} ج.م")
        self.total_after_label.setText(f"الإجمالي بعد الخصم: {total_after:.2f} ج.م")

    def open_add_service_dialog(self):
        dlg = AddServiceDialog(self.db, self)
        if dlg.exec():
            self._load_services()

    def open_add_employee_dialog(self):
        dlg = AddEmployeeDialog(self.db, self)
        if dlg.exec():
            self._load_employees()

    def print_receipt(self):
        if self.invoice_list.count() == 0:
            QMessageBox.warning(self, "تنبيه", "الفاتورة فارغة")
            return

        employee_id = self.employee_combo.currentData()
        employee_name = self.employee_combo.currentText() if employee_id is not None else ""

        discount_text = self.discount_combo.currentText()
        discount_percent = 0
        if discount_text.endswith("%") and discount_text != "بدون خصم":
            discount_percent = int(discount_text[:-1])

        total = 0.0
        items = []
        for i in range(self.invoice_list.count()):
            name, price, qty = self.invoice_list.item(i).data(Qt.UserRole)
            total += price * qty
            items.append((name, price, qty))
        total_after = total * (1 - discount_percent/100.0)

        # Save in DB as a sale (service type)
        sale_id = self.db.create_sale(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            employee_id=employee_id,
            customer_name=None,
            is_shop=0,
            total=total_after,
            discount_percent=discount_percent,
            sale_type="service"
        )
        for name, price, qty in items:
            self.db.add_sale_item(sale_id, name, price, qty)

        # Render simple text receipt
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(RECEIPTS_DIR, f"receipt_service_{sale_id}_{ts}.txt")
        lines = []
        lines.append("صالون مينا العربي")
        lines.append(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"الموظف: {employee_name}")
        lines.append("-" * 30)
        for name, price, qty in items:
            lines.append(f"{name} x{qty} - {price:.2f} ج.م")
        lines.append("-" * 30)
        lines.append(f"الإجمالي قبل الخصم: {total:.2f} ج.م")
        lines.append(f"الخصم: {discount_percent}%")
        lines.append(f"الإجمالي بعد الخصم: {total_after:.2f} ج.م")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        QMessageBox.information(self, "تم", f"تم حفظ الإيصال:\n{path}")
        self.invoice_list.clear()
        self._update_total()