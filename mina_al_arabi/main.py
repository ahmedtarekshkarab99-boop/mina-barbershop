import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)

    # Build minimal app with Cashier and Sales tabs only
    try:
        from mina_al_arabi.dashboards.cashier import CashierDashboard
    except Exception:
        class CashierDashboard(QWidget):
            def __init__(self):
                super().__init__()
                lay = QVBoxLayout(self)
                lay.addWidget(QLabel("الكاشير غير متاح في هذه النسخة."))

    try:
        from mina_al_arabi.dashboards.sales import SalesDashboard
    except Exception:
        class SalesDashboard(QWidget):
            def __init__(self):
                super().__init__()
                lay = QVBoxLayout(self)
                lay.addWidget(QLabel("المبيعات غير متاحة في هذه النسخة."))

    window = QMainWindow()
    window.setWindowTitle("مدير صالون مينا العربي (نسخة مُعاد بناؤها)")
    window.resize(1200, 800)
    window.setLayoutDirection(Qt.RightToLeft)

    tabs = QTabWidget()
    window.setCentralWidget(tabs)

    tabs.addTab(CashierDashboard(), "الكاشير (الخدمات)")
    tabs.addTab(SalesDashboard(), "المبيعات")

    # Apply theme
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

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()