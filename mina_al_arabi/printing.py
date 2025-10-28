import os
try:
    import win32print
except Exception:
    win32print = None


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
PRINTER_CFG_PATH = os.path.join(DATA_DIR, "printer.txt")


def _selected_printer_name() -> str:
    # Prefer saved printer name, otherwise XP-58IIH, otherwise default
    name = ""
    try:
        if os.path.exists(PRINTER_CFG_PATH):
            with open(PRINTER_CFG_PATH, "r", encoding="utf-8") as f:
                name = f.read().strip()
    except Exception:
        name = ""
    if win32print:
        if not name:
            # try XP-58IIH pattern
            try:
                printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
                for p in printers:
                    if "xp-58" in p.lower() or "xp-58iih" in p.lower() or "xprinter" in p.lower():
                        name = p
                        break
            except Exception:
                pass
        if not name:
            try:
                name = win32print.GetDefaultPrinter()
            except Exception:
                name = ""
    return name


def print_receipt(text: str) -> None:
    """
    Print the given text directly to a Windows thermal printer without showing a dialog.
    It will try the saved printer name (data/printer.txt), then XP-58IIH/Xprinter, then the system default.
    """
    if not win32print:
        raise RuntimeError("win32print غير متاح. رجاءً ثبّت pywin32: pip install pywin32")
    printer_name = _selected_printer_name()
    if not printer_name:
        raise RuntimeError("لا توجد طابعة افتراضية أو محفوظة متاحة للطباعة.")
    low = printer_name.lower()
    if any(x in low for x in ["pdf", "xps", "virtual"]):
        raise RuntimeError(f"تم اختيار طابعة غير مناسبة للطباعة الحرارية: {printer_name}")
    hPrinter = win32print.OpenPrinter(printer_name)
    try:
        hJob = win32print.StartDocPrinter(hPrinter, 1, ("فاتورة", None, "RAW"))
        win32print.StartPagePrinter(hPrinter)
        # cp1256 for Arabic stability on many thermal printers
        data = text.encode("cp1256", errors="replace")
        win32print.WritePrinter(hPrinter, data)
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
    finally:
        win32print.ClosePrinter(hPrinter)