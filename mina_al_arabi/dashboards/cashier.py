from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QListWidget,
    QListWidgetItem, QSpinBox, QLineEdit, QDialog, QFormLayout, QDialogButtonBox, QMessageBox,
    QScrollArea, QGridLayout
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from datetime import datetime
import os

from mina_al_arabi.printing import print_receipt


def format_amount(amount: float) -> str:
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
    return f"{dt.strftime('%Y-%m-%d')} {h}:{m} {suffix}"


class AddServiceDialogStandalone(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة خدمة")
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.price_input = QSpinBox()
        self.price_input.setMaximum(100000)
        self.price_input.setSuffix(" ج.م")
        layout.addRow("اسم الخدمة", self.name_input)
        layout.addRow("السعر", self.price_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def result(self):
        name = self.name_input.text().strip()
        price = float(self.price_input.value())
        return name, price


class AddEmployeeDialogStandalone(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("إضافة موظف")
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        layout.addRow("اسم الموظف", self.name_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def result(self):
        return self.name_input.text().strip()


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

        # Search bar
        search_row = QHBoxLayout()
        search_row.addWidget(QLabel("بحث:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("ابحث عن خدمة...")
        self.search_input.textChanged.connect(self._load_services)
        search_row.addWidget(self.search_input)
        left.addLayout(search_row)

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
        self.discount_combo.addItems(["بدون خصم", "10%", "20%", "30%", "40%", "50%"])
        self.discount_combo.currentIndexChanged.connect(self._update_total)
        discount_row.addWidget(self.discount_combo)

        # Hidden material deduction
        mat_row = QHBoxLayout()
        mat_row.addWidget(QLabel("خصم مواد (مخفي):"))
        self.material_deduction_input = QSpinBox()
        self.material_deduction_input.setMaximum(1000000)
        mat_row.addWidget(self.material_deduction_input)

        totals_layout.addWidget(self.total_before_label)
        totals_layout.addWidget(self.total_after_label)
        totals_layout.addLayout(discount_row)
        totals_layout.addLayout(mat_row)
        right.addLayout(totals_layout)

        print_btn = QPushButton("طباعة إيصال")
        print_btn.clicked.connect(self.print_receipt)
        right.addWidget(print_btn)

        # Assemble
        root.addLayout(left, 2)   # larger services area
        root.addLayout(right, 1)

        # Top bar for employee selection
        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("اختر الموظف:"))
        self.employee_combo = QComboBox()
        top_bar.addWidget(self.employee_combo)
        add_emp_btn = QPushButton("إضافة موظف")
        add_emp_btn.clicked.connect(self.open_add_employee_dialog)
        top_bar.addWidget(add_emp_btn)
        right.insertLayout(0, top_bar)

        self._load_employees()
        self._load_services()

    def _load_employees(self):
        self.employee_combo.clear()
        try:
            rows = self.db.list_employees()
            for eid, name in rows:
                self.employee_combo.addItem(name, eid)
        except Exception:
            pass

    def _load_services(self):
        # Clear grid
        while self.services_grid.count():
            item = self.services_grid.itemAt(0)
            w = item.widget()
            self.services_grid.removeItem(item)
            if w:
                w.setParent(None)
        # Query DB and filter by search
        query = (self.search_input.text().strip() or "").lower()
        try:
            services = self.db.list_services()
        except Exception:
            services = []
        # Reverse order so newest appears first
        services = list(reversed(services))
        row, col = 0, 0
        for sid, name, price in services:
            if query and (query not in name.lower()):
                continue
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
        dlg = AddServiceDialogStandalone(self)
        if dlg.exec():
            name, price = dlg.result()
            if name:
                try:
                    self.db.add_service(name, price)
                except Exception:
                    pass
                self._load_services()

    def open_add_employee_dialog(self):
        dlg = AddEmployeeDialogStandalone(self)
        if dlg.exec():
            name = dlg.result()
            if name:
                try:
                    self.db.add_employee(name)
                except Exception:
                    pass
                self._load_employees()

    def print_receipt(self):
        if self.invoice_list.count() == 0:
            QMessageBox.warning(self, "تنبيه", "الفاتورة فارغة")
            return

        employee_id = self.employee_combo.currentData() if self.employee_combo.currentIndex() >= 0 else None
        employee_name = self.employee_combo.currentText() if self.employee_combo.currentIndex() >= 0 else ""

        discount_text = self.discount_combo.currentText()
        discount_percent = 0
        if discount_text.endswith("%") and discount_text != "بدون خصم":
            discount_percent = int(discount_text[:-1])

        material_deduction = float(self.material_deduction_input.value())

        total = 0.0
        items = []
        for i in range(self.invoice_list.count()):
            name, price, qty = self.invoice_list.item(i).data(Qt.UserRole)
            total += price * qty
            items.append((name, price, qty))
        total_after = total * (1 - discount_percent/100.0)

        # Link to active shift
        try:
            sh = self.db.get_active_shift()
            shift_id = sh[0] if sh else None
        except Exception:
            shift_id = None

        # Create sale in DB (service)
        try:
            sale_id = self.db.create_sale(
                date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                employee_id=employee_id,
                customer_name=None,
                is_shop=0,
                total=total,
                discount_percent=discount_percent,
                sale_type="service",
                buyer_type="customer",
                material_deduction=material_deduction,
                shift_id=shift_id,
            )
            for name, price, qty in items:
                self.db.add_sale_item(sale_id, name, price, qty)
        except Exception:
            pass

        # Build simple text receipt (material deduction hidden)
        ts = datetime.now()
        lines = []
        lines.append("صالون مينا العربي")
        lines.append(f"التاريخ: {ts.strftime('%Y-%m-%d %I:%M %p')}")
        lines.append(f"الموظف: {employee_name}")
        lines.append("-" * 30)
        for name, price, qty in items:
            lines.append(f"{name} x{qty} - {format_amount(price)} ج.م")
        lines.append("-" * 30)
        lines.append(f"الإجمالي قبل الخصم: {format_amount(total)} ج.م")
        lines.append(f"الخصم: {discount_percent}%")
        lines.append(f"الإجمالي بعد الخصم: {format_amount(total_after)} ج.م")
        text = "\n".join(lines)

        # Save copy
        path = os.path.join(receipts_dir(), f"receipt_service_{ts.strftime('%Y%m%d_%H%M%S')}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

        # Print directly to default Windows printer
        try:
            print_receipt(text)
            QMessageBox.information(self, "تم", f"تم حفظ وطباعة الإيصال.\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "تنبيه", f"تم حفظ الإيصال لكن فشلت الطباعة:\n{e}\n{path}")

        self.invoice_list.clear()
        self.material_deduction_input.setValue(0)
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
        doc.setPageSize(QSizeF(945, 10000))
        doc.print_(printer)

    def _raw_print_text(self, text: str):
        # Try to send raw text to Windows spooler using pywin32 if available
        try:
            import win32print
        except Exception as e:
            raise Exception(f\"لا يمكن الطباعة الخام لأن win32print غير متاح: {e}\")
        # Resolve printer name
        name = self._selected_printer
        if not name:
            # try Xprinter first
            for p in QPrinterInfo.availablePrinters():
                if \"xprinter\" in p.printerName().lower():
                    name = p.printerName()
                    break
        if not name:
            # default windows printer
            try:
                name = QPrinterInfo.defaultPrinter().printerName()
            except Exception:
                name = None
        if not name:
            raise Exception(\"لا يوجد طابعة مختارة أو افتراضية للطباعة الخام.\")
        # Avoid virtual printers
        low = name.lower()
        if any(bad in low for bad in [\"pdf\", \"xps\", \"virtual\"]) or not name.strip():
            raise Exception(f\"تم اختيار طابعة غير مناسبة للطباعة الخام: {name}\")

        # Encode text for Arabic (Windows-1256)
        data = text.encode(\"cp1256\", errors=\"replace\")
        hPrinter = win32print.OpenPrinter(name)
        try:
            job = win32print.StartDocPrinter(hPrinter, 1, (\"Receipt\", None, \"RAW\"))
            win32print.StartPagePrinter(hPrinter)
            win32print.WritePrinter(hPrinter, data)
            win32print.EndPagePrinter(hPrinter)
            win32print.EndDocPrinter(hPrinter)
        finally:
            win32print.ClosePrinter(hPrinter)
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