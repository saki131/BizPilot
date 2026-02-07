"""PDF生成ヘルパー - 販売員請求書鏡テンプレート準拠"""
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black, white
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os

from models import SalesInvoice, SalesInvoiceDetail, Product, SalesPerson, DiscountRate, ContractorInvoice, ContractorInvoiceDetail, Contractor

# 会社情報（固定値）
COMPANY_INFO = {
    "name": "[COMPANY_NAME]",
    "representative": "[COMPANY_REPRESENTATIVE]",
    "postal_code": "[COMPANY_POSTAL_CODE]",
    "address1": "[COMPANY_ADDRESS1]",
    "address2": "[COMPANY_ADDRESS2]",
}

# 振込先情報
BANK_INFO = {
    "bank_name": "[BANK_NAME]",
    "branch_name": "[BANK_BRANCH_NAME]",
    "account_type": "普通",
    "account_number": "420025",
    "account_holder": "[BANK_ACCOUNT_HOLDER]",
    "yucho_symbol": "[BANK_YUCHO_SYMBOL]",
    "yucho_number": "[BANK_ACCOUNT_NUMBER]1",
}

def setup_japanese_font():
    """日本語フォントの設定"""
    font_name = 'Helvetica'
    try:
        # Windows環境: MS ゴシック
        font_path = "C:\\Windows\\Fonts\\msgothic.ttc"
        pdfmetrics.registerFont(TTFont('Japanese', font_path))
        font_name = 'Japanese'
        print(f"Japanese font loaded: {font_path}")
    except:
        try:
            # Linux環境用フォント（IPAゴシック - TTF形式）
            font_candidates = [
                "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
                "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
                "/usr/share/fonts/truetype/ipafont/ipag.ttf",
                "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf",
                "/usr/share/fonts/truetype/ipafont/ipam.ttf",
            ]
            for fp in font_candidates:
                if os.path.exists(fp):
                    pdfmetrics.registerFont(TTFont('Japanese', fp))
                    font_name = 'Japanese'
                    print(f"Japanese font loaded: {fp}")
                    break
            if font_name == 'Helvetica':
                print("WARNING: Japanese font not found, using Helvetica")
        except Exception as e:
            print(f"Font loading error: {e}")
    return font_name


def generate_sales_receipt_pdf(invoice: SalesInvoice, db: Session) -> BytesIO:
    """販売員用領収書PDF生成
    
    Args:
        invoice: 請求書データ
        db: データベースセッション
        
    Returns:
        BytesIO: PDF データ
    """
    # データ取得
    sales_person = db.query(SalesPerson).filter(
        SalesPerson.id == invoice.sales_person_id
    ).first()
    
    # PDF生成（横向き）
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # フォント設定
    font_name = setup_japanese_font()
    
    # タイトル
    pdf.setFont(font_name, 24)
    title = "領 収 書"
    title_width = pdf.stringWidth(title, font_name, 24)
    pdf.drawString((width - title_width) / 2, height - 40*mm, title)
    
    # 宛名
    pdf.setFont(font_name, 14)
    sales_person_name = sales_person.name if sales_person else ""
    pdf.drawString(30*mm, height - 70*mm, f"{sales_person_name}　様")
    
    # 金額ボックス
    box_y = height - 100*mm
    box_height = 20*mm
    box_width = 140*mm
    box_x = (width - box_width) / 2
    
    pdf.setLineWidth(2)
    pdf.rect(box_x, box_y, box_width, box_height, stroke=1, fill=0)
    pdf.setLineWidth(0.5)
    
    pdf.setFont(font_name, 22)
    total_amount = f"¥{invoice.total_amount_inc_tax:,}-"
    pdf.drawRightString(box_x + box_width - 10*mm, box_y + 6*mm, total_amount)
    
    # 但し書き
    pdf.setFont(font_name, 11)
    note_text = invoice.note if invoice.note else "御品代として"
    pdf.drawString(30*mm, box_y - 15*mm, f"但し、{note_text}")
    
    # 領収日
    receipt_date = invoice.receipt_date if invoice.receipt_date else invoice.invoice_date
    if isinstance(receipt_date, str):
        receipt_date = datetime.strptime(receipt_date, "%Y-%m-%d").date()
    pdf.drawString(30*mm, box_y - 30*mm, f"領収日: {receipt_date.strftime('%Y年%m月%d日')}")
    
    # 発行者情報
    issuer_y = box_y - 60*mm
    pdf.setFont(font_name, 11)
    pdf.drawString(30*mm, issuer_y, COMPANY_INFO["name"])
    pdf.setFont(font_name, 9)
    pdf.drawString(30*mm, issuer_y - 7*mm, f"代表者: {COMPANY_INFO['representative']}")
    pdf.drawString(30*mm, issuer_y - 14*mm, COMPANY_INFO["postal_code"])
    pdf.drawString(30*mm, issuer_y - 21*mm, COMPANY_INFO["address1"])
    pdf.drawString(30*mm, issuer_y - 28*mm, COMPANY_INFO["address2"])
    
    # ハンコ画像を追加（会社名の一部に重ねる）
    stamp_path = os.path.join(os.path.dirname(__file__), "static", "stamp.png")
    if os.path.exists(stamp_path):
        # 代表者名の横にハンコを配置（文字に少しかかるように）
        stamp_size = 25*mm
        stamp_x = 55*mm  # 会社名の右側
        stamp_y = issuer_y - 15*mm
        pdf.drawImage(stamp_path, stamp_x, stamp_y, width=stamp_size, height=stamp_size, mask='auto')
    
    # フッター
    footer_y = 30*mm
    pdf.setFont(font_name, 8)
    pdf.drawCentredString(width / 2, footer_y, "上記の金額を正に領収いたしました。")
    pdf.drawCentredString(width / 2, footer_y - 7*mm, "※再発行はいたしません")
    
    pdf.save()
    buffer.seek(0)
    
    return buffer


