from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QTableWidget, QTableWidgetItem, QPushButton, QRadioButton, QMessageBox, QInputDialog
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from datetime import datetime
from mina_al_arabi.db import Database

def format_amount(amount: float) -> str:
    return str(int(round(amount)))

def format_time_ar_str(dt_str: str) -> str:
    try:
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
        h = dt.strftime("%I")
        m = dt.strftime("%M")
        ampm = dt.strftime("%p")
        suffix = "ص" if ampm == "AM" else "م"
        return f"{dt.strftime('%Y-%m-%d')} {h}:{m} {suffix}"
    except Exception:
        return dt_str


class ReportsDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        layout = QVBoxLayout(self)

        title = QLabel("التقارير")
        title.setFont(self.header_font)
        layout.addWidget(title)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("الموظف"))
        self.employee_combo = QComboBox()
        self.employee_combo.setFont(self.body_font)
        controls.addWidget(self.employee_combo)

        controls.addWidget(QLabel("اليوم"))
        self.day_input = QSpinBox()
        self.day_input.setRange(1, 31)
        self.day_input.setValue(datetime.now().day)
        controls.addWidget(self.day_input)

        controls.addWidget(QLabel("الشهر"))
        self.month_input = QSpinBox()
        self.month_input.setRange(1, 12)
        self.month_input.setValue(datetime.now().month)
        controls.addWidget(self.month_input)

        # Filter mode
        self.daily_radio = QRadioButton("تقرير يومي")
        self.monthly_radio = QRadioButton("تقرير شهري")
        self.daily_radio.setChecked(True)
        controls.addWidget(self.daily_radio)
        controls.addWidget(self.monthly_radio)

        generate_btn = QPushButton("إنشاء التقرير")
        generate_btn.setFont(self.body_font)
        generate_btn.clicked.connect(self.refresh)
        controls.addWidget(generate_btn)

        clear_btn = QPushButton("تصفيه الحساب")
        clear_btn.setFont(self.body_font)
        clear_btn.clicked.connect(self._clear_employee_account)
        controls.addWidget(clear_btn)

        # Management actions on selected invoice
        self.change_emp_btn = QPushButton("تغيير الموظف للفاتورة المحددة")
        self.change_emp_btn.setFont(self.body_font)
        self.change_emp_btn.clicked.connect(self._change_invoice_employee)
        controls.addWidget(self.change_emp_btn)

        self.delete_inv_btn = QPushButton("حذف الفاتورة المحددة")
        self.delete_inv_btn.setFont(self.body_font)
        self.delete_inv_btn.clicked.connect(self._delete_selected_invoice)
        controls.addWidget(self.delete_inv_btn)

        layout.addLayout(controls)

        self.table = QTableWidget(0, 3)
        self.table.setFont(self.body_font)
        self.table.setHorizontalHeaderLabels(["الوصف", "الوقت", "القيمة (ج.م)"])
        layout.addWidget(self.table)

        self.summary_label = QLabel("إجمالي الخدمات: 0 ج.م | إجمالي المبيعات: 0 ج.م | الخصومات: 0 ج.م | الرصيد: 0 ج.م")
        self.summary_label.setFont(self.body_font)
        layout.addWidget(self.summary_label)

        self._load_employees()

    def _load_employees(self):
        self.employee_combo.clear()
        for eid, name in self.db.list_employees():
            self.employee_combo.addItem(name, eid)

    def refresh(self):
        if self.employee_combo.count() == 0:
            return
        employee_id = self.employee_combo.currentData()
        year = datetime.now().year
        month = int(self.month_input.value())
        day = int(self.day_input.value())
        date_str = f"{year}-{month:02d}-{day:02d}"

        # Choose scope
        if self.monthly_radio.isChecked():
            sales = self.db.list_sales_by_employee_in_month(employee_id, year, month)
            loans = self.db.list_loans_by_employee_in_month(employee_id, year, month)
        else:
            sales = self.db.list_sales_by_employee_on_date(employee_id, date_str)
            loans = self.db.list_loans_by_employee_on_date(employee_id, date_str)

        self.table.setRowCount(0)

        total_services = 0.0
        total_products = 0.0
        total_deductions = 0.0

        # Sales entries (apply visible discount and hidden material deduction)
        for s in sales:
            i = self.table.rowCount()
            self.table.insertRow(i)
            desc = "فاتورة خدمات" if s["type"] == "service" else "فاتورة مبيعات"
            # Effective value after visible discount and hidden material deduction
            discount_percent = int(s.get("discount_percent") or 0)
            material_deduction = float(s.get("material_deduction") or 0.0)
            effective_total = float(s["total"]) * (1 - discount_percent / 100.0)
            effective_total -= material_deduction
            if effective_total < 0:
                effective_total = 0.0

            if s.get("buyer_type") == "employee":
                desc = "فاتورة مبيعات (للموظف)"
            elif s["type"] == "service":
                total_services += effective_total
            else:
                total_products += effective_total

            # Set row data with sale id in first cell user data
            desc_item = QTableWidgetItem(desc)
            desc_item.setData(Qt.UserRole, s["id"])
            self.table.setItem(i, 0, desc_item)
            self.table.setItem(i, 1, QTableWidgetItem(format_time_ar_str(s["date"])))
            self.table.setItem(i, 2, QTableWidgetItem(format_amount(effective_total)))

        # Loan deductions
        for lid, date, amount, note in loans:
            i = self.table.rowCount()
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem("خصم (سلفة)"))
            self.table.setItem(i, 1, QTableWidgetItem(format_time_ar_str(date)))
            self.table.setItem(i, 2, QTableWidgetItem(format_amount(amount)))
            total_deductions += amount

        self.table.resizeColumnsToContents()
        balance = total_services + total_products - total_deductions
        self.summary_label.setText(
            f"إجمالي الخدمات: {format_amount(total_services)} ج.م | "
            f"إجمالي المبيعات: {format_amount(total_products)} ج.م | "
            f"الخصومات: {format_amount(total_deductions)} ج.م | "
            f"الرصيد: {format_amount(balance)} ج.م"
        )

    def _clear_employee_account(self):
        if self.employee_combo.count() == 0:
            return
        emp_name = self.employee_combo.currentText()
        emp_id = self.employee_combo.currentData()
        confirm = QMessageBox.question(self, "تأكيد", f"هل تريد تصفية حساب الموظف: {emp_name}؟ سيتم حذف الفواتير والسلف الخاصة به.")
        if confirm == QMessageBox.Yes:
            try:
                self.db.delete_sales_and_items_by_employee(emp_id)
                self.db.delete_loans_by_employee(emp_id)
                QMessageBox.information(self, "تم", "تم تصفية حساب الموظف.")
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء التصفية:\n{e}")

    def _get_selected_sale_id(self) -> int:
        row = self.table.currentRow()
        if row < 0:
            return 0
        cell = self.table.item(row, 0)
        if not cell:
            return 0
        sale_id = int(cell.data(Qt.UserRole) or 0)
        return sale_id

    def _change_invoice_employee(self):
        sale_id = self._get_selected_sale_id()
        if not sale_id:
            QMessageBox.warning(self, "تنبيه", "اختر فاتورة من الجدول أولاً.")
            return
        # Choose new employee
        employees = list(self.db.list_employees())
        if not employees:
            QMessageBox.warning(self, "تنبيه", "لا يوجد موظفون.")
            return
        names = [name for _, name in employees]
        name, ok = QInputDialog.getItem(self, "تغيير الموظف", "اختر الموظف:", names, 0, False)
        if not ok:
            return
        # Map name to id
        new_emp_id = None
        for eid, nm in employees:
            if nm == name:
                new_emp_id = eid
                break
        try:
            self.db.update_sale_employee(sale_id, new_emp_id)
            QMessageBox.information(self, "تم", "تم تغيير الموظف للفاتورة.")
            self.refresh()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"تعذر تغيير الموظف:\n{e}")

    def _delete_selected_invoice(self):
        sale_id = self._get_selected_sale_id()
        if not sale_id:
            QMessageBox.warning(self, "تنبيه", "اختر فاتورة من الجدول أولاً.")
            return
        confirm = QMessageBox.question(self, "تأكيد", "هل أنت متأكد من حذف هذه الفاتورة؟ هذا الإجراء لا يمكن التراجع عنه.")
        if confirm == QMessageBox.Yes:
            try:
                self.db.delete_sale_by_id(sale_id)
                QMessageBox.information(self, "تم", "تم حذف الفاتورة.")
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"تعذر حذف الفاتورة:\n{e}")