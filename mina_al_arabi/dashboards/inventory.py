from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QPushButton, QTableWidget,
    QTableWidgetItem
)
from ..db import Database


class InventoryDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        layout = QVBoxLayout(self)

        form = QHBoxLayout()
        form.addWidget(QLabel("اسم المنتج"))
        self.name_input = QLineEdit()
        form.addWidget(self.name_input)

        form.addWidget(QLabel("الكمية"))
        self.qty_input = QSpinBox()
        self.qty_input.setMaximum(100000)
        form.addWidget(self.qty_input)

        form.addWidget(QLabel("السعر"))
        self.price_input = QSpinBox()
        self.price_input.setMaximum(100000)
        form.addWidget(self.price_input)

        add_btn = QPushButton("إضافة للمخزن")
        add_btn.clicked.connect(self.add_product)
        form.addWidget(add_btn)

        layout.addLayout(form)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["المعرف", "الاسم", "السعر", "الكمية"])
        layout.addWidget(self.table)

        refresh_btn = QPushButton("تحديث القائمة")
        refresh_btn.clicked.connect(self.load_products)
        layout.addWidget(refresh_btn)

        self.load_products()

    def add_product(self):
        name = self.name_input.text().strip()
        qty = int(self.qty_input.value())
        price = float(self.price_input.value())
        if not name:
            return
        self.db.add_product(name, price, qty)
        self.name_input.clear()
        self.qty_input.setValue(0)
        self.price_input.setValue(0)
        self.load_products()

    def load_products(self):
        products = self.db.list_products()
        self.table.setRowCount(0)
        for pid, name, price, qty in products:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(pid)))
            self.table.setItem(r, 1, QTableWidgetItem(name))
            self.table.setItem(r, 2, QTableWidgetItem(f"{price:.2f}"))
            self.table.setItem(r, 3, QTableWidgetItem(str(qty)))