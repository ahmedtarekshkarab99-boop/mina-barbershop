import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from mina_al_arabi.db import Database

# Hint imports for PyInstaller static analysis to ensure bundling of dashboards.
# Wrapped in try/except to avoid crashing if any module is missing during source runs.
try:
    import mina_al_arabi.dashboards.home as _dash_home
    import mina_al_arabi.dashboards.inventory as _dash_inventory
    import mina_al_arabi.dashboards.expenses as _dash_expenses
    import mina_al_arabi.dashboards.reports as _dash_reports
    import mina_al_arabi.dashboards.admin_report as _dash_admin
except Exception:
    pass


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

    # Tabs (order requested) with safe imports to avoid startup crash in EXE
    from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

    def add_tab_or_placeholder(factory, title):
        try:
            widget = factory()
            tabs.addTab(widget, title)
            return widget
        except Exception as e:
            ph = QWidget()
            lay = QVBoxLayout(ph)
            lay.addWidget(QLabel(f"تعذر تحميل \"{title}\": {e}"))
            tabs.addTab(ph, title)
            return None

    # Home
    def _home_factory():
        from mina_al_arabi.dashboards.home import HomeDashboard
        return HomeDashboard(db)
    home_tab = add_tab_or_placeholder(_home_factory, "الرئيسية")

    

    # Cashier
    def _cashier_factory():
        from mina_al_arabi.dashboards.cashier import CashierDashboard
        return CashierDashboard(db)
    cashier_tab = add_tab_or_placeholder(_cashier_factory, "الكاشير")

    # Sales
    def _sales_factory():
        from mina_al_arabi.dashboards.sales import SalesDashboard
        return SalesDashboard(db)
    sales_tab = add_tab_or_placeholder(_sales_factory, "المبيعات")

    # Inventory
    def _inventory_factory():
        from mina_al_arabi.dashboards.inventory import InventoryDashboard
        return InventoryDashboard(db)
    inventory_tab = add_tab_or_placeholder(_inventory_factory, "المنتجات والخدمات")

    # Expenses
    def _expenses_factory():
        from mina_al_arabi.dashboards.expenses import ExpensesDashboard
        return ExpensesDashboard(db)
    expenses_tab = add_tab_or_placeholder(_expenses_factory, "المصاريف")

    # Reports
    def _reports_factory():
        from mina_al_arabi.dashboards.reports import ReportsDashboard
        return ReportsDashboard(db)
    reports_tab = add_tab_or_placeholder(_reports_factory, "التقارير")

    # Admin
    def _admin_factory():
        from mina_al_arabi.dashboards.admin_report import AdminReportDashboard
        return AdminReportDashboard(db)
    admin_tab = add_tab_or_placeholder(_admin_factory, "إدارة")

    # Shift
    def _shift_factory():
        from mina_al_arabi.dashboards.shift import ShiftDashboard
        return ShiftDashboard(db)
    shift_tab = add_tab_or_placeholder(_shift_factory, "الشفتات")

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
            QMessageBox.information(window, "تم", "تم تحديث البرنامج.")
        except Exception:
            QMessageBox.information(window, "تم", "تم تحديث البرنامج.")

    act_refresh = manage_menu.addAction("تحديث البرنامج")
    act_refresh.triggered.connect(refresh_action)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()