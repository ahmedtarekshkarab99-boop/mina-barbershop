# Runtime hook to force import of dashboards so PyInstaller bundles them in the EXE.
# This runs at application start inside the frozen app.
try:
    import mina_al_arabi.dashboards.home  # noqa: F401
    import mina_al_arabi.dashboards.cashier  # noqa: F401
    import mina_al_arabi.dashboards.sales  # noqa: F401
    import mina_al_arabi.dashboards.inventory  # noqa: F401
    import mina_al_arabi.dashboards.expenses  # noqa: F401
    import mina_al_arabi.dashboards.attendance  # noqa: F401
    import mina_al_arabi.dashboards.reports  # noqa: F401
    import mina_al_arabi.dashboards.admin_report  # noqa: F401
    import mina_al_arabi.dashboards.shift  # noqa: F401
except Exception:
    # If any import fails here, the app should still continue; the main will show placeholders.
    pass