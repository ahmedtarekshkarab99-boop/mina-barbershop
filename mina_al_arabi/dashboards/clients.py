from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
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


class ClientsDashboard(QWidget):
    """شاشة العملاء: بحث بالاسم/الهاتف، وعرض تاريخ الفواتير وإجماليات الخدمات/المبيعات."""
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        layout = QVBoxLayout(self)

        title = QLabel("العملاء")
        title.setFont(self.header_font)
        layout.addWidget(title)

        # Search controls
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("بحث (اسم العميل / رقم الهاتف):"))
        self.search_input = QLineEdit()
        self.search_input.setFont(self.body_font)
        self.search_input.setPlaceholderText("اكتب جزءاً من الاسم أو الرقم...")
        search_row.addWidget(self.search_input)
        search_btn = QPushButton("بحث")
        search_btn.setFont(self.body_font)
        search_btn.clicked.connect(self.search_clients)
        search_row.addWidget(search_btn)
        layout.addLayout(search_row)

        # Invoices table
        self.table = QTableWidget(0, 4)
        self.table.setFont(self.body_font)
        self.table.setHorizontalHeaderLabels(["التاريخ", "العميل", "النوع", "القيمة (صافي)"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        # Summary
        self.summary_label = QLabel("إجمالي الخدمات: 0 ج.م | إجمالي المبيعات: 0 ج.م")
        self.summary_label.setFont(self.body_font)
        layout.addWidget(self.summary_label, alignment=Qt.AlignRight)

    def search_clients(self):
        query = self.search_input.text().strip()
        rows = self.db.list_sales_by_customer_like(query)
        self.table.setRowCount(0)
        total_services = 0.0
        total_products = 0.0
        for s in rows:
            i = self.table.rowCount()
            self.table.insertRow(i)
            net = float(s["total"]) * (1 - (int(s.get("discount_percent") or 0)/100.0))
            if net < 0:
                net = 0.0
            # Fill
            self.table.setItem(i, 0, QTableWidgetItem(format_time_ar_str(s["date"])))
            self.table.setItem(i, 1, QTableWidgetItem(s.get("customer_name") or ""))
            self.table.setItem(i, 2, QTableWidgetItem("خدمة" if s.get("type") == "service" else "منتج"))
            self.table.setItem(i, 3, QTableWidgetItem(format_amount(net)))
            if s.get("type") == "service":
                total_services += net
            else:
                total_products += net
        self.table.resizeColumnsToContents()
        self.summary_label.setText(
            f"إجمالي الخدمات: {format_amount(total_services)} ج.م | "
            f"إجمالي المبيعات: {format_amount(total_products)} ج.م"
        )