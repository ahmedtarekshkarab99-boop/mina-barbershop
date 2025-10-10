# PyInstaller hook to ensure all mina_al_arabi submodules are collected
hiddenimports = [
    "mina_al_arabi.db",
    "mina_al_arabi.main",
    "mina_al_arabi.dashboards",
    "mina_al_arabi.dashboards.cashier",
    "mina_al_arabi.dashboards.inventory",
    "mina_al_arabi.dashboards.sales",
    "mina_al_arabi.dashboards.expenses",
    "mina_al_arabi.dashboards.attendance",
    "mina_al_arabi.dashboards.reports",
    "mina_al_arabi.dashboards.admin_report",
]