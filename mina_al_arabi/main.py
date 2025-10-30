import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from mina_al_arabi.db import Database
from mina_al_arabi.dashboards.home import HomeDashboard
from mina_al_arabi.dashboards.cashier import CashierDashboard
from mina_al_arabi.dashboards.sales import SalesDashboard
from mina_al_arabi.dashboards.inventory import InventoryDashboard
from mina_al_arabi.dashboards.expenses import ExpensesDashboard
from mina_al_arabi.dashboards.reports import ReportsDashboard
from mina_al_arabi.dashboards.admin_report import AdminReportDashboard
from mina_al_arabi.dashboards.shift import ShiftDashboard


def apply_theme():
    try:
        QApplication.instance().setFont(QFont("Cairo", 12))
    except Exception:
        QApplication.instance().setFont(QFont("", 12))
    style = """
    QWidget { background-color: #181818; color: #FFFFFF; }
    QMainWindow { background-color: #121212; }
    QTabWidget::pane { border: 1px solid #D4AF37; }
    QTabBar::tab { background: #121212; color: #FFFFFF; padding: 8px 16px; border: 1px solid #D4AF37; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; }
    QTabBar::tab:selected { background: #181818; }
    QPushButton { background-color: #D4AF37; color: black; border-radius: 8px; padding: 8px 14px; font-weight: 600; }
    QPushButton:hover { background-color: #B8962D; }
    QLabel { color: #FFFFFF; }
    QLineEdit, QSpinBox, QComboBox { background-color: #121212; color: #FFFFFF; border: 1px solid #D4AF37; border-radius: 6px; padding: 6px; }
    """
    QApplication.instance().setStyleSheet(style)


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    apply_theme()

    db = Database()
    db.ensure_schema()

    window = QMainWindow()
    window.setWindowTitle("مدير صالون مينا العربي")
    window.resize(1280, 850)
    window.setLayoutDirection(Qt.RightToLeft)

    tabs = QTabWidget()
    window.setCentralWidget(tabs)

    # Tabs (order requested)
    home_tab = HomeDashboard(db)
    cashier_tab = CashierDashboard(db)
    sales_tab = SalesDashboard(db)
    inventory_tab = InventoryDashboard(db)
    expenses_tab = ExpensesDashboard(db)
    reports_tab = ReportsDashboard(db)
    admin_tab = AdminReportDashboard(db)
    shift_tab = ShiftDashboard(db)

    tabs.addTab(home_tab, "الرئيسية")
    tabs.addTab(cashier_tab, "الكاشير")
    tabs.addTab(sales_tab, "المبيعات")
    tabs.addTab(inventory_tab, "المنتجات والخدمات")
    tabs.addTab(expenses_tab, "المصاريف")
    tabs.addTab(reports_tab, "التقارير")
    tabs.addTab(admin_tab, "إدارة")
    tabs.addTab(shift_tab, "الشفتات")

    # Management menu
    from PySide6.QtWidgets import QMenuBar, QMenu, QInputDialog, QMessageBox
    menubar = QMenuBar(window)
    window.setMenuBar(menubar)
    manage_menu = QMenu("إدارة", window)
    menubar.addMenu(manage_menu)

    # Add Service
    def add_service_action():
        name, ok = QInputDialog.getText(window, "إضافة خدمة", "اسم الخدمة:")
        if not (ok and name.strip()):
            return
        price_text, ok2 = QInputDialog.getText(window, "إضافة خدمة", "السعر (ج.م):")
        if not (ok2 and price_text.strip()):
            return
        try:
            price = float(price_text.strip())
            db.add_service(name.strip(), price)
            QMessageBox.information(window, "تم", "تمت إضافة الخدمة.")
            if cashier_tab:
                cashier_tab._load_services()
        except Exception as e:
            QMessageBox.critical(window, "خطأ", f"تعذرت إضافة الخدمة:\n{e}")

    act_add_service = manage_menu.addAction("إضافة خدمة")
    act_add_service.triggered.connect(add_service_action)

    # Add Employee
    def add_employee_action():
        name, ok = QInputDialog.getText(window, "إضافة موظف", "اسم الموظف:")
        if not (ok and name.strip()):
            return
        try:
            db.add_employee(name.strip())
            QMessageBox.information(window, "تم", "تمت إضافة الموظف.")
            if cashier_tab:
                cashier_tab._load_employees()
            if sales_tab:
                sales_tab._load_employees()
        except Exception as e:
            QMessageBox.critical(window, "خطأ", f"تعذرت إضافة الموظف:\n{e}")

    act_add_employee = manage_menu.addAction("إضافة موظف")
    act_add_employee.triggered.connect(add_employee_action)

    # Delete Service
    def delete_service_action():
        name, ok = QInputDialog.getText(window, "حذف خدمة", "اسم الخدمة:")
        if not (ok and name.strip()):
            return
        try:
            db.delete_service_by_name(name.strip())
            QMessageBox.information(window, "تم", "تم حذف الخدمة.")
            if cashier_tab:
                cashier_tab._load_services()
        except Exception as e:
            QMessageBox.critical(window, "خطأ", f"تعذر حذف الخدمة:\n{e}")

    act_delete_service = manage_menu.addAction("حذف خدمة")
    act_delete_service.triggered.connect(delete_service_action)

    # Delete Employee
    def delete_employee_action():
        name, ok = QInputDialog.getText(window, "حذف موظف", "اسم الموظف:")
        if not (ok and name.strip()):
            return
        try:
            db.delete_employee_by_name(name.strip())
            QMessageBox.information(window, "تم", "تم حذف الموظف.")
            if cashier_tab:
                cashier_tab._load_employees()
            if sales_tab:
                sales_tab._load_employees()
        except Exception as e:
            QMessageBox.critical(window, "خطأ", f"تعذر حذف الموظف:\n{e}")

    act_delete_employee = manage_menu.addAction("حذف موظف")
    act_delete_employee.triggered.connect(delete_employee_action)

    # Edit Service Price
    def edit_service_price_action():
        name, ok = QInputDialog.getText(window, "تعديل سعر خدمة", "اسم الخدمة:")
        if not (ok and name.strip()):
            return
        price_text, ok2 = QInputDialog.getText(window, "تعديل سعر خدمة", "السعر الجديد (ج.م):")
        if not (ok2 and price_text.strip()):
            return
        try:
            price = float(price_text.strip())
            db.update_service_price(name.strip(), price)
            QMessageBox.information(window, "تم", "تم تعديل السعر.")
            if cashier_tab:
                cashier_tab._load_services()
        except Exception as e:
            QMessageBox.critical(window, "خطأ", f"تعذر تعديل السعر:\n{e}")

    act_edit_service_price = manage_menu.addAction("تعديل سعر خدمة")
    act_edit_service_price.triggered.connect(edit_service_price_action)

    manage_menu.addSeparator()

    # Backup Data
    def backup_action():
        try:
            path = db.backup()
            QMessageBox.information(window, "تم", f"تم حفظ النسخة الاحتياطية:\n{path}")
        except Exception as e:
            QMessageBox.critical(window, "خطأ", f"تعذر إنشاء النسخة الاحتياطية:\n{e}")

    act_backup = manage_menu.addAction("نسخ احتياطي للبيانات")
    act_backup.triggered.connect(backup_action)

    # Update Program (Refresh)
    def refresh_action():
        try:
            if inventory_tab:
                inventory_tab.load_products()
            if expenses_tab:
                expenses_tab.load_expenses()
            if cashier_tab:
                cashier_tab._load_employees()
                cashier_tab._load_services()
            if sales_tab:
                sales_tab._load_employees()
                sales_tab.load_products()
            QMessageBox.information(window, "تم", "تم تحديث البرنامج.")
        except Exception:
            QMessageBox.information(window, "تم", "تم تحديث البرنامج.")

    act_refresh = manage_menu.addAction("تحديث البرنامج")
    act_refresh.triggered.connect(refresh_action)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()