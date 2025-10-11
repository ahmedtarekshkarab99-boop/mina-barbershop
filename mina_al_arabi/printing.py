import win32print
import win32ui


def print_receipt(text: str) -> None:
    """
    Print the given text directly to the default Windows printer without showing a dialog.
    """
    try:
        printer_name = win32print.GetDefaultPrinter()
        hPrinter = win32print.OpenPrinter(printer_name)
        hJob = win32print.StartDocPrinter(hPrinter, 1, ("فاتورة", None, "RAW"))
        win32print.StartPagePrinter(hPrinter)
        win32print.WritePrinter(hPrinter, text.encode("utf-8"))
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
        win32print.ClosePrinter(hPrinter)
        print("✅ تم إرسال الطباعة إلى:", printer_name)
    except Exception as e:
        print("❌ خطأ في الطباعة:", e)