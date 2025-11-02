from datetime import datetime
import os
from PySide6.QtGui import QFont, QTextDocument
from PySide6.QtPrintSupport import QPrinter

from mina_al_arabi.db import RECEIPTS_DIR

def _format_amount(amount: float) -> str:
    return f"{int(round(amount))}"

def _base_container_html(body_inner: str) -> str:
    return f"""
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="utf-8" />
        <style>
            body {{
                font-family: 'Cairo', 'Segoe UI', Tahoma, sans-serif;
                color: #111;
                margin: 24px;
                background: #ffffff;
            }}
            .container {{
                max-width: 820px;
                margin: 0 auto;
                border: 1px solid #D4AF37;
                padding: 22px 26px;
                background: #fff;
            }}
            .brand {{
                text-align: center;
                margin-bottom: 10px;
            }}
            .brand h1 {{
                margin: 0;
                font-size: 22px;
                color: #000;
                letter-spacing: 0.5px;
                font-weight: 700;
            }}
            .brand h2 {{
                margin: 5px 0 0 0;
                font-size: 13px;
                font-weight: 500;
                color: #555;
            }}
            .meta {{
                font-size: 14px;
                margin: 10px 0 16px 0;
                padding-bottom: 10px;
                border-bottom: 1px dashed #B8962D;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                font-size: 14px;
                margin-bottom: 12px;
            }}
            thead th {{
                background: #f7f4ee;
                color: #111;
                font-weight: 700;
                border-bottom: 1px solid #D4AF37;
                padding: 10px;
            }}
            td {{
                padding: 10px;
                border-bottom: 1px solid #eee;
            }}
            .cell-left {{ text-align: right; }}
            .cell-center {{ text-align: center; }}
            .cell-right {{ text-align: left; }}
            .totals {{
                margin-top: 10px;
                padding-top: 10px;
                border-top: 1px dashed #B8962D;
                font-size: 15px;
            }}
            .totals .line {{ display: flex; justify-content: space-between; margin: 6px 0; }}
            .totals .final {{ font-weight: 700; color: #000; }}
            .signature-area {{
                margin-top: 22px;
                text-align: center;
            }}
            .signature-line {{
                margin: 12px 0;
                font-size: 18px;
                font-weight: 600;
            }}
            .owner {{
                text-align: left;
                font-family: 'Segoe Script', 'Lucida Handwriting', cursive;
                font-size: 15px;
                color: #333;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="brand">
                <h1>صالون مينا العربي</h1>
                <h2>Salon Mina Al Arabi – Beauty &amp; Elegance</h2>
            </div>
            {body_inner}
            <div class="signature-area">
                <div class="signature-line">صالون مينا العربي اختيارك الافضل والاول</div>
                <div class="owner">Y. Abotaleb</div>
            </div>
        </div>
    </body>
    </html>
    """

def render_service_html(customer_name: str, employee_name: str, items: list[tuple[str, float, int]],
                        subtotal: float, discount_percent: int, final_total: float,
                        date_str: str | None = None) -> str:
    """
    items: list of tuples (service_name, unit_price, qty)
    """
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d %I:%M %p')

    rows_html = ""
    for name, price, qty in items:
        rows_html += f"""
        <tr>
            <td class="cell-left">{name}</td>
            <td class="cell-center">{qty}</td>
            <td class="cell-center">{_format_amount(price)}</td>
            <td class="cell-right">{_format_amount(price * qty)}</td>
        </tr>
        """

    body = f"""
    <div class="meta">
        التاريخ: {date_str} &nbsp;&nbsp; • &nbsp;&nbsp; المشتري: {customer_name} &nbsp;&nbsp; • &nbsp;&nbsp; الموظف: {employee_name}
    </div>
    <table>
        <thead>
            <tr>
                <th class="cell-left">الخدمة</th>
                <th class="cell-center">الكمية</th>
                <th class="cell-center">سعر الوحدة</th>
                <th class="cell-right">الإجمالي</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    <div class="totals">
        <div class="line"><span>الإجمالي قبل الخصم</span><span>{_format_amount(subtotal)} ج.م</span></div>
        <div class="line"><span>الخصم</span><span>{discount_percent}%</span></div>
        <div class="line final"><span>الإجمالي بعد الخصم</span><span>{_format_amount(final_total)} ج.م</span></div>
    </div>
    """
    return _base_container_html(body)

def render_product_html(customer_name: str, items: list[tuple[str, float, int]],
                        subtotal: float, discount_percent: int, final_total: float,
                        date_str: str | None = None) -> str:
    """
    items: list of tuples (product_name, unit_price, qty)
    """
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d %I:%M %p')

    rows_html = ""
    for name, price, qty in items:
        rows_html += f"""
        <tr>
            <td class="cell-left">{name}</td>
            <td class="cell-center">{qty}</td>
            <td class="cell-center">{_format_amount(price)}</td>
            <td class="cell-right">{_format_amount(price * qty)}</td>
        </tr>
        """

    body = f"""
    <div class="meta">
        التاريخ: {date_str} &nbsp;&nbsp; • &nbsp;&nbsp; المشتري: {customer_name}
    </div>
    <table>
        <thead>
            <tr>
                <th class="cell-left">المنتج</th>
                <th class="cell-center">الكمية</th>
                <th class="cell-center">سعر الوحدة</th>
                <th class="cell-right">الإجمالي</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    <div class="totals">
        <div class="line"><span>الإجمالي قبل الخصم</span><span>{_format_amount(subtotal)} ج.م</span></div>
        <div class="line"><span>الخصم</span><span>{discount_percent}%</span></div>
        <div class="line final"><span>الإجمالي بعد الخصم</span><span>{_format_amount(final_total)} ج.م</span></div>
    </div>
    """
    return _base_container_html(body)

def save_html(html: str, filename_base: str) -> str:
    os.makedirs(RECEIPTS_DIR, exist_ok=True)
    path = os.path.join(RECEIPTS_DIR, f"{filename_base}.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
        f.flush()
    return path

def print_a4_html(html: str) -> None:
    """Print HTML to default printer using A4-friendly settings."""
    printer = QPrinter()
    printer.setResolution(300)
    doc = QTextDocument()
    doc.setDefaultFont(QFont("Cairo", 14))
    doc.setHtml(html)
    doc.print_(printer)

def save_and_print_service(customer_name: str, employee_name: str, items: list[tuple[str, float, int]],
                           subtotal: float, discount_percent: int, final_total: float,
                           print_now: bool = True) -> str:
    html = render_service_html(customer_name, employee_name, items, subtotal, discount_percent, final_total)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"a4_service_{ts}"
    path = save_html(html, base)
    if print_now:
        print_a4_html(html)
    return path

def save_and_print_product(customer_name: str, items: list[tuple[str, float, int]],
                           subtotal: float, discount_percent: int, final_total: float,
                           print_now: bool = True) -> str:
    html = render_product_html(customer_name, items, subtotal, discount_percent, final_total)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = f"a4_product_{ts}"
    path = save_html(html, base)
    if print_now:
        print_a4_html(html)
    return path