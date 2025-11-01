from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem, QComboBox, QMessageBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from datetime import datetime
from mina_al_arabi.db import Database


def format_amount(x: float) -> str:
    return str(int(round(x)))


class SuppliersDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        layout = QVBoxLayout(self)

        title = QLabel("الموردون")
        title.setFont(self.header_font)
        layout.addWidget(title)

        # Add supplier form
        form_sup = QHBoxLayout()
        form_sup.addWidget(QLabel("اسم المورد"))
        self.sup_name = QLineEdit()
        self.sup_name.setFont(self.body_font)
        form_sup.addWidget(self.sup_name)

        form_sup.addWidget(QLabel("الهاتف"))
        self.sup_phone = QLineEdit()
        self.sup_phone.setFont(self.body_font)
        form_sup.addWidget(self.sup_phone)

        form_sup.addWidget(QLabel("ملاحظة"))
        self.sup_notes = QLineEdit()
        self.sup_notes.setFont(self.body_font)
        form_sup.addWidget(self.sup_notes)

        add_sup_btn = QPushButton("إضافة مورد")
        add_sup_btn.setFont(self.body_font)
        add_sup_btn.clicked.connect(self.add_supplier)
        form_sup.addWidget(add_sup_btn)

        layout.addLayout(form_sup)

        # Suppliers table
        self.table = QTableWidget(0, 5)
        self.table.setFont(self.body_font)
        self.table.setHorizontalHeaderLabels(["المعرف", "الاسم", "الهاتف", "ملاحظة", "الرصيد الحالي"])
        layout.addWidget(self.table)

        # Actions: invoice and payment
        actions = QHBoxLayout()
        actions.addWidget(QLabel("المورد"))
        self.supplier_combo = QComboBox()
        actions.addWidget(self.supplier_combo)

        # Invoice: total + paid
        actions.addWidget(QLabel("فاتورة: الإجمالي"))
        self.inv_total_input = QSpinBox()
        self.inv_total_input.setMaximum(1000000)
        actions.addWidget(self.inv_total_input)

        actions.addWidget(QLabel("مدفوع"))
        self.inv_paid_input = QSpinBox()
        self.inv_paid_input.setMaximum(1000000)
        actions.addWidget(self.inv_paid_input)

        record_inv_btn = QPushButton("تسجيل فاتورة")
        record_inv_btn.setFont(self.body_font)
        record_inv_btn.clicked.connect(self.record_invoice)
        actions.addWidget(record_inv_btn)

        # Payment
        actions.addWidget(QLabel("دفعة: المبلغ"))
        self.pay_amount_input = QSpinBox()
        self.pay_amount_input.setMaximum(1000000)
        actions.addWidget(self.pay_amount_input)

        actions.addWidget(QLabel("ملاحظة"))
        self.pay_note_input = QLineEdit()
        actions.addWidget(self.pay_note_input)

        add_pay_btn = QPushButton("إضافة دفعة")
        add_pay_btn.setFont(self.body_font)
        add_pay_btn.clicked.connect(self.add_payment)
        actions.addWidget(add_pay_btn)

        layout.addLayout(actions)

        # Summary
        self.summary_label = QLabel("إجمالي الفواتير: 0 | إجمالي المدفوعات: 0 | الرصيد المتبقي: 0")
        self.summary_label.setFont(self.body_font)
        layout.addWidget(self.summary_label, alignment=Qt.AlignRight)

        self.load_suppliers()
        self.refresh_summary()

    def load_suppliers(self):
        self.table.setRowCount(0)
        self.supplier_combo.clear()
        for sid, name, phone, notes in self.db.list_suppliers():
            r = self.table.rowCount()
            self.table.insertRow(r)
            # Compute balance
            summary = self.db.supplier_summary(sid)
            bal = summary.get("remaining", 0.0)
            self.table.setItem(r, 0, QTableWidgetItem(str(sid)))
            self.table.setItem(r, 1, QTableWidgetItem(name))
            self.table.setItem(r, 2, QTableWidgetItem(phone or ""))
            self.table.setItem(r, 3, QTableWidgetItem(notes or ""))
            self.table.setItem(r, 4, QTableWidgetItem(format_amount(bal)))
            self.supplier_combo.addItem(name, sid)
        self.table.resizeColumnsToContents()

    def add_supplier(self):
        name = self.sup_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم المورد.")
            return
        phone = self.sup_phone.text().strip() or None
        notes = self.sup_notes.text().strip() or None
        sid = self.db.add_supplier(name, phone, notes)
        self.sup_name.clear()
        self.sup_phone.clear()
        self.sup_notes.clear()
        self.load_suppliers()
        self.refresh_summary()
        QMessageBox.information(self, "تم", "تمت إضافة المورد.")

    def record_invoice(self):
        if self.supplier_combo.count() == 0:
            QMessageBox.warning(self, "تنبيه", "أضف مورداً أولاً.")
            return
        sid = self.supplier_combo.currentData()
        total = float(self.inv_total_input.value())
        paid = float(self.inv_paid_input.value())
        if total <= 0:
            QMessageBox.warning(self, "تنبيه", "أدخل إجمالي الفاتورة.")
            return
        if paid < 0 or paid > total:
            QMessageBox.warning(self, "تنبيه", "المدفوع يجب أن يكون بين 0 والإجمالي.")
            return
        self.db.add_supplier_invoice(sid, total, paid)
        # Optionally sync initial paid as Supplier Payments expense
        if paid > 0:
            self.db.add_supplier_payment(sid, paid, note="دفعة جزء من فاتورة")
        self.inv_total_input.setValue(0)
        self.inv_paid_input.setValue(0)
        self.load_suppliers()
        self.refresh_summary()
        QMessageBox.information(self, "تم", "تم تسجيل الفاتورة.")

    def add_payment(self):
        if self.supplier_combo.count() == 0:
            QMessageBox.warning(self, "تنبيه", "أضف مورداً أولاً.")
            return
        sid = self.supplier_combo.currentData()
        amount = float(self.pay_amount_input.value())
        note = self.pay_note_input.text().strip() or None
        if amount <= 0:
            QMessageBox.warning(self, "تنبيه", "أدخل مبلغ الدفعة.")
            return
        self.db.add_supplier_payment(sid, amount, note)
        self.pay_amount_input.setValue(0)
        self.pay_note_input.clear()
        self.load_suppliers()
        self.refresh_summary()
        QMessageBox.information(self, "تم", "تمت إضافة الدفعة وحفظها ضمن المصاريف (دفعات الموردين).")

    def refresh_summary(self):
        # If a supplier selected, show its summary
        if self.supplier_combo.count() == 0:
            self.summary_label.setText("إجمالي الفواتير: 0 | إجمالي المدفوعات: 0 | الرصيد المتبقي: 0")
            return
        sid = self.supplier_combo.currentData()
        s = self.db.supplier_summary(sid)
        self.summary_label.setText(
            f"إجمالي الفواتير: {format_amount(s.get('total_invoices',0))} | "
            f"إجمالي المدفوعات: {format_amount(s.get('total_payments',0))} | "
            f"الرصيد المتبقي: {format_amount(s.get('remaining',0))}"
        )