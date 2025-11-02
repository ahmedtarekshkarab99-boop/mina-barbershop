from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QComboBox, QMessageBox, QInputDialog
)
from PySide6.QtCore import Qt, Signal
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


class Reports2Dashboard(QWidget):
    """التقارير 2: إدارة جميع الفواتير (المحل/العملاء/الموظفين) مع تعديل النوع والحذف."""
    changes_made = Signal()

    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        layout = QVBoxLayout(self)

        title = QLabel("التقارير 2 - إدارة الفواتير")
        title.setFont(self.header_font)
        layout.addWidget(title)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("فلتر النوع"))
        self.type_filter = QComboBox()
        self.type_filter.addItems(["الكل", "المحل", "العملاء"])
        self.type_filter.currentIndexChanged.connect(self.load_sales)
        controls.addWidget(self.type_filter)

        self.change_type_btn = QPushButton("تغيير نوع الفاتورة")
        self.change_type_btn.setFont(self.body_font)
        self.change_type_btn.clicked.connect(self._change_sale_type)
        controls.addWidget(self.change_type_btn)

        self.delete_btn = QPushButton("حذف الفاتورة")
        self.delete_btn.setFont(self.body_font)
        self.delete_btn.clicked.connect(self._delete_sale)
        controls.addWidget(self.delete_btn)

        # Generate report (full refresh)
        self.generate_btn = QPushButton("إنشاء التقرير")
        self.generate_btn.setFont(self.body_font)
        self.generate_btn.clicked.connect(self._generate_report)
        controls.addWidget(self.generate_btn)

        layout.addLayout(controls)

        self.table = QTableWidget(0, 6)
        self.table.setFont(self.body_font)
        self.table.setHorizontalHeaderLabels(["المعرف", "التاريخ", "نوع العنصر", "نوع الفاتورة", "العميل", "القيمة (صافي)"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)

        self.summary_label = QLabel("إجمالي الفواتير المعروضة: 0 ج.م")
        self.summary_label.setFont(self.body_font)
        layout.addWidget(self.summary_label, alignment=Qt.AlignRight)

        self.load_sales()

    def load_sales(self):
        rows = self.db.list_all_sales()
        # Apply filter – restrict to Sales/Inventory data only (products)
        sel = self.type_filter.currentText()
        filtered = []
        for s in rows:
            # Skip cashier/service invoices entirely
            if (s.get("type") or "") != "product":
                continue
            bt = s.get("buyer_type") or "customer"
            if sel == "الكل":
                filtered.append(s)
            elif sel == "المحل" and bt == "shop":
                filtered.append(s)
            elif sel == "العملاء" and bt == "customer":
                filtered.append(s)

        self.table.setRowCount(0)
        total_net = 0.0
        for s in filtered:
            i = self.table.rowCount()
            self.table.insertRow(i)
            # id
            id_item = QTableWidgetItem(str(s["id"]))
            id_item.setData(Qt.UserRole, s["id"])
            self.table.setItem(i, 0, id_item)
            # date
            self.table.setItem(i, 1, QTableWidgetItem(format_time_ar_str(s["date"])))
            # item type (always product for Reports 2)
            self.table.setItem(i, 2, QTableWidgetItem("منتج"))
            # buyer type
            bt_disp = {"customer": "عميل", "shop": "المحل"}.get(s.get("buyer_type"), "عميل")
            self.table.setItem(i, 3, QTableWidgetItem(bt_disp))
            # person (client name for customer; empty for shop) with phone if available
            person = s.get("customer_name") or ""
            try:
                phone = self.db.get_client_phone(person) or ""
                if person and phone:
                    person = f"{person} — {phone}"
            except Exception:
                pass
            self.table.setItem(i, 4, QTableWidgetItem(person))
            # net value after visible discount
            net = float(s["total"]) * (1 - (int(s.get("discount_percent") or 0) / 100.0))
            if net < 0:
                net = 0.0
            total_net += net
            self.table.setItem(i, 5, QTableWidgetItem(format_amount(net)))

        self.table.resizeColumnsToContents()
        self.summary_label.setText(f"إجمالي الفواتير المعروضة: {format_amount(total_net)} ج.م")

    def _generate_report(self):
        # Full reload to reflect latest system changes
        try:
            self.load_sales()
            try:
                self.changes_made.emit()
            except Exception:
                pass
        except Exception:
            pass

    def _get_selected_sale_id(self) -> int:
        row = self.table.currentRow()
        if row < 0:
            return 0
        cell = self.table.item(row, 0)
        if not cell:
            return 0
        sid = int(cell.data(Qt.UserRole) or 0)
        return sid

    def _change_sale_type(self):
        sale_id = self._get_selected_sale_id()
        if not sale_id:
            QMessageBox.warning(self, "تنبيه", "اختر فاتورة من الجدول أولاً.")
            return
        # Choose new type
        new_type, ok = QInputDialog.getItem(self, "تغيير نوع الفاتورة", "اختر النوع:", ["عميل", "المحل"], 0, False)
        if not ok:
            return
        # Map to internal buyer_type
        if new_type == "عميل":
            # Ask for customer name
            cust_name, ok2 = QInputDialog.getText(self, "اسم العميل", "أدخل اسم العميل:", text="غير محدد")
            if not ok2:
                return
            try:
                self.db.update_sale_buyer_type(sale_id, "customer", employee_id=None, customer_name=cust_name.strip() or "غير محدد")
                QMessageBox.information(self, "تم", "تم تغيير نوع الفاتورة إلى عميل.")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"تعذر التغيير:\n{e}")
        elif new_type == "المحل":
            try:
                self.db.update_sale_buyer_type(sale_id, "shop")
                QMessageBox.information(self, "تم", "تم تغيير نوع الفاتورة إلى المحل.")
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"تعذر التغيير:\n{e}")

        self.load_sales()
        try:
            self.changes_made.emit()
        except Exception:
            pass

    def _delete_sale(self):
        sale_id = self._get_selected_sale_id()
        if not sale_id:
            QMessageBox.warning(self, "تنبيه", "اختر فاتورة من الجدول أولاً.")
            return
        confirm = QMessageBox.question(self, "تأكيد", "هل أنت متأكد من حذف هذه الفاتورة؟ هذا الإجراء لا يمكن التراجع عنه.")
        if confirm == QMessageBox.Yes:
            try:
                self.db.delete_sale_by_id(sale_id)
                QMessageBox.information(self, "تم", "تم حذف الفاتورة.")
                self.load_sales()
                try:
                    self.changes_made.emit()
                except Exception:
                    pass
            except Exception as e:
                QMessageBox.critical(self, "خطأ", f"تعذر حذف الفاتورة:\n{e}")