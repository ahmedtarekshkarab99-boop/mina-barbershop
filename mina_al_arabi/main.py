import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QMessageBox, QMenuBar, QMenu
)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from mina_al_arabi.db import Database
from mina_al_arabi.dashboards.cashier import CashierDashboard
from mina_al_arabi.dashboards.inventory import InventoryDashboard
from mina_al_arabi.dashboards.sales import SalesDashboard
from mina_al_arabi.dashboards.expenses import ExpensesDashboard
from mina_al_arabi.dashboards.attendance import AttendanceDashboard


class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle("مدير صالون مينا العربي")
        self.resize(1100, 700)

        # RTL and font
        self.setLayoutDirection(Qt.RightToLeft)

        # Tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.cashier_tab = CashierDashboard(self.db)
        self.inventory_tab = InventoryDashboard(self.db)
        self.sales_tab = SalesDashboard(self.db)
        self.expenses_tab = ExpensesDashboard(self.db)
        self.attendance_tab = AttendanceDashboard(self.db)

        self.tabs.addTab(self.cashier_tab, "الكاشير (الخدمات)")
        self.tabs.addTab(self.inventory_tab, "المخزن")
        self.tabs.addTab(self.sales_tab, "المبيعات")
        self.tabs.addTab(self.expenses_tab, "المصاريف")
        self.tabs.addTab(self.attendance_tab, "الحضور")

        # Menu
        self._build_menu()

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

    def _backup_db(self):
        try:
            path = self.db.backup()
            QMessageBox.information(self, "تم", f"تم حفظ النسخة الاحتياطية:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "خطأ", f"حدث خطأ أثناء النسخ الاحتياطي:\n{e}")


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