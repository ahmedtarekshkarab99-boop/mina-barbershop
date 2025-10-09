from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from mina_al_arabi.db import Database


class HomeDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.header_font = QFont("Cairo", 20, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        layout = QVBoxLayout(self)

        title = QLabel("الرئيسية")
        title.setFont(self.header_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.summary_label = QLabel("")
        self.summary_label.setFont(self.body_font)
        self.summary_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.summary_label)

        self.refresh_summary()

    def refresh_summary(self):
        # Simple overview counts
        try:
            num_employees = len(self.db.list_employees())
        except Exception:
            num_employees = 0
        try:
            num_services = len(self.db.list_services())
        except Exception:
            num_services = 0
        try:
            products = self.db.list_products()
            num_products = len(products)
            total_stock = sum(p[3] for p in products) if products else 0
        except Exception:
            num_products = 0
            total_stock = 0

        self.summary_label.setText(
            f"عدد الموظفين: {num_employees} | عدد الخدمات: {num_services} | "
            f"عدد المنتجات: {num_products} (إجمالي الكمية: {total_stock})"
        )