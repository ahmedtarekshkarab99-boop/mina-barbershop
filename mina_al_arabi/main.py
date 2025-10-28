import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

from mina_al_arabi.db import Database


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

    # Tabs (order requested) with safe imports to avoid startup crash
    try:
        from mina_al_arabi.dashboards.home import HomeDashboard
        tabs.addTab(HomeDashboard(db), "الرئيسية")
    except Exception:
        pass

    try:
        from mina_al_arabi.dashboards.cashier import CashierDashboard
        tabs.addTab(CashierDashboard(), "الكاشير")
    except Exception:
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
        ph = QWidget()
        lay = QVBoxLayout(ph)
        lay.addWidget(QLabel("شاشة الكاشير غير متاحة في هذه النسخة."))
        tabs.addTab(ph, "الكاشير")

    try:
        from mina_al_arabi.dashboards.sales import SalesDashboard
        tabs.addTab(SalesDashboard(), "المبيعات")
    except Exception:
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
        ph = QWidget()
        lay = QVBoxLayout(ph)
        lay.addWidget(QLabel("شاشة المبيعات غير متاحة في هذه النسخة."))
        tabs.addTab(ph, "المبيعات")

    try:
        from mina_al_arabi.dashboards.inventory import InventoryDashboard
        tabs.addTab(InventoryDashboard(db), "المنتجات والخدمات")
    except Exception:
        pass

    try:
        from mina_al_arabi.dashboards.expenses import ExpensesDashboard
        tabs.addTab(ExpensesDashboard(db), "المصاريف")
    except Exception:
        pass

    try:
        from mina_al_arabi.dashboards.reports import ReportsDashboard
        tabs.addTab(ReportsDashboard(db), "التقارير")
    except Exception:
        pass

    try:
        from mina_al_arabi.dashboards.admin_report import AdminReportDashboard
        tabs.addTab(AdminReportDashboard(db), "إدارة")
    except Exception:
        pass

    try:
        from mina_al_arabi.dashboards.shift import ShiftDashboard
        tabs.addTab(ShiftDashboard(db), "الشفتات")
    except Exception:
        pass

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()