def generate_contractor_receipt_pdf(invoice: ContractorInvoice, db: Session) -> BytesIO:
    """委託先用領収書PDF生成
    
    Args:
        invoice: 委託先請求書データ
        db: データベースセッション
        
    Returns:
        BytesIO: PDF データ
    """
    # データ取得
    contractor = db.query(Contractor).filter(
        Contractor.id == invoice.contractor_id
    ).first()
    
    # PDF生成（横向き）
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # フォント設定
    font_name = setup_japanese_font()
    
    # タイトル
    pdf.setFont(font_name, 24)
    title = "領 収 書"
    title_width = pdf.stringWidth(title, font_name, 24)
    pdf.drawString((width - title_width) / 2, height - 40*mm, title)
    
    # 宛名
    pdf.setFont(font_name, 14)
    contractor_name = contractor.name if contractor else ""
    pdf.drawString(30*mm, height - 70*mm, f"{contractor_name}　様")
    
    # 金額ボックス
    box_y = height - 100*mm
    box_height = 20*mm
    box_width = 140*mm
    box_x = (width - box_width) / 2
    
    pdf.setLineWidth(2)
    pdf.rect(box_x, box_y, box_width, box_height, stroke=1, fill=0)
    pdf.setLineWidth(0.5)
    
    pdf.setFont(font_name, 22)
    total_amount = f"¥{invoice.total_amount_inc_tax:,}-"
    pdf.drawRightString(box_x + box_width - 10*mm, box_y + 6*mm, total_amount)
    
    # 但し書き
    pdf.setFont(font_name, 11)
    note_text = invoice.note if invoice.note else "御品代として"
    pdf.drawString(30*mm, box_y - 15*mm, f"但し、{note_text}")
    
    # 領収日
    receipt_date = invoice.receipt_date if invoice.receipt_date else invoice.invoice_date
    if isinstance(receipt_date, str):
        receipt_date = datetime.strptime(receipt_date, "%Y-%m-%d").date()
    pdf.drawString(30*mm, box_y - 30*mm, f"領収日: {receipt_date.strftime('%Y年%m月%d日')}")
    
    # 発行者情報
    issuer_y = box_y - 60*mm
    pdf.setFont(font_name, 11)
    pdf.drawString(30*mm, issuer_y, COMPANY_INFO["name"])
    pdf.setFont(font_name, 9)
    pdf.drawString(30*mm, issuer_y - 7*mm, f"代表者: {COMPANY_INFO['representative']}")
    pdf.drawString(30*mm, issuer_y - 14*mm, COMPANY_INFO["postal_code"])
    pdf.drawString(30*mm, issuer_y - 21*mm, COMPANY_INFO["address1"])
    pdf.drawString(30*mm, issuer_y - 28*mm, COMPANY_INFO["address2"])
    
    # ハンコ画像を追加（会社名の一部に重ねる）
    stamp_path = os.path.join(os.path.dirname(__file__), "static", "stamp.png")
    if os.path.exists(stamp_path):
        # 代表者名の横にハンコを配置（文字に少しかかるように）
        stamp_size = 25*mm
        stamp_x = 55*mm  # 会社名の右側
        stamp_y = issuer_y - 15*mm
        pdf.drawImage(stamp_path, stamp_x, stamp_y, width=stamp_size, height=stamp_size, mask='auto')
    
    # フッター
    footer_y = 30*mm
    pdf.setFont(font_name, 8)
    pdf.drawCentredString(width / 2, footer_y, "上記の金額を正に領収いたしました。")
    pdf.drawCentredString(width / 2, footer_y - 7*mm, "※再発行はいたしません")
    
    pdf.save()
    buffer.seek(0)
    
    return buffer


