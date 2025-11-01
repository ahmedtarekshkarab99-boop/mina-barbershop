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
    """تقرير إداري شهري شامل: الإيرادات، المصروفات، والملخص المالي."""
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

        clear_btn = QPushButton("حذف بيانات الشهر (مشتريات للمحل)")
        clear_btn.setFont(self.body_font)
        clear_btn.clicked.connect(self._clear_month_data)
        controls.addWidget(clear_btn)

        layout.addLayout(controls)

        # Dashboard top summary
        self.top_summary_label = QLabel("💰 صافي الربح: 0 | 🏪 قيمة المخزون: 0 | 🧾 أرصدة الموردين المعلقة: 0")
        self.top_summary_label.setFont(self.body_font)
        layout.addWidget(self.top_summary_label, alignment=Qt.AlignCenter)

        # Section 1: Revenue (simplified: net-after-discount only + per-employee)
        self.rev_header = QLabel("القسم 1 – الإيرادات (بعد الخصم)")
        self.rev_header.setFont(self.header_font)
        layout.addWidget(self.rev_header)

        self.rev_totals_label = QLabel("إجمالي الخدمات (صافي): 0 | إجمالي المبيعات (صافي): 0 | إجمالي الإيرادات (الصافي): 0")
        self.rev_totals_label.setFont(self.body_font)
        layout.addWidget(self.rev_totals_label, alignment=Qt.AlignRight)

        self.emp_table = QTableWidget(0, 2)
        self.emp_table.setFont(self.body_font)
        self.emp_table.setHorizontalHeaderLabels(["الموظف", "إجمالي خدمات الشهر (صافي)"])
        self.emp_table.horizontalHeader().setStretchLastSection(True)
        self.emp_table.verticalHeader().setVisible(False)
        layout.addWidget(self.emp_table)

        # Section 2: Expenses and Costs (simplified totals only)
        self.exp_header = QLabel("القسم 2 – المصاريف والتكاليف")
        self.exp_header.setFont(self.header_font)
        layout.addWidget(self.exp_header)

        self.exp_totals_label = QLabel("إجمالي المصاريف: 0 | مشتريات المحل: 0 | يوميات العمالة: 0 | دفعات الموردين: 0 | إجمالي خصومات المواد (مخفي): 0")
        self.exp_totals_label.setFont(self.body_font)
        layout.addWidget(self.exp_totals_label, alignment=Qt.AlignRight)

        # Section 3: Financial Summary (net only)
        self.fin_header = QLabel("القسم 3 – الملخص المالي")
        self.fin_header.setFont(self.header_font)
        layout.addWidget(self.fin_header)

        self.fin_totals_label = QLabel("إجمالي الإيرادات (الصافي): 0 | إجمالي المصاريف: 0 | صافي الربح: 0")
        self.fin_totals_label.setFont(self.body_font)
        layout.addWidget(self.fin_totals_label, alignment=Qt.AlignRight)

        self.refresh()

    def refresh(self):
        year = int(self.year_input.value())
        month = int(self.month_input.value())

        # Revenue totals (net-after-discount only)
        net_services = self.db.sum_services_net_in_month(year, month)
        net_sales = self.db.sum_products_net_in_month(year, month)
        total_revenue = net_services + net_sales
        self.rev_totals_label.setText(
            f"إجمالي الخدمات (صافي): {format_amount(net_services)} ج.م | "
            f"إجمالي المبيعات (صافي): {format_amount(net_sales)} ج.م | "
            f"إجمالي الإيرادات (الصافي): {format_amount(total_revenue)} ج.م"
        )

        # Per-employee services totals (effective after discounts/material deductions)
        self.emp_table.setRowCount(0)
        for eid, name in self.db.list_employees():
            sales = self.db.list_sales_by_employee_in_month(eid, year, month)
            emp_total = 0.0
            for s in sales:
                if s.get("type") == "service" and s.get("buyer_type") == "customer":
                    disc = int(s.get("discount_percent") or 0)
                    mat = float(s.get("material_deduction") or 0.0)
                    eff = float(s["total"]) * (1 - disc/100.0) - mat
                    if eff < 0:
                        eff = 0.0
                    emp_total += eff
            if emp_total > 0:
                r = self.emp_table.rowCount()
                self.emp_table.insertRow(r)
                self.emp_table.setItem(r, 0, QTableWidgetItem(name))
                self.emp_table.setItem(r, 1, QTableWidgetItem(format_amount(emp_total)))
        self.emp_table.resizeColumnsToContents()

        # Expenses and costs (simplified totals only)
        shop_exp = self.db.sum_expenses_category_in_month("مشتريات للمحل", year, month)
        daily_exp = self.db.sum_expenses_category_in_month("يوميات العمالة", year, month)
        supp_pay = self.db.sum_expenses_category_in_month("دفعات الموردين", year, month)
        # General = all minus categorized above
        rows = self.db.list_expenses()
        from datetime import datetime as dtmod
        gen_exp = 0.0
        for rid, date, cat, amount, note in rows:
            try:
                d = dtmod.strptime(date, "%Y-%m-%d %H:%M:%S")
                if d.year != year or d.month != month:
                    continue
            except Exception:
                if not (str(date)[:4] == str(year) and str(date)[5:7] == f"{month:02d}"):
                    continue
            if cat not in {"مشتريات للمحل", "يوميات العمالة", "دفعات الموردين"}:
                gen_exp += amount

        total_expenses = gen_exp + shop_exp + daily_exp + supp_pay
        total_hidden_material = self.db.sum_material_deductions_in_month(year, month)
        self.exp_totals_label.setText(
            f"إجمالي المصاريف: {format_amount(total_expenses)} ج.م | "
            f"مشتريات المحل: {format_amount(shop_exp)} ج.م | "
            f"يوميات العمالة: {format_amount(daily_exp)} ج.م | "
            f"دفعات الموردين: {format_amount(supp_pay)} ج.م | "
            f"إجمالي خصومات المواد (مخفي): {format_amount(total_hidden_material)} ج.م"
        )

        # Financial summary (net-only)
        net_profit = total_revenue - total_expenses
        self.fin_totals_label.setText(
            f"إجمالي الإيرادات (الصافي): {format_amount(total_revenue)} ج.م | "
            f"إجمالي المصاريف: {format_amount(total_expenses)} ج.م | "
            f"صافي الربح: {format_amount(net_profit)} ج.م"
        )

        # Top dashboard summary: Net Profit, Inventory Value, Pending Supplier Balances
        inv_value = self.db.inventory_total_value()
        supp_pending = self.db.total_supplier_pending_balance()
        self.top_summary_label.setText(
            f"💰 صافي الربح: {format_amount(net_profit)} ج.م | "
            f"🏪 قيمة المخزون: {format_amount(inv_value)} ج.م | "
            f"🧾 أرصدة الموردين المعلقة: {format_amount(supp_pending)} ج.م"
        )

    def _clear_month_data(self):
        year = int(self.year_input.value())
        month = int(self.month_input.value())
        confirm = QMessageBox.question(self, "تأكيد", f"هل تريد حذف بيانات مشتريات المحل لشهر {month}/{year}؟")
        if confirm == QMessageBox.Yes:
            try:
                self.db.delete_shop_data_in_month(year, month)
                QMessageBox.information(self, "تم", "تم حذف بيانات الشهر.")
                self.refresh()
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء الحذف:\n{e}")