"""領収書PDF生成関数"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session

from models import SalesInvoice, SalesPerson, ContractorInvoice, Contractor
from pdf_generator import setup_japanese_font, COMPANY_INFO


def generate_sales_receipt_pdf(invoice: SalesInvoice, db: Session) -> BytesIO:
    """販売員請求書の領収書PDF生成"""
    buffer = BytesIO()
    width, height = A4
    pdf = canvas.Canvas(buffer, pagesize=A4)
    
    # フォント設定
    font_name = setup_japanese_font()
    
    # ===== タイトル =====
    pdf.setFont(font_name, 24)
    pdf.drawCentredString(width / 2, height - 40*mm, "領 収 書")
    
    # ===== 宛先 =====
    sales_person = db.query(SalesPerson).filter(SalesPerson.id == invoice.sales_person_id).first()
    pdf.setFont(font_name, 14)
    pdf.drawString(30*mm, height - 60*mm, f"{sales_person.name if sales_person else ''} 様")
    
    # ===== 金額 =====
    pdf.setFont(font_name, 16)
    amount_text = f"¥{invoice.total_amount_inc_tax:,}"
    pdf.drawString(30*mm, height - 80*mm, f"金額: {amount_text}")
    
    # ===== 但し書き =====
    pdf.setFont(font_name, 11)
    note_text = invoice.note if invoice.note else "御品代として"
    pdf.drawString(30*mm, height - 95*mm, f"但し、{note_text}")
    
    # ===== 領収日 =====
    receipt_date = invoice.receipt_date if invoice.receipt_date else invoice.invoice_date
    if receipt_date:
        pdf.setFont(font_name, 11)
        pdf.drawString(30*mm, height - 110*mm, f"領収日: {receipt_date.strftime('%Y年%m月%d日')}")
    
    # ===== 発行者情報 =====
    issuer_y = height - 140*mm
    pdf.setFont(font_name, 11)
    pdf.drawString(30*mm, issuer_y, COMPANY_INFO['name'])
    pdf.drawString(30*mm, issuer_y - 7*mm, f"代表: {COMPANY_INFO['representative']}")
    pdf.drawString(30*mm, issuer_y - 14*mm, COMPANY_INFO['postal_code'])
    pdf.drawString(30*mm, issuer_y - 21*mm, COMPANY_INFO['address1'])
    pdf.drawString(30*mm, issuer_y - 28*mm, COMPANY_INFO['address2'])
    
    # ===== 備考 =====
    pdf.setFont(font_name, 9)
    pdf.drawString(30*mm, height - 200*mm, "※この領収書は再発行できません。大切に保管してください。")
    
    pdf.save()
    buffer.seek(0)
    
    return buffer


def generate_contractor_receipt_pdf(invoice: ContractorInvoice, db: Session) -> BytesIO:
    """委託先請求書の領収書PDF生成"""
    buffer = BytesIO()
    width, height = A4
    pdf = canvas.Canvas(buffer, pagesize=A4)
    
    # フォント設定
    font_name = setup_japanese_font()
    
    # ===== タイトル =====
    pdf.setFont(font_name, 24)
    pdf.drawCentredString(width / 2, height - 40*mm, "領 収 書")
    
    # ===== 宛先 =====
    contractor = db.query(Contractor).filter(Contractor.id == invoice.contractor_id).first()
    pdf.setFont(font_name, 14)
    pdf.drawString(30*mm, height - 60*mm, f"{contractor.name if contractor else ''} 様")
    
    # ===== 金額 =====
    pdf.setFont(font_name, 16)
    amount_text = f"¥{invoice.total_amount_inc_tax:,}"
    pdf.drawString(30*mm, height - 80*mm, f"金額: {amount_text}")
    
    # ===== 但し書き =====
    pdf.setFont(font_name, 11)
    note_text = invoice.note if invoice.note else "御品代として"
    pdf.drawString(30*mm, height - 95*mm, f"但し、{note_text}")
    
    # ===== 領収日 =====
    receipt_date = invoice.receipt_date if invoice.receipt_date else invoice.invoice_date
    if receipt_date:
        pdf.setFont(font_name, 11)
        pdf.drawString(30*mm, height - 110*mm, f"領収日: {receipt_date.strftime('%Y年%m月%d日')}")
    
    # ===== 発行者情報 =====
    issuer_y = height - 140*mm
    pdf.setFont(font_name, 11)
    pdf.drawString(30*mm, issuer_y, COMPANY_INFO['name'])
    pdf.drawString(30*mm, issuer_y - 7*mm, f"代表: {COMPANY_INFO['representative']}")
    pdf.drawString(30*mm, issuer_y - 14*mm, COMPANY_INFO['postal_code'])
    pdf.drawString(30*mm, issuer_y - 21*mm, COMPANY_INFO['address1'])
    pdf.drawString(30*mm, issuer_y - 28*mm, COMPANY_INFO['address2'])
    
    # ===== 備考 =====
    pdf.setFont(font_name, 9)
    pdf.drawString(30*mm, height - 200*mm, "※この領収書は再発行できません。大切に保管してください。")
    
    pdf.save()
    buffer.seek(0)
    
    return buffer