def generate_sales_invoice_pdf(invoice: SalesInvoice, db: Session) -> BytesIO:
    """販売員請求書PDF生成（既存の機能を維持）
    
    Args:
        invoice: 請求書データ
        db: データベースセッション
        
    Returns:
        BytesIO: PDF データ
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    font_name = setup_japanese_font()
    
    # タイトル
    pdf.setFont(font_name, 16)
    pdf.drawCentredString(width / 2, height - 30*mm, "請求書")
    
    # 基本情報
    pdf.setFont(font_name, 10)
    pdf.drawString(30*mm, height - 50*mm, f"請求日: {invoice.invoice_date}")
    pdf.drawString(30*mm, height - 60*mm, f"支払期限: {invoice.payment_due_date}")
    
    # 宛名
    sales_person = db.query(SalesPerson).filter(
        SalesPerson.id == invoice.sales_person_id
    ).first()
    sales_person_name = sales_person.name if sales_person else ""
    pdf.setFont(font_name, 12)
    pdf.drawString(30*mm, height - 80*mm, f"{sales_person_name} 様")
    
    # 合計金額
    pdf.setFont(font_name, 14)
    pdf.drawString(30*mm, height - 110*mm, f"合計金額: ¥{invoice.total_amount_inc_tax:,}")
    
    # フッター
    pdf.setFont(font_name, 9)
    pdf.drawString(30*mm, 30*mm, COMPANY_INFO["name"])
    pdf.drawString(30*mm, 23*mm, f"{COMPANY_INFO['postal_code']} {COMPANY_INFO['address1']}")
    
    pdf.save()
    buffer.seek(0)
    
    return buffer


def generate_contractor_invoice_pdf(invoice: ContractorInvoice, db: Session) -> BytesIO:
    """委託先請求書PDF生成（既存の機能を維持）
    
    Args:
        invoice: 委託先請求書データ
        db: データベースセッション
        
    Returns:
        BytesIO: PDF データ
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    font_name = setup_japanese_font()
    
    # タイトル
    pdf.setFont(font_name, 16)
    pdf.drawCentredString(width / 2, height - 30*mm, "請求書")
    
    # 基本情報
    pdf.setFont(font_name, 10)
    pdf.drawString(30*mm, height - 50*mm, f"請求日: {invoice.invoice_date}")
    pdf.drawString(30*mm, height - 60*mm, f"支払期限: {invoice.payment_due_date}")
    
    # 宛名
    contractor = db.query(Contractor).filter(
        Contractor.id == invoice.contractor_id
    ).first()
    contractor_name = contractor.name if contractor else ""
    pdf.setFont(font_name, 12)
    pdf.drawString(30*mm, height - 80*mm, f"{contractor_name} 様")
    
    # 合計金額
    pdf.setFont(font_name, 14)
    pdf.drawString(30*mm, height - 110*mm, f"合計金額: ¥{invoice.total_amount_inc_tax:,}")
    
    # フッター
    pdf.setFont(font_name, 9)
    pdf.drawString(30*mm, 30*mm, COMPANY_INFO["name"])
    pdf.drawString(30*mm, 23*mm, f"{COMPANY_INFO['postal_code']} {COMPANY_INFO['address1']}")
    
    pdf.save()
    buffer.seek(0)
    
    return buffer
