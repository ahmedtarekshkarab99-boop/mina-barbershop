import os
import time
import json
from typing import Optional
from mina_al_arabi.db import RECEIPTS_DIR, DATA_DIR

try:
    import win32print
except Exception:
    win32print = None


STATE_PATH = os.path.join(DATA_DIR, "auto_print_state.json")
PRINTER_CFG_PATH = os.path.join(DATA_DIR, "printer.txt")


def load_selected_printer() -> Optional[str]:
    try:
        if os.path.exists(PRINTER_CFG_PATH):
            with open(PRINTER_CFG_PATH, "r", encoding="utf-8") as f:
                name = f.read().strip()
                return name or None
    except Exception:
        pass
    return None


def is_virtual_printer(name: str) -> bool:
    low = name.lower()
    return (not name.strip()) or any(b in low for b in ["pdf", "xps", "virtual"])


def raw_print_text(text: str, printer_name: Optional[str]) -> None:
    if win32print is None:
        raise RuntimeError("win32print غير متاح. رجاءً ثبّت pywin32: pip install pywin32")
    # Resolve printer
    if not printer_name:
        # Fallback to default printer
        try:
            printer_name = win32print.GetDefaultPrinter()
        except Exception:
            printer_name = None
    if not printer_name:
        raise RuntimeError("لا يوجد طابعة محددة أو افتراضية للطباعة.")
    if is_virtual_printer(printer_name):
        raise RuntimeError(f"تم اختيار طابعة غير مناسبة للطباعة الحرارية: {printer_name}")

    data = text.encode("cp1256", errors="replace")
    hPrinter = win32print.OpenPrinter(printer_name)
    try:
        job = win32print.StartDocPrinter(hPrinter, 1, ("AutoPrintReceipt", None, "RAW"))
        win32print.StartPagePrinter(hPrinter)
        win32print.WritePrinter(hPrinter, data)
        win32print.EndPagePrinter(hPrinter)
        win32print.EndDocPrinter(hPrinter)
    finally:
        win32print.ClosePrinter(hPrinter)


def load_state() -> dict:
    if os.path.exists(STATE_PATH):
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_state(state: dict) -> None:
    try:
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def main():
    os.makedirs(RECEIPTS_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    state = load_state()
    processed = set(state.get("processed_files", []))
    printer_name = load_selected_printer()

    print(f"[AutoPrint] Watching: {RECEIPTS_DIR}")
    print(f"[AutoPrint] Printer: {printer_name or '(default)'}")

    while True:
        try:
            files = [f for f in os.listdir(RECEIPTS_DIR) if f.lower().endswith(".txt")]
            files.sort()
            for fname in files:
                path = os.path.join(RECEIPTS_DIR, fname)
                if path in processed:
                    continue
                # Read content
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        text = f.read()
                except Exception:
                    # Try cp1256 if utf-8 fails
                    try:
                        with open(path, "r", encoding="cp1256") as f:
                            text = f.read()
                    except Exception as e:
                        print(f"[AutoPrint] Failed to read {fname}: {e}")
                        processed.add(path)
                        continue

                # Print
                try:
                    raw_print_text(text, printer_name)
                    print(f"[AutoPrint] Printed: {fname}")
                except Exception as e:
                    print(f"[AutoPrint] Failed to print {fname}: {e}")
                # Mark as processed regardless to avoid loops
                processed.add(path)
                state["processed_files"] = list(processed)
                save_state(state)
        except Exception as loop_err:
            print(f"[AutoPrint] Loop error: {loop_err}")
        time.sleep(2)


if __name__ == "__main__":
    main()