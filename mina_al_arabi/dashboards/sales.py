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

        # Search + refresh
        ctrl_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث عن منتج...")
        self.search_input.textChanged.connect(self.load_products)
        ctrl_row.addWidget(self.search_input)
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

        buyer_layout = QHBoxLayout()
        buyer_layout.addWidget(QLabel("اسم العميل"))
        self.customer_input = QLineEdit()
        self.customer_input.setFont(self.body_font)
        buyer_layout.addWidget(self.customer_input)
        buyer_layout.addWidget(QLabel("الموظف"))
        self.employee_combo = QComboBox()
        buyer_layout.addWidget(self.employee_combo)
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

        totals_layout = QVBoxLayout()
        self.total_label = QLabel("الإجمالي: 0 ج.م")
        self.total_label.setFont(self.body_font)
        totals_layout.addWidget(self.total_label)

        # Discounts
        disc_row = QHBoxLayout()
        disc_row.addWidget(QLabel("الخصم:"))
        self.discount_combo = QComboBox()
        self.discount_combo.addItems(["بدون خصم", "10%", "20%", "30%", "40%", "50%"])
        self.discount_combo.currentIndexChanged.connect(self._update_total)
        disc_row.addWidget(self.discount_combo)

        # Hidden material deduction
        mat_row = QHBoxLayout()
        mat_row.addWidget(QLabel("خصم مواد (مخفي):"))
        self.material_deduction_input = QSpinBox()
        self.material_deduction_input.setMaximum(1000000)
        mat_row.addWidget(self.material_deduction_input)

        totals_layout.addLayout(disc_row)
        totals_layout.addLayout(mat_row)
        right.addLayout(totals_layout)

        self.submit_btn = QPushButton("طباعة إيصال")
        self.submit_btn.setFont(self.body_font)
        self.submit_btn.clicked.connect(self._submit_invoice)
        right.addWidget(self.submit_btn)

        # Increase products section width relative to invoice
        root.addLayout(left, 3)
        root.addLayout(right, 1)

        self._load_employees()
        self.load_products()

    def _load_employees(self):
        self.employee_combo.clear()
        try:
            rows = self.db.list_employees()
            for eid, name in rows:
                self.employee_combo.addItem(name, eid)
        except Exception:
            pass

    

    def load_products(self):
        # Clear grid
        while self.products_grid.count():
            item = self.products_grid.itemAt(0)
            w = item.widget()
            self.products_grid.removeItem(item)
            if w:
                w.setParent(None)
        # Query DB, reverse order, filter by search
        query = (self.search_input.text().strip() or "").lower()
        try:
            products = self.db.list_products()
        except Exception:
            products = []
        products = list(reversed(products))
        row, col = 0, 0
        for pid, name, price, qty in products:
            if query and (query not in name.lower()):
                continue
            label_text = f"{name}\n{format_amount(price)} ج.م\nالمتوفر: {qty}"
            btn = QPushButton(label_text)
            # Smaller icons than before to fit more items
            btn.setMinimumSize(220, 160)
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
        # Newest items first: insert at top
        self.invoice_list.insertItem(0, inv_item)
        self._update_total()

    def remove_selected_invoice_item(self):
        for item in self.invoice_list.selectedItems():
            row = self.invoice_list.row(item)
            self.invoice_list.takeItem(row)
        self._update_total()

    def _update_total(self):
        total = 0.0
        for i in range(self.invoice_list.count()):
            data = self.invoice_list.item(i).data(Qt.UserRole)
            if data is None:
                continue
            if len(data) == 3:
                name, price, qty = data
            else:
                pid, name, price, qty = data
            total += price * qty
        # apply visible discount
        discount_text = self.discount_combo.currentText()
        discount_percent = 0
        if discount_text.endswith("%") and discount_text != "بدون خصم":
            discount_percent = int(discount_text[:-1])
        total_after = total * (1 - discount_percent/100.0)
        self.total_label.setText(f"الإجمالي: {format_amount(total_after)} ج.م")

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

        discount_text = self.discount_combo.currentText()
        discount_percent = 0
        if discount_text.endswith("%") and discount_text != "بدون خصم":
            discount_percent = int(discount_text[:-1])
        material_deduction = float(self.material_deduction_input.value())

        customer_name = self.customer_input.text().strip() or "غير محدد"
        employee_id = self.employee_combo.currentData() if self.employee_combo.currentIndex() >= 0 else None

        # Link to active shift
        try:
            sh = self.db.get_active_shift()
            shift_id = sh[0] if sh else None
        except Exception:
            shift_id = None

        # Create sale in DB (product)
        try:
            sale_id = self.db.create_sale(
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                employee_id=employee_id,
                customer_name=customer_name,
                is_shop=0,
                total=total,
                discount_percent=discount_percent,
                sale_type="product",
                buyer_type="customer",
                material_deduction=material_deduction,
                shift_id=shift_id,
            )
            for pid, name, price, qty in items:
                self.db.add_sale_item(sale_id, name, price, qty)
                # Reduce inventory
                if pid:
                    try:
                        self.db.update_product_qty(pid, -qty)
                    except Exception:
                        pass
        except Exception:
            pass

        ts = datetime.now()
        basename = f"receipt_product_{ts.strftime('%Y%m%d_%H%M%S')}"
        txt_path = os.path.join(receipts_dir(), f"{basename}.txt")

        lines = [
            "صالون مينا العربي",
            f"التاريخ: {ts.strftime('%Y-%m-%d %I:%M %p')}",
            f"المشتري: {customer_name}",
            "-" * 30
        ]
        for _, name, price, qty in items:
            lines.append(f"{name} x{qty} - {format_amount(price)} ج.م")
        # visible discount effect
        total_after = total * (1 - discount_percent/100.0)
        lines += ["-" * 30, f"الإجمالي: {format_amount(total_after)} ج.م"]
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
        self.material_deduction_input.setValue(0)
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