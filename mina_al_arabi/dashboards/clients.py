from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox
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
    """شاشة العملاء: بحث بالاسم، وحقل لتعديل رقم الهاتف، وعرض تاريخ الفواتير وإجماليات الخدمات/المبيعات."""
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        layout = QVBoxLayout(self)

        title = QLabel("العملاء")
        title.setFont(self.header_font)
        layout.addWidget(title)

        # Search by name (unchanged)
        search_row = QHBoxLayout()
        name_lbl = QLabel("اسم العميل:")
        name_lbl.setFont(self.body_font)
        search_row.addWidget(name_lbl)
        self.search_input = QLineEdit()
        self.search_input.setFont(self.body_font)
        self.search_input.setPlaceholderText("اكتب جزءاً من الاسم...")
        search_row.addWidget(self.search_input)
        search_btn = QPushButton("بحث")
        search_btn.setFont(self.body_font)
        search_btn.clicked.connect(self.search_clients)
        search_row.addWidget(search_btn)
        layout.addLayout(search_row)

        # Client detail/edit panel (phone)
        detail_row = QHBoxLayout()
        self.selected_client_label = QLabel("العميل المحدد: -")
        self.selected_client_label.setFont(self.body_font)
        detail_row.addWidget(self.selected_client_label)
        detail_row.addWidget(QLabel("رقم الهاتف:"))
        self.phone_edit = QLineEdit()
        self.phone_edit.setFont(self.body_font)
        self.phone_edit.setPlaceholderText("أدخل رقم الهاتف (اختياري)")
        detail_row.addWidget(self.phone_edit)
        save_btn = QPushButton("حفظ الرقم")
        save_btn.setFont(self.body_font)
        save_btn.clicked.connect(self.save_phone)
        detail_row.addWidget(save_btn)
        layout.addLayout(detail_row)

        # Invoices table
        self.table = QTableWidget(0, 4)
        self.table.setFont(self.body_font)
        self.table.setHorizontalHeaderLabels(["التاريخ", "العميل", "النوع", "القيمة (صافي)"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        # React to selection to load phone
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)

        # Summary
        self.summary_label = QLabel("إجمالي الخدمات: 0 ج.م | إجمالي المبيعات: 0 ج.م")
        self.summary_label.setFont(self.body_font)
        layout.addWidget(self.summary_label, alignment=Qt.AlignRight)

        self.current_client_name = None

    def search_clients(self):
        query_name = self.search_input.text().strip()
        rows = []
        if query_name:
            rows = self.db.list_sales_by_customer_like(query_name)
        # Render
        self.table.setRowCount(0)
        total_services = 0.0
        total_products = 0.0
        # Show customer name with phone when available
        for s in rows:
            i = self.table.rowCount()
            self.table.insertRow(i)
            net = float(s["total"]) * (1 - (int(s.get("discount_percent") or 0)/100.0))
            if net < 0:
                net = 0.0
            cust_name = s.get("customer_name") or ""
            phone = self.db.get_client_phone(cust_name) or ""
            display_name = f"{cust_name}" + (f" — {phone}" if phone else "")
            # Fill
            self.table.setItem(i, 0, QTableWidgetItem(format_time_ar_str(s["date"])))
            self.table.setItem(i, 1, QTableWidgetItem(display_name))
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
        # Reset selection info
        self.current_client_name = None
        self.selected_client_label.setText("العميل المحدد: -")
        self.phone_edit.clear()

    def _on_table_selection_changed(self):
        row = self.table.currentRow()
        if row < 0:
            return
        # Extract original name from display (before phone)
        disp = self.table.item(row, 1).text() if self.table.item(row, 1) else ""
        # If contains separator " — ", split
        name = disp.split(" — ")[0].strip() if disp else ""
        self.current_client_name = name or None
        self.selected_client_label.setText(f"العميل المحدد: {name or '-'}")
        # Load phone
        if name:
            phone = self.db.get_client_phone(name) or ""
            self.phone_edit.setText(phone)
        else:
            self.phone_edit.clear()

    def save_phone(self):
        name = self.current_client_name
        if not name:
            QMessageBox.warning(self, "تنبيه", "اختر فاتورة من الجدول لتحديد العميل.")
            return
        phone = self.phone_edit.text().strip()
        # Basic validation: digits only with optional leading '+'
        if phone and not (phone.startswith("+") and phone[1:].isdigit() or phone.isdigit()):
            QMessageBox.warning(self, "تنبيه", "رقم الهاتف غير صالح. استخدم أرقام فقط مع إمكانية + لبداية الرقم الدولي.")
            return
        try:
            self.db.set_client_phone(name, phone)
            QMessageBox.information(self, "تم", "تم حفظ رقم الهاتف.")
            # Refresh current view to show phone next to name
            self.search_clients()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"تعذر حفظ الرقم:\n{e}")