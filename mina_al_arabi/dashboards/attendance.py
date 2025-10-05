from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QGridLayout, QSpinBox,
    QMessageBox, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from datetime import datetime
from mina_al_arabi.db import Database


class AttendanceDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        layout = QVBoxLayout(self)

        # Employees grid
        title_emp = QLabel("الموظفون:")
        title_emp.setFont(self.header_font)
        layout.addWidget(title_emp)
        self.grid = QGridLayout()
        layout.addLayout(self.grid)

        # Loans
        loan_layout = QHBoxLayout()
        lbl = QLabel("سلفة لموظف:")
        lbl.setFont(self.body_font)
        loan_layout.addWidget(lbl)
        self.loan_employee_combo = QComboBox()
        self.loan_employee_combo.setFont(self.body_font)
        loan_layout.addWidget(self.loan_employee_combo)
        loan_layout.addWidget(QLabel("المبلغ"))
        self.loan_amount_input = QSpinBox()
        self.loan_amount_input.setFont(self.body_font)
        self.loan_amount_input.setMaximum(100000)
        loan_layout.addWidget(self.loan_amount_input)
        add_loan_btn = QPushButton("إضافة سلفة")
        add_loan_btn.setFont(self.body_font)
        add_loan_btn.clicked.connect(self.add_loan)
        loan_layout.addWidget(add_loan_btn)
        layout.addLayout(loan_layout)

        # Report day/month only
        report_layout = QHBoxLayout()
        lbl_rep = QLabel("تقرير يومي: يوم / شهر")
        lbl_rep.setFont(self.body_font)
        report_layout.addWidget(lbl_rep)
        self.day_input = QSpinBox()
        self.day_input.setRange(1, 31)
        self.day_input.setValue(datetime.now().day)
        report_layout.addWidget(self.day_input)
        self.month_input = QSpinBox()
        self.month_input.setRange(1, 12)
        self.month_input.setValue(datetime.now().month)
        report_layout.addWidget(self.month_input)
        gen_report_btn = QPushButton("تحديث التقرير")
        gen_report_btn.setFont(self.body_font)
        gen_report_btn.clicked.connect(self.load_report)
        report_layout.addWidget(gen_report_btn)
        layout.addLayout(report_layout)

        self.report_table = QTableWidget(0, 4)
        self.report_table.setFont(self.body_font)
        self.report_table.setHorizontalHeaderLabels(["التاريخ", "الموظف", "حضور", "انصراف"])
        layout.addWidget(self.report_table, alignment=Qt.AlignCenter)

        self.load_employees()
        self._load_loan_employees()
        self.load_report()

        # Delete all attendance data button
        delete_all_btn = QPushButton("حذف كل البيانات")
        delete_all_btn.setFont(self.body_font)
        delete_all_btn.clicked.connect(self._delete_all_attendance)
        layout.addWidget(delete_all_btn, alignment=Qt.AlignRi_codeghnewt</)


    def load_employees(self):
        # Clear grid
        while self.grid.count():
            item = self.grid.itemAt(0)
            w = item.widget()
            self.grid.removeItem(item)
            if w:
                w.setParent(None)

        employees = self.db.list_employees()
        for i, (eid, name) in enumerate(employees):
            name_label = QLabel(name)
            name_label.setFont(self.body_font)
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
            # Position name closer to check buttons by using a 2-column grouping
            self.grid.addWidget(name_label, row, col)
            self.grid.addWidget(check_in_btn, row, col + 1)
            self.grid.addWidget(check_out_btn, row, col + 2)

    def _load_loan_employees(self):
        self.loan_employee_combo.clear()
        for eid, name in self.db.list_employees():
            self.loan_employee_combo.addItem(name, eid)

    def _delete_all_attendance(self):
        self.db.delete_all_attendance()
        self.load_report()

    def add_loan(self):
        if self.loan_employee_combo.count() == 0:
            return
        emp_id = self.loan_employee_combo.currentData()
        amount = float(self.loan_amount_input.value())
        if not emp_id or amount <= 0:
            return
        self.db.add_loan(emp_id, amount, note="سلفة")
        self.loan_amount_input.setValue(0)
        QMessageBox.information(self, "تم", "تم تسجيل السلفة")
        self.load_report()

    def load_report(self):
        # Filter attendance by selected day/month in current year
        year = datetime.now().year
        month = int(self.month_input.value())
        rows = self.db.list_attendance_for_month(year, month)
        day = int(self.day_input.value())
        self.report_table.setRowCount(0)
        for r in rows:
            # r["date"] is YYYY-MM-DD
            try:
                if int(r["date"].split("-")[2]) != day:
                    continue
            except Exception:
                pass
            i = self.report_table.rowCount()
            self.report_table.insertRow(i)
            self.report_table.setItem(i, 0, QTableWidgetItem(r["date"]))
            self.report_table.setItem(i, 1, QTableWidgetItem(r["employee"]))
            self.report_table.setItem(i, 2, QTableWidgetItem(r["check_in"] or ""))
            self.report_table.setItem(i, 3, QTableWidgetItem(r["check_out"] or ""))