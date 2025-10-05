from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QSpinBox, QTableWidget, QTableWidgetItem
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from datetime import datetime
from mina_al_arabi.db import Database


class ReportsDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        layout = QVBoxLayout(self)

        title = QLabel("التقارير")
        title.setFont(self.header_font)
        layout.addWidget(title)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("الموظف"))
        self.employee_combo = QComboBox()
        self.employee_combo.setFont(self.body_font)
        controls.addWidget(self.employee_combo)

        controls.addWidget(QLabel("اليوم"))
        self.day_input = QSpinBox()
        self.day_input.setRange(1, 31)
        self.day_input.setValue(datetime.now().day)
        controls.addWidget(self.day_input)

        controls.addWidget(QLabel("الشهر"))
        self.month_input = QSpinBox()
        self.month_input.setRange(1, 12)
        self.month_input.setValue(datetime.now().month)
        controls.addWidget(self.month_input)

        layout.addLayout(controls)

        self.table = QTableWidget(0, 3)
        self.table.setFont(self.body_font)
        self.table.setHorizontalHeaderLabels(["رقم الفاتورة", "الوقت", "الإجمالي"])
        layout.addWidget(self.table, alignment=Qt.AlignCenter)

        self.summary_label = QLabel("إجمالي خدمات اليوم: 0 ج.م")
        self.summary_label.setFont(self.body_font)
        layout.addWidget(self.summary_label)

        self.employee_combo.currentIndexChanged.connect(self.refresh)
        self.day_input.valueChanged.connect(self.refresh)
        self.month_input.valueChanged.connect(self.refresh)

        self._load_employees()
        self.refresh()

    def _load_employees(self):
        self.employee_combo.clear()
        for eid, name in self.db.list_employees():
            self.employee_combo.addItem(name, eid)

    def refresh(self):
        if self.employee_combo.count() == 0:
            return
        employee_id = self.employee_combo.currentData()
        # Compose date YYYY-MM-DD
        year = datetime.now().year
        month = int(self.month_input.value())
        day = int(self.day_input.value())
        date_str = f"{year}-{month:02d}-{day:02d}"

        sales = self.db.list_sales_by_employee_on_date(employee_id, date_str)
        self.table.setRowCount(0)

        total_services = 0.0
        for s in sales:
            i = self.table.rowCount()
            self.table.insertRow(i)
            # Show invoice id, time, total
            time_part = s["date"].split(" ")[1] if " " in s["date"] else s["date"]
            self.table.setItem(i, 0, QTableWidgetItem(str(s["id"])))
            self.table.setItem(i, 1, QTableWidgetItem(time_part))
            self.table.setItem(i, 2, QTableWidgetItem(f"{s['total']:.2f} ج.م"))
            if s["type"] == "service":
                total_services += s["total"]

        self.summary_label.setText(f"إجمالي خدمات اليوم: {total_services:.2f} ج.م")