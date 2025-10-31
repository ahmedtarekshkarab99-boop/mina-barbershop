from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QLineEdit, QPushButton, QMessageBox
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from mina_al_arabi.db import Database


class ShiftDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        layout = QVBoxLayout(self)

        title = QLabel("إدارة الشفتات (فتح/إغلاق)")
        title.setFont(self.header_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.status_label = QLabel("")
        self.status_label.setFont(self.body_font)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        form = QHBoxLayout()
        form.addWidget(QLabel("اسم الكاشير"))
        self.cashier_input = QLineEdit()
        self.cashier_input.setFont(self.body_font)
        form.addWidget(self.cashier_input)

        self.open_btn = QPushButton("فتح شفت")
        self.open_btn.setFont(self.body_font)
        self.open_btn.clicked.connect(self.open_shift)
        form.addWidget(self.open_btn)

        self.close_btn = QPushButton("إغلاق الشفت")
        self.close_btn.setFont(self.body_font)
        self.close_btn.clicked.connect(self.close_shift)
        form.addWidget(self.close_btn)

        layout.addLayout(form)

        self.summary_label = QLabel("")
        self.summary_label.setFont(self.body_font)
        layout.addWidget(self.summary_label, alignment=Qt.AlignRight)

        self.refresh()

    def refresh(self):
        sh = self.db.get_active_shift()
        if sh:
            _, shift_number, cashier_name, opened_at, closed_at, active = sh
            self.status_label.setText(f"شفت مفتوح رقم {shift_number} - {cashier_name} منذ {opened_at}")
            self.open_btn.setEnabled(False)
            self.close_btn.setEnabled(True)
        else:
            self.status_label.setText("لا يوجد شفت مفتوح حالياً")
            self.open_btn.setEnabled(True)
            self.close_btn.setEnabled(False)

    def open_shift(self):
        name = self.cashier_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم الكاشير لفتح الشفت")
            return
        sid = self.db.open_shift(name)
        self.cashier_input.clear()
        QMessageBox.information(self, "تم", f"تم فتح شفت رقم {sid}")
        self.refresh()

    def close_shift(self):
        sh = self.db.get_active_shift()
        if not sh:
            QMessageBox.warning(self, "تنبيه", "لا يوجد شفت مفتوح للإغلاق")
            return
        sid = sh[0]
        self.db.close_shift(sid)
        summary = self.db.shift_summary(sid)
        # Build summary text
        txt = []
        txt.append(f"شفت رقم: {summary.get('shift_number','')}")
        txt.append(f"الكاشير: {summary.get('cashier_name','')}")
        txt.append(f"البدء: {summary.get('opened_at','')}")
        txt.append(f"الانتهاء: {summary.get('closed_at','')}")
        txt.append(f"مدة الشفت: {summary.get('duration','')}")
        txt.append(f"إجمالي المبيعات بعد الخصم: {int(summary.get('total_sales',0))} ج.م")
        txt.append(f"عدد الفواتير: {summary.get('invoice_count',0)}")
        txt.append(f"خصومات العملاء: {int(summary.get('customer_discounts',0))} ج.م")
        txt.append(f"خصومات المواد: {int(summary.get('material_deductions',0))} ج.م")
        txt.append(f"إجمالي المصاريف: {int(summary.get('total_expenses',0))} ج.م")
        report_text = "\n".join(txt)
        self.summary_label.setText(report_text)
        QMessageBox.information(self, "تم", "تم إغلاق الشفت وعرض التقرير.")
        self.refresh()