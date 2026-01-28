"""PDF生成ヘルパー"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from sqlalchemy.orm import Session

from models import SalesInvoice, SalesInvoiceDetail, Product, SalesPerson, DiscountRate


def generate_sales_invoice_pdf(invoice: SalesInvoice, db: Session) -> BytesIO:
    """販売員請求書PDF生成
    
    Args:
        invoice: 請求書データ
        db: データベースセッション
        
    Returns:
        BytesIO: PDF データ
    """
    # 販売員情報取得
    sales_person = db.query(SalesPerson).filter(
        SalesPerson.id == invoice.sales_person_id
    ).first()
    
    # 割引率情報取得
    discount_rate = db.query(DiscountRate).filter(
        DiscountRate.id == invoice.discount_rate_id
    ).first()
    
    # 明細取得
    details = db.query(SalesInvoiceDetail).filter(
        SalesInvoiceDetail.sales_invoice_id == invoice.id
    ).all()
    
    # PDFを生成
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # 日本語フォント設定（Windowsの場合）
    try:
        # MS ゴシックを使用
        font_path = "C:\\Windows\\Fonts\\msgothic.ttc"
        pdfmetrics.registerFont(TTFont('Japanese', font_path))
        pdf.setFont('Japanese', 12)
    except:
        # フォントが見つからない場合はHelveticaを使用
        pdf.setFont('Helvetica', 12)
    
    # タイトル
    pdf.setFont('Japanese', 18)
    pdf.drawString(50*mm, height - 30*mm, "請 求 書")
    
    # 請求書番号
    pdf.setFont('Japanese', 10)
    pdf.drawString(50*mm, height - 40*mm, f"請求書番号: {invoice.invoice_number}")
    
    # 販売員情報
    pdf.drawString(50*mm, height - 50*mm, f"販売員: {sales_person.name if sales_person else ''}")
    pdf.drawString(50*mm, height - 55*mm, f"請求期間: {invoice.start_date} ～ {invoice.end_date}")
    
    # 割引率
    pdf.drawString(50*mm, height - 65*mm, 
                   f"適用割引率: {float(discount_rate.rate) * 100:.0f}% (下限額: ¥{discount_rate.threshold_amount:,})")
    
    # 明細テーブルヘッダー
    y_position = height - 80*mm
    pdf.setFont('Japanese', 9)
    pdf.drawString(15*mm, y_position, "商品名")
    pdf.drawString(65*mm, y_position, "数量")
    pdf.drawString(80*mm, y_position, "単価")
    pdf.drawString(100*mm, y_position, "金額")
    pdf.drawString(120*mm, y_position, "割引率")
    pdf.drawString(140*mm, y_position, "割引額")
    pdf.drawString(160*mm, y_position, "割引後")
    pdf.drawString(160*mm, y_position - 3*mm, "金額")
    pdf.drawString(182*mm, y_position, "ノルマ")
    pdf.drawString(182*mm, y_position - 3*mm, "対象")
    
    # 罫線
    pdf.line(15*mm, y_position - 5*mm, 195*mm, y_position - 5*mm)
    
    # 明細データ
    y_position -= 10*mm
    for detail in details:
        product = db.query(Product).filter(Product.id == detail.product_id).first()
        pdf.drawString(15*mm, y_position, product.name if product else "")
        pdf.drawRightString(75*mm, y_position, f"{detail.total_quantity}")
        pdf.drawRightString(98*mm, y_position, f"¥{detail.unit_price:,}")
        pdf.drawRightString(118*mm, y_position, f"¥{detail.amount:,}")
        # ノルマ対象マーク
        if product and product.quota_target_flag:
            pdf.drawString(185*mm, y_position, "*")
        y_position -= 6*mm
        
        # ページ送り判定（簡易版）
        if y_position < 50*mm:
            pdf.showPage()
            pdf.setFont('Japanese', 9)
            y_position = height - 30*mm
    
    # 合計欄
    y_position -= 10*mm
    pdf.line(15*mm, y_position, 195*mm, y_position)
    
    y_position -= 8*mm
    pdf.setFont('Japanese', 9)
    
    # 商品小計行
    total_subtotal = invoice.quota_subtotal + invoice.non_quota_subtotal
    total_discount = invoice.quota_discount_amount + invoice.non_quota_discount_amount
    total_after_discount = total_subtotal - total_discount
    discount_rate_percent = float(discount_rate.rate) * 100
    
    pdf.drawString(15*mm, y_position, "小計")
    pdf.drawString(65*mm, y_position, "商品小計")
    pdf.drawRightString(118*mm, y_position, f"¥{total_subtotal:,}")
    pdf.drawString(122*mm, y_position, f"{discount_rate_percent:.0f}%")
    pdf.drawRightString(155*mm, y_position, f"¥{total_discount:,}")
    pdf.drawRightString(178*mm, y_position, f"¥{total_after_discount:,}")
    
    # ノルマ対象小計
    y_position -= 6*mm
    pdf.drawString(15*mm, y_position, "ノルマ")
    pdf.drawString(15*mm, y_position - 3*mm, "対象")
    pdf.drawRightString(118*mm, y_position, f"¥{invoice.quota_subtotal:,}")
    pdf.drawString(122*mm, y_position, f"{discount_rate_percent:.0f}%")
    pdf.drawRightString(155*mm, y_position, f"¥{invoice.quota_discount_amount:,}")
    pdf.drawRightString(178*mm, y_position, f"¥{invoice.quota_total:,}")
    
    # ノルマ対象外小計
    y_position -= 8*mm
    pdf.drawString(15*mm, y_position, "ノルマ")
    pdf.drawString(15*mm, y_position - 3*mm, "対象外")
    pdf.drawRightString(118*mm, y_position, f"¥{invoice.non_quota_subtotal:,}")
    pdf.drawString(122*mm, y_position, f"{discount_rate_percent:.0f}%")
    pdf.drawRightString(155*mm, y_position, f"¥{invoice.non_quota_discount_amount:,}")
    pdf.drawRightString(178*mm, y_position, f"¥{invoice.non_quota_total:,}")
    
    # 割引対象外小計（現在は常に0）
    y_position -= 8*mm
    pdf.drawString(15*mm, y_position, "割引対象外")
    pdf.drawRightString(118*mm, y_position, "¥0")
    pdf.drawRightString(178*mm, y_position, "¥0")
    
    # 合計金額（税抜）
    y_position -= 8*mm
    pdf.line(15*mm, y_position, 195*mm, y_position)
    y_position -= 6*mm
    pdf.setFont('Japanese', 10)
    pdf.drawString(15*mm, y_position, "合計金額（税抜）")
    pdf.drawRightString(118*mm, y_position, f"¥{total_subtotal:,}")
    pdf.drawString(122*mm, y_position, f"{discount_rate_percent:.0f}%")
    pdf.drawRightString(155*mm, y_position, f"¥{total_discount:,}")
    pdf.drawRightString(178*mm, y_position, f"¥{total_after_discount:,}")
    
    # 消費税
    y_position -= 8*mm
    pdf.setFont('Japanese', 9)
    pdf.drawString(15*mm, y_position, "消費税率")
    pdf.drawString(50*mm, y_position, "10%")
    
    y_position -= 6*mm
    pdf.drawString(15*mm, y_position, "消費税額")
    pdf.drawRightString(178*mm, y_position, f"¥{invoice.tax_amount:,}")
    
    # 最終合計
    y_position -= 8*mm
    pdf.line(15*mm, y_position, 195*mm, y_position)
    y_position -= 8*mm
    pdf.setFont('Japanese', 12)
    pdf.drawString(15*mm, y_position, "税込合計:")
    pdf.drawRightString(178*mm, y_position, f"¥{invoice.total_amount_inc_tax:,}")
    
    pdf.save()
    buffer.seek(0)
    
    return buffer
