from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QLineEdit, QSpinBox, QPushButton,
    QTableWidget, QTableWidgetItem
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from datetime import datetime
from mina_al_arabi.db import Database


CATEGORIES = ["إيجار", "كهرباء", "مياه", "إنترنت", "مشتريات للمحل", "مصاريف مينا"]


def format_amount(amount: float) -> str:
    return str(int(round(amount)))


def format_time_ar(dt: datetime) -> str:
    h = dt.strftime("%I")
    m = dt.strftime("%M")
    ampm = dt.strftime("%p")
    suffix = "ص" if ampm == "AM" else "م"
    return f"{h}:{m} {suffix}"


class ExpensesDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        layout = QVBoxLayout(self)

        form = QHBoxLayout()
        lbl_cat = QLabel("الفئة")
        lbl_cat.setFont(self.body_font)
        form.addWidget(lbl_cat)
        self.category_combo = QComboBox()
        self.category_combo.addItems(CATEGORIES)
        self.category_combo.setFont(self.body_font)
        form.addWidget(self.category_combo)

        lbl_amt = QLabel("المبلغ")
        lbl_amt.setFont(self.body_font)
        form.addWidget(lbl_amt)
        self.amount_input = QSpinBox()
        self.amount_input.setMaximum(1000000)
        self.amount_input.setFont(self.body_font)
        form.addWidget(self.amount_input)

        lbl_note = QLabel("ملاحظة")
        lbl_note.setFont(self.body_font)
        form.addWidget(lbl_note)
        self.note_input = QLineEdit()
        self.note_input.setFont(self.body_font)
        form.addWidget(self.note_input)

        add_btn = QPushButton("إضافة مصروف")
        add_btn.setFont(self.body_font)
        add_btn.clicked.connect(self.add_expense)
        form.addWidget(add_btn)

        layout.addLayout(form)

        self.table = QTableWidget(0, 4)
        self.table.setFont(self.body_font)
        self.table.setHorizontalHeaderLabels(["المعرف", "التاريخ", "الفئة/الملاحظة", "المبلغ"])
        layout.addWidget(self.table)

        actions = QHBoxLayout()
        refresh_btn = QPushButton("تحديث")
        refresh_btn.setFont(self.body_font)
        refresh_btn.clicked.connect(self.load_expenses)
        actions.addWidget(refresh_btn)

        delete_selected_btn = QPushButton("حذف المحدد")
        delete_selected_btn.setFont(self.body_font)
        delete_selected_btn.clicked.connect(self.delete_selected)
        actions.addWidget(delete_selected_btn)

        delete_all_btn = QPushButton("حذف الكل")
        delete_all_btn.setFont(self.body_font)
        delete_all_btn.clicked.connect(self.delete_all)
        actions.addWidget(delete_all_btn)

        layout.addLayout(actions)

        self.summary_label = QLabel("إجمالي المصاريف: 0 ج.م")
        self.summary_label.setFont(self.body_font)
        layout.addWidget(self.summary_label, alignment=Qt.AlignRight)

        self.others_summary_label = QLabel("إجمالي بند مصاريف مينا: 0 ج.م")
        self.others_summary_label.setFont(self.body_font)
        layout.addWidget(self.others_summary_label, alignment=Qt.AlignRight)

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

    def delete_selected(self):
        row = self.table.currentRow()
        if row < 0:
            return
        item = self.table.item(row, 0)
        if not item:
            return
        try:
            exp_id = int(item.text())
            self.db.delete_expense_by_id(exp_id)
            self.load_expenses()
        except ValueError:
            pass

    def delete_all(self):
        self.db.delete_all_expenses()
        self.load_expenses()

    def load_expenses(self):
        rows = self.db.list_expenses()
        self.table.setRowCount(0)
        total = 0.0
        mina_total = 0.0
        for rid, date, cat, amount, note in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(rid)))
            # Format time Arabic 12h
            try:
                dt = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
                date_display = f"{dt.strftime('%Y-%m-%d')} {format_time_ar(dt)}"
            except Exception:
                date_display = date
            self.table.setItem(r, 1, QTableWidgetItem(date_display))
            # Map legacy "أخرى" to "مصاريف مينا" and show note when present
            is_mina = cat in {"أخرى", "مصاريف مينا"}
            display_cat = "مصاريف مينا" if cat == "أخرى" else cat
            cat_display = note if (is_mina and note) else display_cat
            self.table.setItem(r, 2, QTableWidgetItem(cat_display))
            self.table.setItem(r, 3, QTableWidgetItem(format_amount(amount)))
            total += amount
            if is_mina:
                mina_total += amount
        self.table.resizeColumnsToContents()
        self.summary_label.setText(f"إجمالي المصاريف: {format_amount(total)} ج.م")
        self.others_summary_label.setText(f"إجمالي بند مصاريف مينا: {format_amount(mina_total)} ج.م")