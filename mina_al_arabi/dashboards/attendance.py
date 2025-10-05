from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QGridLayout, QSpinBox,
    QMessageBox, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt
from datetime import datetime
from mina_al_arabi.db import Database


class AttendanceDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        layout = QVBoxLayout(self)

        # Employees grid
        layout.addWidget(QLabel("الموظفون:"))
        self.grid = QGridLayout()
        layout.addLayout(self.grid)

        # Loans
        loan_layout = QHBoxLayout()
        loan_layout.addWidget(QLabel("سلفة لموظف:"))
        self.loan_employee_input = QLineEdit()
        self.loan_employee_input.setPlaceholderText("اكتب اسم الموظف بالضبط")
        loan_layout.addWidget(self.loan_employee_input)
        loan_layout.addWidget(QLabel("المبلغ"))
        self.loan_amount_input = QSpinBox()
        self.loan_amount_input.setMaximum(100000)
        loan_layout.addWidget(self.loan_amount_input)
        add_loan_btn = QPushButton("إضافة سلفة")
        add_loan_btn.clicked.connect(self.add_loan)
        loan_layout.addWidget(add_loan_btn)
        layout.addLayout(loan_layout)

        # Monthly report
        report_layout = QHBoxLayout()
        report_layout.addWidget(QLabel("تقرير شهري: سنة"))
        self.year_input = QSpinBox()
        self.year_input.setRange(2000, 2100)
        self.year_input.setValue(datetime.now().year)
        report_layout.addWidget(self.year_input)
        report_layout.addWidget(QLabel("شهر"))
        self.month_input = QSpinBox()
        self.month_input.setRange(1, 12)
        self.month_input.setValue(datetime.now().month)
        report_layout.addWidget(self.month_input)
        gen_report_btn = QPushButton("تحديث التقرير")
        gen_report_btn.clicked.connect(self.load_report)
        report_layout.addWidget(gen_report_btn)
        layout.addLayout(report_layout)

        self.report_table = QTableWidget(0, 4)
        self.report_table.setHorizontalHeaderLabels(["التاريخ", "الموظف", "حضور", "انصراف"])
        layout.addWidget(self.report_table)

        self.load_employees()
        self.load_report()

    def load_employees(self):
        # Clear grid
        while self.grid.count():
            w = self.grid.itemAt(0).widget()
            self.grid.removeItem(self.grid.itemAt(0))
            if w:
                w.setParent(None)

        employees = self.db.list_employees()
        for i, (eid, name) in enumerate(employees):
            name_label = QLabel(name)
            check_in_btn = QPushButton("حضور")
            check_out_btn = QPushButton("انصراف")

            def make_check_in(eid=eid, name=name):
                def handler():
                    self.db.check_in(eid)
                    QMessageBox.information(self, "تم", f"تم تسجيل حضور: {name}")
                    self.load_report()
                return handler

            def make_check_out(eid=eid, name=name):
                def handler():
                    self.db.check_out(eid)
                    QMessageBox.information(self, "تم", f"تم تسجيل انصراف: {name}")
                    self.load_report()
                return handler

            check_in_btn.clicked.connect(make_check_in())
            check_out_btn.clicked.connect(make_check_out())

            row = i // 3
            col = (i % 3) * 3
            self.grid.addWidget(name_label, row, col)
            self.grid.addWidget(check_in_btn, row, col + 1)
            self.grid.addWidget(check_out_btn, row, col + 2)

    def add_loan(self):
        emp_name = self.loan_employee_input.text().strip()
        amount = float(self.loan_amount_input.value())
        if not emp_name or amount <= 0:
            return
        # Find employee by name
        employees = self.db.list_employees()
        emp_id = None
        for eid, name in employees:
            if name == emp_name:
                emp_id = eid
                break
        if emp_id is None:
            QMessageBox.warning(self, "تنبيه", "لم يتم العثور على الموظف")
            return
        self.db.add_loan(emp_id, amount)
        self.loan_employee_input.clear()
        self.loan_amount_input.setValue(0)
        QMessageBox.information(self, "تم", "تم تسجيل السلفة")

    def load_report(self):
        year = int(self.year_input.value())
        month = int(self.month_input.value())
        rows = self.db.list_attendance_for_month(year, month)
        self.report_table.setRowCount(0)
        for r in rows:
            i = self.report_table.rowCount()
            self.report_table.insertRow(i)
            self.report_table.setItem(i, 0, QTableWidgetItem(r["date"]))
            self.report_table.setItem(i, 1, QTableWidgetItem(r["employee"]))
            self.report_table.setItem(i, 2, QTableWidgetItem(r["check_in"] or ""))
            self.report_table.setItem(i, 3, QTableWidgetItem(r["check_out"] or ""))