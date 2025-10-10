from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QListWidget,
    QListWidgetItem, QSpinBox, QLineEdit, QDialog, QFormLayout, QDialogButtonBox, QMessageBox,
    QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt, QSizeF
from PySide6.QtGui import QFont, QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrinterInfo
from datetime import datetime
from mina_al_arabi.db import Database, RECEIPTS_DIR, DATA_DIR
import os


def format_amount(amount: float) -> str:
    return f"{int(round(amount))}"


def format_time_ar(dt: datetime) -> str:
    h = dt.strftime("%I")
    m = dt.strftime("%M")
    ampm = dt.strftime("%p")
    suffix = "ص" if ampm == "AM" else "م"
    return f"{dt.strftime('%Y-%m-%d')} {h}:{m} {suffix}"


class AddServiceDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("إضافة خدمة")
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.price_input = QSpinBox()
        self.price_input.setMaximum(100000)
        self.price_input.setSuffix(" ج.م")
        layout.addRow("اسم الخدمة", self.name_input)
        layout.addRow("السعر", self.price_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.add)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def add(self):
        name = self.name_input.text().strip()
        price = float(self.price_input.value())
        if not name:
            QMessageBox.warning(self, "تنبيه", "من فضلك أدخل اسم الخدمة")
            return
        self.db.add_service(name, price)
        self.accept()


class AddEmployeeDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("إضافة موظف")
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        layout.addRow("اسم الموظف", self.name_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.add)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def add(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "من فضلك أدخل اسم الموظف")
            return
        self.db.add_employee(name)
        self.accept()


class CashierDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        # Fonts
        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        root = QHBoxLayout(self)

        # Left: Services (larger)
        left = QVBoxLayout()
        title_services = QLabel("الخدمات المتاحة")
        title_services.setFont(self.header_font)
        left.addWidget(title_services)

        self.services_area = QScrollArea()
        self.services_area.setWidgetResizable(True)
        self.services_container = QWidget()
        self.services_grid = QGridLayout(self.services_container)
        self.services_grid.setSpacing(12)
        self.services_area.setWidget(self.services_container)
        left.addWidget(self.services_area)

        # Right: Invoice
        right = QVBoxLayout()
        title_invoice = QLabel("الفاتورة")
        title_invoice.setFont(self.header_font)
        right.addWidget(title_invoice)

        self.invoice_list = QListWidget()
        self.invoice_list.setFont(self.body_font)
        right.addWidget(self.invoice_list)

        action_row = QHBoxLayout()
        remove_btn = QPushButton("حذف العنصر المحدد")
        remove_btn.clicked.connect(self.remove_selected_invoice_item)
        action_row.addWidget(remove_btn)
        right.addLayout(action_row)

        totals_layout = QVBoxLayout()
        self.total_before_label = QLabel("الإجمالي قبل الخصم: 0 ج.م")
        self.total_before_label.setFont(self.body_font)
        self.total_after_label = QLabel("الإجمالي بعد الخصم: 0 ج.م")
        self.total_after_label.setFont(self.body_font)

        discount_row = QHBoxLayout()
        discount_row.addWidget(QLabel("الخصم:"))
        self.discount_combo = QComboBox()
        self.discount_combo.addItems(["بدون خصم", "10%", "15%", "20%"])
        self.discount_combo.currentIndexChanged.connect(self._update_total)
        discount_row.addWidget(self.discount_combo)

        totals_layout.addWidget(self.total_before_label)
        totals_layout.addWidget(self.total_after_label)
        totals_layout.addLayout(discount_row)
        right.addLayout(totals_layout)

        print_btn = QPushButton("طباعة إيصال")
        print_btn.clicked.connect(self.print_receipt)
        right.addWidget(print_btn)

        # Initialize printer selection from saved config
        self._printer_cfg_path = os.path.join(DATA_DIR, "printer.txt")
        self._selected_printer = self._load_saved_printer()

        # Assemble
        root.addLayout(left, 2)   # larger services area
        root.addLayout(right, 1)

        # Top bar for employee selection
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("اختر الموظف:"))
        self.employee_combo = QComboBox()
        top_bar.addWidget(self.employee_combo)
        refresh_emp_btn = QPushButton("تحديث")
        refresh_emp_btn.clicked.connect(self._load_employees)
        top_bar.addWidget(refresh_emp_btn)
        right.insertLayout(0, top_bar)

        self._load_employees()
        self._load_services()

    def _load_employees(self):
        self.employee_combo.clear()
        for eid, name in self.db.list_employees():
            self.employee_combo.addItem(name, eid)

    def _load_services(self):
        # Clear grid
        while self.services_grid.count():
            item = self.services_grid.itemAt(0)
            w = item.widget()
            self.services_grid.removeItem(item)
            if w:
                w.setParent(None)
        # Add service buttons
        row, col = 0, 0
        for sid, name, price in self.db.list_services():
            btn = QPushButton(f"{name}\n{format_amount(price)} ج.م")
            btn.setMinimumSize(160, 120)
            btn.setStyleSheet("QPushButton { background-color: #D4AF37; color: black; border-radius: 8px; font-size: 16px; } QPushButton:hover { background-color: #B8962D; }")
            btn.clicked.connect(lambda _, n=name, p=price: self.add_service_to_invoice(n, p))
            self.services_grid.addWidget(btn, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def add_service_to_invoice(self, name: str, price: float):
        inv_item = QListWidgetItem(f"{name} - {price:.2f} ج.م")
        inv_item.setData(Qt.UserRole, (name, price, 1))
        self.invoice_list.addItem(inv_item)
        self._update_total()

    def remove_selected_invoice_item(self):
        for item in self.invoice_list.selectedItems():
            row = self.invoice_list.row(item)
            self.invoice_list.takeItem(row)
        self._update_total()

    def _update_total(self):
        total = 0.0
        for i in range(self.invoice_list.count()):
            name, price, qty = self.invoice_list.item(i).data(Qt.UserRole)
            total += price * qty

        discount_text = self.discount_combo.currentText()
        discount_percent = 0
        if discount_text.endswith("%") and discount_text != "بدون خصم":
            discount_percent = int(discount_text[:-1])

        total_after = total * (1 - discount_percent/100.0)
        self.total_before_label.setText(f"الإجمالي قبل الخصم: {total:.2f} ج.م")
        self.total_after_label.setText(f"الإجمالي بعد الخصم: {total_after:.2f} ج.م")

    def open_add_service_dialog(self):
        dlg = AddServiceDialog(self.db, self)
        if dlg.exec():
            self._load_services()

    def open_add_employee_dialog(self):
        dlg = AddEmployeeDialog(self.db, self)
        if dlg.exec():
            self._load_employees()

    def print_receipt(self):
        if self.invoice_list.count() == 0:
            QMessageBox.warning(self, "تنبيه", "الفاتورة فارغة")
            return

        employee_id = self.employee_combo.currentData()
        employee_name = self.employee_combo.currentText() if employee_id is not None else ""

        discount_text = self.discount_combo.currentText()
        discount_percent = 0
        if discount_text.endswith("%") and discount_text != "بدون خصم":
            discount_percent = int(discount_text[:-1])

        total = 0.0
        items = []
        for i in range(self.invoice_list.count()):
            name, price, qty = self.invoice_list.item(i).data(Qt.UserRole)
            total += price * qty
            items.append((name, price, qty))
        total_after = total * (1 - discount_percent/100.0)

        # Save in DB as a sale (service type)
        sale_id = self.db.create_sale(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            employee_id=employee_id,
            customer_name=None,
            is_shop=0,
            total=total_after,
            discount_percent=discount_percent,
            sale_type="service"
        )
        for name, price, qty in items:
            self.db.add_sale_item(sale_id, name, price, qty)

        # Build professional, large HTML receipt (RTL) and save both HTML and TXT
        ts = datetime.now()
        basename = f"receipt_service_{sale_id}_{ts.strftime('%Y%m%d_%H%M%S')}"
        txt_path = os.path.join(RECEIPTS_DIR, f"{basename}.txt")
        html_path = os.path.join(RECEIPTS_DIR, f"{basename}.html")

        rows_html = ""
        for name, price, qty in items:
            rows_html += f"<tr><td>{name}</td><td>{qty}</td><td>{format_amount(price)}</td><td>{format_amount(price * qty)}</td></tr>"

        receipt_html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>إيصال خدمة</title>
<style>
  body {{ font-family: 'Cairo', sans-serif; color: #000; margin: 24px; }}
  .brand {{ font-size: 28px; font-weight: 700; text-align: center; }}
  .meta {{ font-size: 16px; margin-top: 6px; text-align: center; }}
  .separator {{ margin: 12px 0; border-top: 2px solid #000; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 16px; }}
  th, td {{ border: 1px solid #000; padding: 8px; }}
  th {{ background: #f0f0f0; }}
  .total {{ font-size: 20px; font-weight: 700; text-align: left; margin-top: 12px; }}
  .footer {{ margin-top: 16px; font-size: 14px; text-align: center; color: #444; }}
</style>
</head>
<body>
  <div class="brand">صالون مينا العربي</div>
  <div class="meta">التاريخ: {format_time_ar(ts)}</div>
  <div class="meta">الموظف: {employee_name}</div>
  <div class="separator"></div>
  <table>
    <thead>
      <tr><th>الخدمة</th><th>الكمية</th><th>سعر الخدمة (ج.م)</th><th>الإجمالي (ج.م)</th></tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
  <div class="total">الإجمالي قبل الخصم: {format_amount(total)} ج.م</div>
  <div class="total">الخصم: {discount_percent}%</div>
  <div class="total">الإجمالي بعد الخصم: {format_amount(total_after)} ج.م</div>
  <div class="footer">شكراً لزيارتكم</div>
</body>
</html>"""

        # Plain text alongside
        lines = [
            "صالون مينا العربي",
            f"التاريخ: {format_time_ar(ts)}",
            f"الموظف: {employee_name}",
            "-" * 30
        ]
        for name, price, qty in items:
            lines.append(f"{name} x{qty} - {format_amount(price)} ج.م")
        lines += ["-" * 30, f"الإجمالي قبل الخصم: {format_amount(total)} ج.م", f"الخصم: {discount_percent}%", f"الإجمالي بعد الخصم: {format_amount(total_after)} ج.م"]
        with open(txt_path, "w", encoding="utf-8") as ftxt:
            ftxt.write("\n".join(lines))
        with open(html_path, "w", encoding="utf-8") as fhtml:
            fhtml.write(receipt_html)

        # Try to print the HTML (larger professional format)
        try:
            self._print_receipt_html(receipt_html)
            QMessageBox.information(self, "تم", f"تم حفظ وطباعة الإيصال.\nالمسار:\n{html_path}")
        except Exception as e:
            QMessageBox.information(self, "تنبيه", f"تم حفظ الإيصال لكن فشلت الطباعة:\n{e}\nالمسار:\n{html_path}")

        self.invoice_list.clear()
        self._update_total()

    def _load_saved_printer(self) -> str | None:
        try:
            if os.path.exists(self._printer_cfg_path):
                with open(self._printer_cfg_path, "r", encoding="utf-8") as f:
                    name = f.read().strip()
                    return name or None
        except Exception:
            pass
        return None

    def _print_receipt_html(self, html: str):
        # Select configured printer; if empty, pick Xprinter; else default
        printer_info = None
        if self._selected_printer:
            for p in QPrinterInfo.availablePrinters():
                if p.printerName() == self._selected_printer:
                    printer_info = p
                    break
        if printer_info is None:
            for p in QPrinterInfo.availablePrinters():
                if "xprinter" in p.printerName().lower():
                    printer_info = p
                    break
        if printer_info is None:
            try:
                printer_info = QPrinterInfo.defaultPrinter()
            except Exception:
                printer_info = None

        printer = QPrinter()
        if printer_info is not None:
            printer.setPrinterName(printer_info.printerName())
        # High resolution for clarity
        printer.setResolution(300)

        # Safety: avoid PDF/XPS/virtual printers that save to files
        try:
            pname = printer_info.printerName() if printer_info else ""
        except Exception:
            pname = ""
        low = pname.lower()
        if (not pname) or any(bad in low for bad in ["pdf", "xps", "virtual"]):
            raise Exception(f"تم اختيار طابعة غير مناسبة للطباعة الحرارية: {pname}. من فضلك اختر طابعة Xprinter من إدارة > اختيار الطابعة.")

        # Render HTML with big fonts and force a wider page (approx 80mm roll)
        doc = QTextDocument()
        doc.setDefaultFont(QFont("Cairo", 16))
        doc.setHtml(html)
        # 80mm ≈ 3.15in; at 300 dpi => ~945 px width