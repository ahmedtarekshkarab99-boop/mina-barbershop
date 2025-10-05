from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem
)
from mina_al_arabi.db import Database


CATEGORIES = ["إيجار", "كهرباء", "مياه", "إنترنت", "مشتريات للمحل", "أخرى"]


class ExpensesDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        layout = QVBoxLayout(self)

        form = QHBoxLayout()
        form.addWidget(QLabel("الفئة"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(CATEGORIES)
        form.addWidget(self.category_combo)

        form.addWidget(QLabel("المبلغ"))
        self.amount_input = QSpinBox()
        self.amount_input.setMaximum(1000000)
        form.addWidget(self.amount_input)

        form.addWidget(QLabel("ملاحظة"))
        self.note_input = QLineEdit()
        form.addWidget(self.note_input)

        add_btn = QPushButton("إضافة مصروف")
        add_btn.clicked.connect(self.add_expense)
        form.addWidget(add_btn)

        layout.addLayout(form)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["المعرف", "التاريخ", "الفئة", "المبلغ"])
        layout.addWidget(self.table)

        refresh_btn = QPushButton("تحديث")
        refresh_btn.clicked.connect(self.load_expenses)
        layout.addWidget(refresh_btn)

        self.load_expenses()

    def add_expense(self):
        cat = self.category_combo.currentText()
        amount = float(self.amount_input.value())
        note = self.note_input.text().strip() or None
        if amount <= 0:
            return
        self.db.add_expense(cat, amount, note)
        self.amount_input.setValue(0)
        self.note_input.clear()
        self.load_expenses()

    def load_expenses(self):
        rows = self.db.list_expenses()
        self.table.setRowCount(0)
        for rid, date, cat, amount, note in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(rid)))
            self.table.setItem(r, 1, QTableWidgetItem(date))
            self.table.setItem(r, 2, QTableWidgetItem(cat))
            self.table.setItem(r, 3, QTableWidgetItem(f"{amount:.2f}"))