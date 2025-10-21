from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget,
    QListWidgetItem, QMessageBox, QAbstractItemView, QScrollArea, QGridLayout, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from datetime import datetime
import os

from mina_al_arabi.printing import print_receipt


def format_amount(amount: float) -> str:
    # Show whole numbers only
    return f"{int(round(amount))}"


def receipts_dir() -> str:
    base = os.path.join(os.path.dirname(__file__), "..", "data", "receipts")
    base = os.path.abspath(base)
    os.makedirs(base, exist_ok=True)
    return base


def format_time_ar(dt: datetime) -> str:
    h = dt.strftime("%I")
    m = dt.strftime("%M")
    ampm = dt.strftime("%p")
    suffix = "ص" if ampm == "AM" else "م"
    return f"{h}:{m} {suffix}"


class SalesDashboard(QWidget):
    def __init__(self):
        super().__init__()

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

        # Buyer: only customer for simplified build
        buyer_layout = QHBoxLayout()
        buyer_layout.addWidget(QLabel("اسم العميل"))
        self.customer_input = QLineEdit()
        self.customer_input.setFont(self.body_font)
        buyer_layout.addWidget(self.customer_input)
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

        # Seed demo data
        self.products = [("شامبو", 40, 20), ("جل شعر", 35, 30), ("بديل زيت", 25, 15), ("كريم", 50, 10)]

        self.load_products()

    def _update_buyer_fields(self):
        # Simplified: only customer name used
        self.submit_btn.setText("طباعة إيصال")

    

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
        for name, price, qty in self.products:
            label_text = f"{name}\n{format_amount(price)} ج.م\nالمتوفر: {qty}"
            btn = QPushButton(label_text)
            btn.setMinimumSize(260, 180)
            btn.setStyleSheet("QPushButton { background-color: #D4AF37; color: black; border-radius: 8px; font-size: 16px; } QPushButton:hover { background-color: #B8962D; }")
            btn.clicked.connect(lambda _, n=name, pr=price, q=qty: self.add_product_to_invoice(n, pr, q))
            self.products_grid.addWidget(btn, row, col)
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def add_product_to_invoice(self, name: str, price: float, qty_available: int):
        if qty_available <= 0:
            QMessageBox.warning(self, "تنبيه", f"المنتج {name} غير متوفر")
            return
        inv_item = QListWidgetItem(f"{name} - {format_amount(price)} ج.م")
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
            name, price, qty = self.invoice_list.item(i).data(Qt.UserRole)
            total += price * qty
            items.append((name, price, qty))

        customer_name = self.customer_input.text().strip() or "غير محدد"

        ts = datetime.now()
        basename = f"receipt_product_{ts.strftime('%Y%m%d_%H%M%S')}"
        txt_path = os.path.join(receipts_dir(), f"{basename}.txt")

        lines = [
            "صالون مينا العربي",
            f"التاريخ: {ts.strftime('%Y-%m-%d %I:%M %p')}",
            f"المشتري: {customer_name}",
            "-" * 30
        ]
        for name, price, qty in items:
            lines.append(f"{name} x{qty} - {format_amount(price)} ج.م")
        lines += ["-" * 30, f"الإجمالي: {format_amount(total)} ج.م"]
        receipt_text = "\n".join(lines)

        with open(txt_path, "w", encoding="utf-8") as ftxt:
            ftxt.write(receipt_text)

        try:
            print_receipt(receipt_text)
            QMessageBox.information(self, "تم", f"تم حفظ وطباعة الإيصال.\n{txt_path}")
        except Exception as e:
            QMessageBox.information(self, "تنبيه", f"تم حفظ الإيصال لكن فشلت الطباعة:\n{e}\n{txt_path}")

        # Reset
        self.invoice_list.clear()
        self.customer_input.clear()
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