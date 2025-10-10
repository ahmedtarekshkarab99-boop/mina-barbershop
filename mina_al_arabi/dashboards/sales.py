from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget,
    QListWidgetItem, QMessageBox, QAbstractItemView, QScrollArea, QGridLayout, QComboBox, QRadioButton, QInputDialog
)
from PySide6.QtCore import Qt, QSizeF
from PySide6.QtGui import QFont, QTextDocument
from PySide6.QtPrintSupport import QPrinter, QPrinterInfo
from datetime import datetime
from mina_al_arabi.db import Database, RECEIPTS_DIR, DATA_DIR
import os


def format_amount(amount: float) -> str:
    # Show whole numbers only
    return f"{int(round(amount))}"


def format_time_ar(dt: datetime) -> str:
    h = dt.strftime("%I")
    m = dt.strftime("%M")
    ampm = dt.strftime("%p")
    suffix = "ص" if ampm == "AM" else "م"
    return f"{h}:{m} {suffix}"


class SalesDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        self.header_font = QFont("Cairo", 18, QFont.Bold)
        self.body_font = QFont("Cairo", 14)

        root = QHBoxLayout(self)

        # Left: Products area (larger)
        left = QVBoxLayout()
        title_products = QLabel("المنتجات")
        title_products.setFont(self.header_font)
        left.addWidget(title_products)

        # Top control row: refresh
        ctrl_row = QHBoxLayout()
        refresh_btn = QPushButton("تحديث المنتجات")
        refresh_btn.setFont(self.body_font)
        refresh_btn.clicked.connect(self.load_products)
        ctrl_row.addWidget(refresh_btn)
        left.addLayout(ctrl_row)

        self.products_area = QScrollArea()
        self.products_area.setWidgetResizable(True)
        self.products_container = QWidget()
        self.products_grid = QGridLayout(self.products_container)
        self.products_grid.setSpacing(12)
        self.products_area.setWidget(self.products_container)
        # Give products area a bit more prominence
        self.products_area.setMinimumHeight(500)
        left.addWidget(self.products_area)

        # Right: Invoice area
        right = QVBoxLayout()
        title_invoice = QLabel("الفاتورة")
        title_invoice.setFont(self.header_font)
        right.addWidget(title_invoice)

        # Buyer selection - mutually exclusive
        buyer_layout = QHBoxLayout()

        self.customer_radio = QRadioButton("عميل")
        self.customer_radio.setChecked(True)
        self.store_radio = QRadioButton("المحل")
        self.employee_radio = QRadioButton("موظف")

        buyer_layout.addWidget(self.customer_radio)
        buyer_layout.addWidget(self.store_radio)
        buyer_layout.addWidget(self.employee_radio)

        buyer_layout.addWidget(QLabel("اسم العميل"))
        self.customer_input = QLineEdit()
        self.customer_input.setFont(self.body_font)
        buyer_layout.addWidget(self.customer_input)

        buyer_layout.addWidget(QLabel("الموظف"))
        self.employee_combo = QComboBox()
        self.employee_combo.setFont(self.body_font)
        buyer_layout.addWidget(self.employee_combo)

        # Link radios to enabling/disabling fields
        self.customer_radio.toggled.connect(self._update_buyer_fields)
        self.store_radio.toggled.connect(self._update_buyer_fields)
        self.employee_radio.toggled.connect(self._update_buyer_fields)

        right.addLayout(buyer_layout)

        self.invoice_list = QListWidget()
        self.invoice_list.setFont(self.body_font)
        self.invoice_list.setSelectionMode(QAbstractItemView.MultiSelection)
        right.addWidget(self.invoice_list)

        action_row = QHBoxLayout()
        remove_btn = QPushButton("حذف العنصر المحدد")
        remove_btn.setFont(self.body_font)
        remove_btn.clicked.connect(self.remove_selected_invoice_item)
        action_row.addWidget(remove_btn)

        choose_printer_btn = QPushButton("اختيار الطابعة")
        choose_printer_btn.setFont(self.body_font)
        choose_printer_btn.clicked.connect(self._choose_printer)
        action_row.addWidget(choose_printer_btn)

        test_print_btn = QPushButton("طباعة اختبار")
        test_print_btn.setFont(self.body_font)
        test_print_btn.clicked.connect(self._test_print)
        action_row.addWidget(test_print_btn)

        right.addLayout(action_row)

        totals_layout = QHBoxLayout()
        self.total_label = QLabel("الإجمالي: 0 ج.م")
        self.total_label.setFont(self.body_font)
        totals_layout.addWidget(self.total_label)
        right.addLayout(totals_layout)

        self.submit_btn = QPushButton("طباعة إيصال")
        self.submit_btn.setFont(self.body_font)
        self.submit_btn.clicked.connect(self._submit_invoice)
        right.addWidget(self.submit_btn)

        # Increase products section width relative to invoice
        root.addLayout(left, 3)
        root.addLayout(right, 1)

        # Printer config path
        self._printer_cfg_path = os.path.join(DATA_DIR, "printer.txt")
        self._selected_printer = self._load_saved_printer()

        self._load_employees()
        self._update_buyer_fields()
        self.load_products()

    def _update_buyer_fields(self):
        # Only one active at a time: customer, store, employee
        is_customer = self.customer_radio.isChecked()
        is_store = self.store_radio.isChecked()
        is_employee = self.employee_radio.isChecked()

        self.customer_input.setEnabled(is_customer)
        self.employee_combo.setEnabled(is_employee)

        # Button text: print receipt for customer, register invoice for store/employee
        self.submit_btn.setText("طباعة إيصال" if is_customer else "تسجيل الفاتورة")

    def _load_employees(self):
        self.employee_combo.clear()
        for eid, name in self.db.list_employees():
            self.employee_combo.addItem(name, eid)

    def load_products(self):
        # Clear grid
        while self.products_grid.count():
            item = self.products_grid.itemAt(0)
            w = item.widget()
            self.products_grid.removeItem(item)
            if w:
                w.setParent(None)
        # Add product buttons
        row, col = 0, 0
        for pid, name, price, qty in self.db.list_products():
            label_text = f"{name}\n{format_amount(price)} ج.م\nالمتوفر: {qty}"
            btn = QPushButton(label_text)
            # Make product buttons a bit larger
            btn.setMinimumSize(260, 180)
            btn.setStyleSheet("QPushButton { background-color: #D4AF37; color: black; border-radius: 8px; font-size: 16px; } QPushButton:hover { background-color: #B8962D; }")
            btn.clicked.connect(lambda _, p=pid, n=name, pr=price, q=qty: self.add_product_to_invoice(p, n, pr, q))
            self.products_grid.addWidget(btn, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def add_product_to_invoice(self, pid: int, name: str, price: float, qty_available: int):
        if qty_available <= 0:
            QMessageBox.warning(self, "تنبيه", f"المنتج {name} غير متوفر")
            return
        inv_item = QListWidgetItem(f"{name} - {format_amount(price)} ج.م")
        inv_item.setData(Qt.UserRole, (pid, name, price, 1))
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
            pid, name, price, qty = self.invoice_list.item(i).data(Qt.UserRole)
            total += price * qty
        self.total_label.setText(f"الإجمالي: {format_amount(total)} ج.م")

    def _submit_invoice(self):
        if self.invoice_list.count() == 0:
            QMessageBox.warning(self, "تنبيه", "الفاتورة فارغة")
            return

        total = 0.0
        items = []
        for i in range(self.invoice_list.count()):
            pid, name, price, qty = self.invoice_list.item(i).data(Qt.UserRole)
            total += price * qty
            items.append((pid, name, price, qty))

        # Determine buyer type
        is_customer = self.customer_radio.isChecked()
        is_store = self.store_radio.isChecked()
        is_employee = self.employee_radio.isChecked()

        customer_name = self.customer_input.text().strip() if is_customer else None
        employee_id = self.employee_combo.currentData() if is_employee else None

        buyer_type = "customer"
        is_shop = 0
        if is_store:
            buyer_type = "shop"
            is_shop = 1
        elif is_employee:
            buyer_type = "employee"

        sale_id = self.db.create_sale(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            employee_id=employee_id,
            customer_name=customer_name if is_customer else None,
            is_shop=is_shop,
            total=total,
            discount_percent=0,
            sale_type="product",
            buyer_type=buyer_type
        )
        for pid, name, price, qty in items:
            self.db.add_sale_item(sale_id, name, price, qty)
            # Decrease inventory
            self.db.update_product_qty(pid, -qty)

        # If shop is buyer, record as expense category "مشتريات للمحل" with product name in note
        if is_store:
            for _, name, price, qty in items:
                self.db.add_expense(category="مشتريات للمحل", amount=price * qty, note=name)

        # Action: for customer -> print receipt, otherwise -> just register (no receipt)
        if is_customer:
            ts = datetime.now()
            arabic_time = format_time_ar(ts)
            basename = f"receipt_product_{sale_id}_{ts.strftime('%Y%m%d_%H%M%S')}"
            txt_path = os.path.join(RECEIPTS_DIR, f"{basename}.txt")
            html_path = os.path.join(RECEIPTS_DIR, f"{basename}.html")

            # Build professional, large HTML receipt (RTL)
            rows_html = ""
            for _, name, price, qty in items:
                rows_html += f"<tr><td>{name}</td><td>{qty}</td><td>{format_amount(price)}</td><td>{format_amount(price * qty)}</td></tr>"

            receipt_html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<title>إيصال</title>
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
  <div class="meta">التاريخ: {ts.strftime('%Y-%m-%d')} {arabic_time}</div>
  <div class="meta">المشتري: {customer_name if customer_name else 'غير محدد'}</div>
  <div class="separator"></div>
  <table>
    <thead>
      <tr><th>المنتج</th><th>الكمية</th><th>سعر الوحدة (ج.م)</th><th>الإجمالي (ج.م)</th></tr>
    </thead>
    <tbody>
      {rows_html}
    </tbody>
  </table>
  <div class="total">الإجمالي: {format_amount(total)} ج.م</div>
  <div class="footer">شكراً لزيارتكم</div>
</body>
</html>"""

            # Also keep a plain text alongside
            lines = [
                "صالون مينا العربي",
                f"التاريخ: {ts.strftime('%Y-%m-%d')} {arabic_time}",
                f"المشتري: {customer_name if customer_name else 'غير محدد'}",
                "-" * 30
            ]
            for _, name, price, qty in items:
                lines.append(f"{name} x{qty} - {format_amount(price)} ج.م")
            lines += ["-" * 30, f"الإجمالي: {format_amount(total)} ج.م"]
            receipt_text = "\n".join(lines)

            with open(txt_path, "w", encoding="utf-8") as ftxt:
                ftxt.write(receipt_text)
            with open(html_path, "w", encoding="utf-8") as fhtml:
                fhtml.write(receipt_html)

            # Try to print the HTML (larger professional format)
            try:
                self._print_receipt_html(receipt_html)
                QMessageBox.information(self, "تم", f"تم حفظ وطباعة الإيصال.\nالمسار:\n{html_path}")
            except Exception as e:
                QMessageBox.information(self, "تنبيه", f"تم حفظ الإيصال لكن فشلت الطباعة:\n{e}\nالمسار:\n{html_path}")
        else:
            QMessageBox.information(self, "تم", "تم تسجيل الفاتورة بنجاح.")

        # Reset
        self.invoice_list.clear()
        self.customer_input.clear()
        self.customer_radio.setChecked(True)
        self._update_total()
        self.load_products()

    def _load_saved_printer(self) -> str | None:
        try:
            if os.path.exists(self._printer_cfg_path):
                with open(self._printer_cfg_path, "r", encoding="utf-8") as f:
                    name = f.read().strip()
                    return name or None
        except Exception:
            pass
        return None

    def _save_printer(self, name: str):
        try:
            with open(self._printer_cfg_path, "w", encoding="utf-8") as f:
                f.write(name or "")
        except Exception:
            pass

    def _choose_printer(self):
        printers = [p.printerName() for p in QPrinterInfo.availablePrinters()]
        if not printers:
            QMessageBox.warning(self, "تنبيه", "لا يوجد طابعات متاحة على النظام.")
            return
        current = self._selected_printer or (QPrinterInfo.defaultPrinter().printerName() if QPrinterInfo.defaultPrinter() else "")
        name, ok = QInputDialog.getItem(self, "اختيار الطابعة", "اختر الطابعة:", printers, printers.index(current) if current in printers else 0, False)
        if ok and name:
            self._selected_printer = name
            self._save_printer(name)
            QMessageBox.information(self, "تم", f"تم اختيار الطابعة:\n{name}")

    def _test_print(self):
        content = "اختبار طباعة\nصالون مينا العربي\nالخط كبير وواضح\n1234567890\n"
        try:
            self._print_receipt_html(f"<html dir='rtl'><body style='font-family:Cairo,Arial; font-size:18pt;'>{content.replace('\n','<br/>')}</body></html>")
            QMessageBox.information(self, "تم", "تم إرسال صفحة اختبار إلى الطابعة.")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"فشل إرسال صفحة الاختبار:\n{e}")

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

        # Render HTML with big fonts and force a wider page (approx 80mm roll)
        doc = QTextDocument()
        doc.setDefaultFont(QFont("Cairo", 16))
        doc.setHtml(html)
        # 80mm ≈ 3.15in; at 300 dpi => ~945 px width
        doc.setPageSize(QSizeF(945, 10000))
        doc.print_(printer)
        # Select Xprinter if available, otherwise use default printer
        printer_info = None
        for p in QPrinterInfo.availablePrinters():
            if "xprinter" in p.printerName().lower():
                printer()