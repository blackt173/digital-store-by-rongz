import os
from fpdf import FPDF
from datetime import datetime
from utils import format_currency

def generate_invoice(transaction_id, customer_name, customer_id, product_name, quantity, total_amount, date_str=None):
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Ensure invoices directory exists
    if not os.path.exists("invoices"):
        os.makedirs("invoices")

    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, 'DigitalShop Invoice', ln=True, align='C')
    pdf.ln(10)

    # Invoice Details
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 10, 'Transaction ID:')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, str(transaction_id), ln=True)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 10, 'Date:')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, str(date_str), ln=True)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 10, 'Customer Name:')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, str(customer_name), ln=True)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(50, 10, 'Customer ID:')
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, str(customer_id), ln=True)

    pdf.ln(10)

    # Table Header
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(90, 10, 'Product', border=1)
    pdf.cell(30, 10, 'Quantity', border=1, align='C')
    pdf.cell(30, 10, 'Unit Price', border=1, align='C')
    pdf.cell(40, 10, 'Total', border=1, align='C')
    pdf.ln()

    # Table Content
    # We might need to encode product_name properly if it has weird chars, 
    # but Arial only supports Latin-1 by default. Let's replace non-ascii chars.
    safe_product_name = product_name.encode('ascii', 'ignore').decode('ascii')
    if not safe_product_name.strip():
        safe_product_name = "Digital Product"

    unit_price = total_amount / quantity if quantity > 0 else 0

    pdf.set_font("Arial", '', 12)
    pdf.cell(90, 10, safe_product_name, border=1)
    pdf.cell(30, 10, str(quantity), border=1, align='C')
    pdf.cell(30, 10, f"${unit_price:.2f}", border=1, align='C')
    pdf.cell(40, 10, f"${total_amount:.2f}", border=1, align='C')
    pdf.ln(20)

    # Summary
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(150, 10, 'Total Paid:', align='R')
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(40, 10, f"${total_amount:.2f}", align='C', ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(0, 128, 0) # Green
    pdf.cell(0, 10, 'STATUS: PAID', ln=True, align='C')
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, 'Thank you for your purchase!', ln=True, align='C')

    # Save PDF
    file_path = f"invoices/INV_{transaction_id}.pdf"
    pdf.output(file_path)
    
    return file_path
