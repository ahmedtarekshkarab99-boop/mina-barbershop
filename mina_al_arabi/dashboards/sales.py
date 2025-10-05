from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QListWidget,
    QListWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt
from datetime import datetime
from mina_al_arabi.db import Database, RECEIPTS_DIR
import os


class SalesDashboard(QWidget):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db

        layout = QVBoxLayout(self)

        # Buyer
        buyer_layout = QHBoxLayout()
        buyer_layout.addWidget(QLabel("اسم العميل"))
        self.customer_input = QLineEdit()
        buyer_layout.addWidget(self.customer_input)
        self.shop_checkbox = QCheckBox("المحل")
        buyer_layout.addWidget(self.shop_checkbox)
        layout.addLayout(buyer_layout)

        layout.addWidget(QLabel("المنتجات:"))
        self.products_list = QListWidget()
        self.products_list.setSelectionMode(self.products_list.MultiSelection)
        layout.addWidget(self.products_list)

        add_btn = QPushButton("إضافة المنتجات المحددة إلى الفاتورة")
        add_btn.clicked.connect(self.add_selected_products)
        layout.addWidget(add_btn)

        layout.addWidget(QLabel("الفاتورة:"))
        self.invoice_list = QListWidget()
        layout.addWidget(self.invoice_list)

        totals_layout = QHBoxLayout()
        self.total_label = QLabel("الإجمالي: 0 ج.م")
        totals_layout.addWidget(self.total_label)
        layout.addLayout(totals_layout)

        print_btn = QPushButton("طباعة إيصال")
        print_btn.clicked.connect(self.print_receipt)
        layout.addWidget(print_btn)

        self.load_products()

    def load_products(self):
        self.products_list.clear()
        for pid, name, price, qty in self.db.list_products():
            item = QListWidgetItem(f"{name} - {price:.2f} ج.م (المتوفر: {qty})")
            item.setData(Qt.UserRole, (pid, name, price, qty))
            self.products_list.addItem(item)

    def add_selected_products(self):
        for item in self.products_list.selectedItems():
            pid, name, price, qty_available = item.data(Qt.UserRole)
            if qty_available <= 0:
                QMessageBox.warning(self, "تنبيه", f"المنتج {name} غير متوفر")
                continue
            inv_item = QListWidgetItem(f"{name} - {price:.2f} ج.م")
            inv_item.setData(Qt.UserRole, (pid, name, price, 1))
            self.invoice_list.addItem(inv_item)
        self._update_total()

    def _update_total(self):
        total = 0.0
        for i in range(self.invoice_list.count()):
            pid, name, price, qty = self.invoice_list.item(i).data(Qt.UserRole)
            total += price * qty
        self.total_label.setText(f"الإجمالي: {total:.2f} ج.م")

    def print_receipt(self):
        if self.invoice_list.count() == 0:
            QMessageBox.warning(self, "تنبيه", "الفاتورة فارغة")
            return

        total = 0.0
        items = []
        for i in range(self.invoice_list.count()):
            pid, name, price, qty = self.invoice_list.item(i).data(Qt.UserRole)
            total += price * qty
            items.append((pid, name, price, qty))

        is_shop = 1 if self.shop_checkbox.isChecked() else 0
        customer_name = None if is_shop else self.customer_input.text().strip()

        sale_id = self.db.create_sale(
            date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            employee_id=None,
            customer_name=customer_name if customer_name else None,
            is_shop=is_shop,
            total=total,
            discount_percent=0,
            sale_type="product"
        )
        for pid, name, price, qty in items:
            self.db.add_sale_item(sale_id, name, price, qty)
            # Decrease inventory
            self.db.update_product_qty(pid, -qty)

        # If shop is buyer, record as expense
        if is_shop:
            self.db.add_expense(category="مشتريات للمحل", amount=total, note=f"فاتورة رقم {sale_id}")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(RECEIPTS_DIR, f"receipt_product_{sale_id}_{ts}.txt")
        lines = []
        lines.append("صالون مينا العربي")
        lines.append(f"التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        if is_shop:
            lines.append("المشتري: المحل")
        else:
            lines.append(f"المشتري: {customer_name if customer_name else 'غير محدد'}")
        lines.append("-" * 30)
        for _, name, price, qty in items:
            lines.append(f"{name} x{qty} - {price:.2f} ج.م")
        lines.append("-" * 30)
        lines.append(f"الإجمالي: {total:.2f} ج.م")
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        QMessageBox.information(self, "تم", f"تم حفظ الإيصال:\n{path}")
        self.invoice_list.clear()
        self.customer_input.clear()
        self.shop_checkbox.setChecked(False)
        self._update_total()
        self.load_products()