from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QListWidget,
    QListWidgetItem, QSpinBox, QLineEdit, QDialog, QFormLayout, QDialogButtonBox, QMessageBox
)
from PySide6.QtCore import Qt
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

        main_layout = QVBoxLayout(self)

        # Employee selection
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("اختر الموظف:"))
        self.employee_combo = QComboBox()
        top_bar.addWidget(self.employee_combo)

        refresh_emp_btn = QPushButton("تحديث")
        refresh_emp_btn.clicked.connect(self._load_employees)
        top_bar.addWidget(refresh_emp_btn)
        main_layout.addLayout(top_bar)

        # Services list
        self.services_list = QListWidget()
        main_layout.addWidget(QLabel("الخدمات المتاحة:"))
        main_layout.addWidget(self.services_list)

        # Add selected to invoice
        btns = QHBoxLayout()
        add_btn = QPushButton("إضافة للخدمة المختارة إلى الفاتورة")
        add_btn.clicked.connect(self.add_selected_service_to_invoice)
        btns.addWidget(add_btn)
        main_layout.addLayout(btns)

        # Invoice section
        main_layout.addWidget(QLabel("الفاتورة:"))
        self.invoice_list = QListWidget()
        main_layout.addWidget(self.invoice_list)

        totals_layout = QHBoxLayout()
        self.total_label = QLabel("الإجمالي: 0 ج.م")
        totals_layout.addWidget(self.total_label)
        self.discount_combo = QComboBox()
        self.discount_combo.addItems(["بدون خصم", "10%", "15%", "20%"])
        totals_layout.addWidget(QLabel("الخصم:"))
        totals_layout.addWidget(self.discount_combo)
        main_layout.addLayout(totals_layout)

        print_btn = QPushButton("طباعة إيصال")
        print_btn.clicked.connect(self.print_receipt)
        main_layout.addWidget(print_btn)

        self._load_employees()
        self._load_services()

    def _load_employees(self):
        self.employee_combo.clear()
        for eid, name in self.db.list_employees():
            self.employee_combo.addItem(name, eid)

    def _load_services(self):
        self.services_list.clear()
        for sid, name, price in self.db.list_services():
            item = QListWidgetItem(f"{name} - {price:.2f} ج.م")
            item.setData(Qt.UserRole, (name, price))
            self.services_list.addItem(item)

    def add_selected_service_to_invoice(self):
        for item in self.services_list.selectedItems():
            name, price = item.data(Qt.UserRole)
            inv_item = QListWidgetItem(f"{name} - {price:.2f} ج.م")
            inv_item.setData(Qt.UserRole, (name, price, 1))
            self.invoice_list.addItem(inv_item)
        self._update_total()

    def _update_total(self):
        total = 0.0
        for i in range(self.invoice_list.count()):
            name, price, qty = self.invoice_list.item(i).data(Qt.UserRole)
            total += price * qty

        discount_text = self.discount_combo.currentText()
        discount_percent = 0
        if discount_text.endswith("%"):
            discount_percent = int(discount_text[:-1]) if discount_text != "بدون خصم" else 0
        total_after = total * (1 - discount_percent/100.0)
        self.total_label.setText(f"الإجمالي: {total_after:.2f} ج.م")

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
        if discount_text.endswith("%"):
            discount_percent = int(discount_text[:-1]) if discount_text != "بدون خصم" else 0

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
        lines.append(f"الخصم: {discount_percent}%")
        lines.append(f"الإجمالي: {total_after:.2f} ج.م")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        QMessageBox.information(self, "تم", f"تم حفظ الإيصال:\n{path}")
        self.invoice_list.clear()
        self._update_total()