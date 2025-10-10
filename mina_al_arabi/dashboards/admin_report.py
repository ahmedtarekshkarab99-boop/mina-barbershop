from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
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


class AdminReportDashboard(QWidget):
    """تقرير إداري شهري: إجمالي سعر الخدمات، إجمالي مصاريف مشتريات المحل، وقائمة البضائع المباعة للمحل."""
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        layout = QVBoxLayout(self)

        # Controls (month/year)
        controls = QHBoxLayout()
        title = QLabel("التقرير الإداري الشهري")
        title.setFont(self.header_font)
        controls.addWidget(title)

        controls.addStretch()

        controls.addWidget(QLabel("الشهر"))
        self.month_input = QSpinBox()
        self.month_input.setRange(1, 12)
        self.month_input.setValue(datetime.now().month)
        self.month_input.setFont(self.body_font)
        controls.addWidget(self.month_input)

        controls.addWidget(QLabel("السنة"))
        self.year_input = QSpinBox()
        self.year_input.setRange(2000, 2100)
        self.year_input.setValue(datetime.now().year)
        self.year_input.setFont(self.body_font)
        controls.addWidget(self.year_input)

        refresh_btn = QPushButton("تحديث")
        refresh_btn.setFont(self.body_font)
        refresh_btn.clicked.connect(self.refresh)
        controls.addWidget(refresh_btn)

        clear_btn = QPushButton("حذف بيانات الشهر")
        clear_btn.setFont(self.body_font)
        clear_btn.clicked.connect(self._clear_month_data)
        controls.addWidget(clear_btn)

        layout.addLayout(controls)

        # Summary line (single row)
        self.summary_label = QLabel("")
        self.summary_label.setFont(self.body_font)
        self.summary_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.summary_label)

        # Table of shop purchases (full screen area)
        self.table = QTableWidget(0, 5)
        self.table.setFont(self.body_font)
        self.table.setHorizontalHeaderLabels(["التاريخ", "المنتج", "الكمية", "سعر الوحدة", "الإجمالي"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.refresh()

    def refresh(self):
        year = int(self.year_input.value())
        month = int(self.month_input.value())

        # Totals
        total_services = self.db.sum_services_in_month(year, month)
        total_shop_expenses = self.db.sum_expenses_category_in_month("مشتريات للمحل", year, month)

        self.summary_label.setText(
            f"إجمالي الخدمات (الشهر): {format_amount(total_services)} ج.م | "
            f"إجمالي مصاريف مشتريات المحل: {format_amount(total_shop_expenses)} ج.م"
        )

        # Shop purchases list
        rows = self.db.list_shop_purchases_in_month(year, month)
        self.table.setRowCount(0)
        for date, item_name, unit_price, qty in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(format_time_ar_str(date)))
            self.table.setItem(r, 1, QTableWidgetItem(item_name))
            self.table.setItem(r, 2, QTableWidgetItem(str(qty)))
            self.table.setItem(r, 3, QTableWidgetItem(format_amount(unit_price)))
            self.table.setItem(r, 4, QTableWidgetItem(format_amount(unit_price * qty)))
        self.table.resizeColumnsToContents()

    def _clear_month_data(self):
        year = int(self.year_input.value())
        month = int(self.month_input.value())
        confirm = QMessageBox.question(self, "تأكيد", f"هل تريد حذف بيانات شهر {month}/{year}؟")
        if confirm == QMessageBox.Yes:
            try:
                self.db.delete_shop_data_in_month(year, month)
                QMessageBox.information(self, "تم", "تم حذف بيانات الشهر.")
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف:\n{e}")