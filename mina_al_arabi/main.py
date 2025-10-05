import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QMessageBox, QMenuBar, QMenu, QInputDialog
)
from PySide6.QtGui import QAction, QFont
from PySide6.QtCore import Qt
from mina_al_arabi.db import Database
from mina_al_arabi.dashboards.cashier import CashierDashboard
from mina_al_arabi.dashboards.inventory import InventoryDashboard
from mina_al_arabi.dashboards.sales import SalesDashboard
from mina_al_arabi.dashboards.expenses import ExpensesDashboard
from mina_al_arabi.dashboards.attendance import AttendanceDashboard
from mina_al_arabi.dashboards.reports import ReportsDashboard


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle("مدير صالون مينا العربي")
        self.resize(1200, 800)

        # RTL
        self.setLayoutDirection(Qt.RightToLeft)

        # Tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.cashier_tab = CashierDashboard(self.db)
        self.inventory_tab = InventoryDashboard(self.db)
        self.sales_tab = SalesDashboard(self.db)
        self.expenses_tab = ExpensesDashboard(self.db)
        self.attendance_tab = AttendanceDashboard(self.db)
        self.reports_tab = ReportsDashboard(self.db)

        self.tabs.addTab(self.cashier_tab, "الكاشير (الخدمات)")
        self.tabs.addTab(self.inventory_tab, "المخزن")
        self.tabs.addTab(self.sales_tab, "المبيعات")
        self.tabs.addTab(self.expenses_tab, "المصاريف")
        self.tabs.addTab(self.attendance_tab, "الحضور")
        self.tabs.addTab(self.reports_tab, "التقارير")

        # Menu
        self._build_menu()

        # Dark premium theme stylesheet (black/gold/white)
        self._apply_theme()

    def _build_menu(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        manage_menu = QMenu("إدارة", self)
        menubar.addMenu(manage_menu)

        add_service_action = QAction("إضافة خدمة", self)
        add_service_action.triggered.connect(self.cashier_tab.open_add_service_dialog)
        manage_menu.addAction(add_service_action)

        add_employee_action = QAction("إضافة موظف", self)
        add_employee_action.triggered.connect(self.cashier_tab.open_add_employee_dialog)
        manage_menu.addAction(add_employee_action)

        backup_action = QAction("نسخ احتياطي للبيانات", self)
        backup_action.triggered.connect(self._backup_db)
        manage_menu.addAction(backup_action)

        manage_menu.addSeparator()

        delete_service_action = QAction("حذف خدمة", self)
        delete_service_action.triggered.connect(self._delete_service)
        manage_menu.addAction(delete_service_action)

        delete_employee_action = QAction("حذف موظف", self)
        delete_employee_action.triggered.connect(self._delete_employee)
        manage_menu.addAction(delete_employee_action)

        edit_service_price_action = QAction("تعديل سعر خدمة", self)
        edit_service_price_action.triggered.connect(self._edit_service_price)
        manage_menu.addAction(edit_service_price_action)

    def _apply_theme(self):
        # Set global font preference
        try:
            QApplication.instance().setFont(QFont("Cairo", 12))
        except Exception:
            QApplication.instance().setFont(QFont("", 12))
        # Stylesheet
        style = """
        QWidget { background-color: #181818; color: #FFFFFF; }
        QMainWindow { background-color: #121212; }
        QTabWidget::pane { border: 1px solid #D4AF37; }
        QTabBar::tab { background: #121212; color: #FFFFFF; padding: 8px 16px; border: 1px solid #D4AF37; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; }
        QTabBar::tab:selected { background: #181818; }
        QPushButton { background-color: #D4AF37; color: black; border-radius: 8px; padding: 8px 14px; font-weight: 600; }
        QPushButton:hover { background-color: #B8962D; }
        QLabel { color: #FFFFFF; }
        QMenuBar { background-color: #121212; color: #FFFFFF; }
        QMenu { background-color: #121212; color: #FFFFFF; border: 1px solid #D4AF37; }
        QLineEdit, QSpinBox, QComboBox { background-color: #121212; color: #FFFFFF; border: 1px solid #D4AF37; border-radius: 6px; padding: 6px; }
        QCheckBox { color: #FFFFFF; }
        QTableWidget { background-color: #181818; color: #FFFFFF; gridline-color: #D4AF37; }
        QHeaderView::section { background-color: #121212; color: #FFFFFF; border: 1px solid #D4AF37; }
        """
        QApplication.instance().setStyleSheet(style)

    def _backup_db(self):
        try:
            path = self.db.backup()
            QMessageBox.information(self, "تم", f"تم حفظ النسخة الاحتياطية:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء النسخ الاحتياطي:\n{e}")

    def _delete_service(self):
        name, ok = QInputDialog.getText(self, "حذف خدمة", "اسم الخدمة:")
        if ok and name.strip():
            self.db.delete_service_by_name(name.strip())
            QMessageBox.information(self, "تم", "تم حذف الخدمة")
            self.cashier_tab._load_services()

    def _delete_employee(self):
        name, ok = QInputDialog.getText(self, "حذف موظف", "اسم الموظف:")
        if ok and name.strip():
            self.db.delete_employee_by_name(name.strip())
            QMessageBox.information(self, "تم", "تم حذف الموظف")
            self.cashier_tab._load_employees()
            self.sales_tab._load_employees()

    def _edit_service_price(self):
        name, ok = QInputDialog.getText(self, "تعديل سعر خدمة", "اسم الخدمة:")
        if not (ok and name.strip()):
            return
        price_text, ok2 = QInputDialog.getText(self, "تعديل سعر خدمة", "السعر الجديد (ج.م):")
        if ok2 and price_text.strip():
            try:
                new_price = float(price_text.strip())
                self.db.update_service_price(name.strip(), new_price)
                QMessageBox.information(self, "تم", "تم تعديل السعر")
                self.cashier_tab._load_services()
            except ValueError:
                QMessageBox.warning(self, "خطأ", "من فضلك أدخل رقمًا صحيحًا للسعر")


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)

    db = Database()
    db.ensure_schema()

    window = MainWindow(db)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()