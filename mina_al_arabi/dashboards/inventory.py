from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSpinBox, QPushButton, QTableWidget,
    QTableWidgetItem
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from mina_al_arabi.db import Database


class InventoryDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        layout = QVBoxLayout(self)

        form = QHBoxLayout()
        lbl_name = QLabel("اسم المنتج")
        lbl_name.setFont(self.body_font)
        form.addWidget(lbl_name)
        self.name_input = QLineEdit()
        self.name_input.setFont(self.body_font)
        self.name_input.setMinimumWidth(250)
        form.addWidget(self.name_input)

        lbl_qty = QLabel("الكمية")
        lbl_qty.setFont(self.body_font)
        form.addWidget(lbl_qty)
        self.qty_input = QSpinBox()
        self.qty_input.setFont(self.body_font)
        self.qty_input.setMaximum(100000)
        self.qty_input.setMinimumWidth(120)
        form.addWidget(self.qty_input)

        lbl_price = QLabel("السعر")
        lbl_price.setFont(self.body_font)
        form.addWidget(lbl_price)
        self.price_input = QSpinBox()
        self.price_input.setFont(self.body_font)
        self.price_input.setMaximum(100000)
        self.price_input.setMinimumWidth(120)
        form.addWidget(self.price_input)

        add_btn = QPushButton("إضافة للمخزن")
        add_btn.setFont(self.body_font)
        add_btn.clicked.connect(self.add_product)
        form.addWidget(add_btn)

        layout.addLayout(form)

        self.table = QTableWidget(0, 4)
        self.table.setFont(self.body_font)
        self.table.setHorizontalHeaderLabels(["المعرف", "الاسم", "السعر", "الكمية"])
        self.table.setStyleSheet("QTableWidget { gridline-color: #D4AF37; }")
        # Expand to fill available space
        layout.addWidget(self.table)

        action_row = QHBoxLayout()
        refresh_btn = QPushButton("تحديث القائمة")
        refresh_btn.setFont(self.body_font)
        refresh_btn.clicked.connect(self.load_products)
        action_row.addWidget(refresh_btn)

        delete_btn = QPushButton("حذف المنتج المحدد")
        delete_btn.setFont(self.body_font)
        delete_btn.clicked.connect(self.delete_selected_product)
        action_row.addWidget(delete_btn)

        layout.addLayout(action_row)

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

    def delete_selected_product(self):
        row = self.table.currentRow()
        if row < 0:
            return
        pid_item = self.table.item(row, 0)
        if not pid_item:
            return
        try:
            pid = int(pid_item.text())
            self.db.delete_product(pid)
            self.load_products()
        except ValueError:
            pass

    def load_products(self):
        products = self.db.list_products()
        self.table.setRowCount(0)
        for pid, name, price, qty in products:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(pid)))
            self.table.setItem(r, 1, QTableWidgetItem(name))
            self.table.setItem(r, 2, QTableWidgetItem(str(int(round(price)))))
            self.table.setItem(r, 3, QTableWidgetItem(str(qty)))
        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()