from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QGridLayout, QSpinBox,
    QMessageBox, QTableWidget, QTableWidgetItem, QComboBox, QSizePolicy, QCheckBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from datetime import datetime, timedelta
from mina_al_arabi.db import Database

def format_time_12h_ar(time_str: str) -> str:
    """Convert 'HH:MM:SS' to Arabic 12-hour format 'hh:mm ص/م'."""
    if not time_str:
        return ""
    try:
        dt = datetime.strptime(time_str, "%H:%M:%S")
        h = dt.strftime("%I")
        m = dt.strftime("%M")
        ampm = dt.strftime("%p")
        suffix = "ص" if ampm == "AM" else "م"
        return f"{h}:{m} {suffix}"
    except Exception:
        return time_str

def compute_hours(date_str: str, check_in: str, check_out: str) -> str:
    """Return total working hours HH:MM considering overnight wrap (checkout after midnight)."""
    if not check_in or not check_out:
        return ""
    try:
        base_date = datetime.strptime(date_str, "%Y-%m-%d")
        ci = datetime.strptime(check_in, "%H:%M:%S")
        co = datetime.strptime(check_out, "%H:%M:%S")
        ci_dt = base_date.replace(hour=ci.hour, minute=ci.minute, second=ci.second)
        co_dt = base_date.replace(hour=co.hour, minute=co.minute, second=co.second)
        if co_dt < ci_dt:
            co_dt += timedelta(days=1)
        delta = co_dt - ci_dt
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    except Exception:
        return ""

class AttendanceDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Employees grid
        title_emp = QLabel("الموظفون:")
        title_emp.setFont(self.header_font)
        layout.addWidget(title_emp)
        self.grid = QGridLayout()
        self.grid.setHorizontalSpacing(8)
        self.grid.setVerticalSpacing(8)
        layout.addLayout(self.grid)

        # Admin controls
        admin_row = QHBoxLayout()
        self.admin_mode = QCheckBox("وضع المدير (تمكين الإدخال/التعديل اليدوي)")
        self.admin_mode.setFont(self.body_font)
        admin_row.addWidget(self.admin_mode)
        add_manual_btn = QPushButton("إضافة حضور يدوي")
        add_manual_btn.setFont(self.body_font)
        add_manual_btn.clicked.connect(self.add_manual_attendance)
        admin_row.addWidget(add_manual_btn)
        edit_btn = QPushButton("تعديل سجل حضور محدد")
        edit_btn.setFont(self.body_font)
        edit_btn.clicked.connect(self.edit_selected_attendance)
        admin_row.addWidget(edit_btn)
        del_btn = QPushButton("حذف السجل المحدد")
        del_btn.setFont(self.body_font)
        del_btn.clicked.connect(self.delete_selected_attendance)
        admin_row.addWidget(del_btn)
        layout.addLayout(admin_row)

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

        # Report controls
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

        self.report_table = QTableWidget(0, 6)
        self.report_table.setFont(self.body_font)
        self.report_table.setHorizontalHeaderLabels(["المعرف", "التاريخ", "الموظف", "حضور", "انصراف", "الساعات", "الحالة"])
        self.report_table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.report_table.setMinimumHeight(420)
        self.report_table.horizontalHeader().setStretchLastSection(True)
        self.report_table.verticalHeader().setVisible(False)
        layout.addWidget(self.report_table)

        # Delete all attendance data button (admin only)
        delete_all_btn = QPushButton("حذف كل بيانات الحضور")
        delete_all_btn.setFont(self.body_font)
        delete_all_btn.clicked.connect(self._delete_all_attendance)
        layout.addWidget(delete_all_btn, alignment=Qt.AlignRight)

        self.load_employees()
        self._load_loan_employees()
        self.load_report()

    def load_employees(self):
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
            self.grid.addWidget(name_label, row, col)
            self.grid.addWidget(check_in_btn, row, col + 1)
            self.grid.addWidget(check_out_btn, row, col + 2)

    def _load_loan_employees(self):
        self.loan_employee_combo.clear()
        for eid, name in self.db.list_employees():
            self.loan_employee_combo.addItem(name, eid)

    def _require_admin(self) -> bool:
        if not self.admin_mode.isChecked():
            QMessageBox.warning(self, "تنبيه", "هذه العملية متاحة للمدير فقط. فعّل وضع المدير أولاً.")
            return False
        return True

    def _delete_all_attendance(self):
        if not self._require_admin():
            return
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

    def add_manual_attendance(self):
        if not self._require_admin():
            return
        # Simple manual entry dialog via sequential prompts
        emps = self.db.list_employees()
        if not emps:
            QMessageBox.warning(self, "تنبيه", "لا يوجد موظفون.")
            return
        # Select employee
        names = [name for _, name in emps]
        emp_combo = QComboBox()
        for eid, name in emps:
            emp_combo.addItem(name, eid)
        # For simplicity, use input dialogs
        from PySide6.QtWidgets import QInputDialog
        # Employee selection
        # Note: QInputDialog does not support dropdown directly; we fallback to first employee or implement a small flow
        employee_id = emp_combo.itemData(0)
        # Manual input
        date_str, ok1 = QInputDialog.getText(self, "إضافة حضور يدوي", "التاريخ (YYYY-MM-DD):", text=datetime.now().strftime("%Y-%m-%d"))
        if not ok1 or not date_str.strip():
            return
        ci_str, ok2 = QInputDialog.getText(self, "إضافة حضور يدوي", "وقت الحضور (HH:MM:SS):", text="09:00:00")
        if not ok2 or not ci_str.strip():
            return
        co_str, ok3 = QInputDialog.getText(self, "إضافة حضور يدوي", "وقت الانصراف (HH:MM:SS) (اختياري):", text="")
        note_str, ok4 = QInputDialog.getText(self, "إضافة حضور يدوي", "ملاحظة (اختياري):", text="")
        try:
            self.db.add_manual_attendance(employee_id, date_str.strip(), ci_str.strip(), co_str.strip() or None, note_str.strip() or None)
            QMessageBox.information(self, "تم", "تمت إضافة سجل حضور يدوي.")
            self.load_report()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"تعذر إضافة السجل:\n{e}")

    def edit_selected_attendance(self):
        if not self._require_admin():
            return
        row = self.report_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "اختر سجلاً من الجدول.")
            return
        rec_id_item = self.report_table.item(row, 0)
        if not rec_id_item:
            return
        rec_id = int(rec_id_item.text())
        # Prompt for new times
        from PySide6.QtWidgets import QInputDialog
        ci_current = self.report_table.item(row, 3).text() if self.report_table.item(row, 3) else ""
        co_current = self.report_table.item(row, 4).text() if self.report_table.item(row, 4) else ""
        # Use raw HH:MM:SS instead of formatted
        ci_raw, ok1 = QInputDialog.getText(self, "تعديل سجل", "وقت الحضور (HH:MM:SS):", text=ci_current.replace(" ص", "").replace(" م", ""))
        if not ok1:
            return
        co_raw, ok2 = QInputDialog.getText(self, "تعديل سجل", "وقت الانصراف (HH:MM:SS):", text=co_current.replace(" ص", "").replace(" م", ""))
        if not ok2:
            return
        note_raw, ok3 = QInputDialog.getText(self, "تعديل سجل", "ملاحظة (اختياري):", text="")
        try:
            self.db.edit_attendance(rec_id, check_in=ci_raw.strip() or None, check_out=co_raw.strip() or None, note=note_raw.strip() or None, manual=1)
            QMessageBox.information(self, "تم", "تم تعديل السجل.")
            self.load_report()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"تعذر تعديل السجل:\n{e}")

    def delete_selected_attendance(self):
        if not self._require_admin():
            return
        row = self.report_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "تنبيه", "اختر سجلاً من الجدول.")
            return
        rec_id_item = self.report_table.item(row, 0)
        if not rec_id_item:
            return
        rec_id = int(rec_id_item.text())
        from PySide6.QtWidgets import QInputDialog
        confirm = QMessageBox.question(self, "تأكيد", "هل تريد حذف السجل المحدد؟")
        if confirm == QMessageBox.Yes:
            # Soft delete: set times to None and mark manual; optionally we could hard delete
            with self.db.connect() as conn:
                c = conn.cursor()
                c.execute("DELETE FROM attendance WHERE id = ?", (rec_id,))
                conn.commit()
            QMessageBox.information(self, "تم", "تم حذف السجل.")
            self.load_report()

    def load_report(self):
        year = datetime.now().year
        month = int(self.month_input.value())
        rows = self.db.list_attendance_for_month(year, month)
        day = int(self.day_input.value())
        self.report_table.setRowCount(0)
        for r in rows:
            try:
                if int(r["date"].split("-")[2]) != day:
                    continue
            except Exception:
                pass
            i = self.report_table.rowCount()
            self.report_table.insertRow(i)
            # id
            self.report_table.setItem(i, 0, QTableWidgetItem(str(r["id"])))
            self.report_table.setItem(i, 1, QTableWidgetItem(r["date"]))
            self.report_table.setItem(i, 2, QTableWidgetItem(r["employee"]))
            self.report_table.setItem(i, 3, QTableWidgetItem(format_time_12h_ar(r["check_in"]) if r["check_in"] else ""))
            self.report_table.setItem(i, 4, QTableWidgetItem(format_time_12h_ar(r["check_out"]) if r["check_out"] else ""))
            hours = compute_hours(r["date"], r["check_in"], r["check_out"])
            status = "يدوي" if r.get("manual") else "طبيعي"
            if r.get("manual"):
                status += " (أضيف يدوياً بواسطة المدير)"
            self.report_table.setItem(i, 5, QTableWidgetItem(hours))
            self.report_table.setItem(i, 6, QTableWidgetItem(status))
        self.report_table.resizeColumnsToContents()