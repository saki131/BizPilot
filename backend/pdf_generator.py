"""PDF生成ヘルパー - 販売員請求書鏡テンプレート準拠"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black, white
from sqlalchemy.orm import Session
from datetime import datetime

from models import SalesInvoice, SalesInvoiceDetail, Product, SalesPerson, DiscountRate


def setup_japanese_font():
    """日本語フォントの設定"""
    font_name = 'Helvetica'
    try:
        # Windows環境: MS ゴシック
        font_path = "C:\\Windows\\Fonts\\msgothic.ttc"
        pdfmetrics.registerFont(TTFont('Japanese', font_path))
        font_name = 'Japanese'
    except:
        try:
            import os
            # Linux環境用フォント
            font_candidates = [
                "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
            ]
            for fp in font_candidates:
                if os.path.exists(fp):
                    pdfmetrics.registerFont(TTFont('Japanese', fp))
                    font_name = 'Japanese'
                    break
        except:
            pass
    return font_name


def draw_box(pdf, x, y, w, h, fill=False):
    """四角枠を描画"""
    if fill:
        pdf.setFillColor(black)
        pdf.rect(x, y, w, h, stroke=1, fill=1)
        pdf.setFillColor(white)
    else:
        pdf.rect(x, y, w, h, stroke=1, fill=0)


def generate_sales_invoice_pdf(invoice: SalesInvoice, db: Session) -> BytesIO:
    """販売員請求書PDF生成（販売員請求書鏡テンプレート準拠）
    
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
    
    discount_rate = db.query(DiscountRate).filter(
        DiscountRate.id == invoice.discount_rate_id
    ).first()
    
    details = db.query(SalesInvoiceDetail).filter(
        SalesInvoiceDetail.sales_invoice_id == invoice.id
    ).all()
    
    # PDF生成
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # フォント設定
    font_name = setup_japanese_font()
    pdf.setFont(font_name, 10)
    pdf.setLineWidth(0.5)
    
    # ===== ヘッダー部分 =====
    # 請求書タイトル（中央上部、大きく）
    pdf.setFont(font_name, 24)
    title = "請 求 書"
    title_width = pdf.stringWidth(title, font_name, 24)
    pdf.drawString((width - title_width) / 2, height - 25*mm, title)
    
    # 請求書番号（右上）
    pdf.setFont(font_name, 10)
    pdf.drawRightString(width - 15*mm, height - 15*mm, f"No. {invoice.invoice_number}")
    
    # 発行日（右上）
    issue_date = datetime.now().strftime("%Y年%m月%d日")
    pdf.drawRightString(width - 15*mm, height - 22*mm, f"発行日: {issue_date}")
    
    # ===== 宛名部分（左側） =====
    y_addr = height - 45*mm
    pdf.setFont(font_name, 14)
    sales_person_name = sales_person.name if sales_person else ""
    pdf.drawString(20*mm, y_addr, f"{sales_person_name}　様")
    
    # 下線
    pdf.setLineWidth(1)
    pdf.line(20*mm, y_addr - 2*mm, 80*mm, y_addr - 2*mm)
    pdf.setLineWidth(0.5)
    
    # ===== 請求金額ボックス（中央大きく） =====
    box_y = height - 75*mm
    box_height = 18*mm
    box_width = 120*mm
    box_x = (width - box_width) / 2
    
    # 外枠
    pdf.setLineWidth(2)
    pdf.rect(box_x, box_y, box_width, box_height, stroke=1, fill=0)
    pdf.setLineWidth(0.5)
    
    # 「ご請求金額」ラベル
    pdf.setFont(font_name, 12)
    pdf.drawString(box_x + 5*mm, box_y + 11*mm, "ご請求金額")
    
    # 金額
    pdf.setFont(font_name, 20)
    total_amount = f"¥{invoice.total_amount_inc_tax:,}-"
    pdf.drawRightString(box_x + box_width - 10*mm, box_y + 5*mm, total_amount)
    
    # 税込表示
    pdf.setFont(font_name, 9)
    pdf.drawRightString(box_x + box_width - 10*mm, box_y + 13*mm, "（税込）")
    
    # ===== 請求期間 =====
    pdf.setFont(font_name, 10)
    period_y = box_y - 10*mm
    start_date = invoice.start_date.strftime("%Y年%m月%d日") if invoice.start_date else ""
    end_date = invoice.end_date.strftime("%Y年%m月%d日") if invoice.end_date else ""
    pdf.drawCentredString(width / 2, period_y, f"請求期間: {start_date} ～ {end_date}")
    
    # ===== 明細テーブル =====
    table_top = period_y - 15*mm
    table_left = 15*mm
    table_right = width - 15*mm
    table_width = table_right - table_left
    
    # 列幅定義
    col_widths = [60*mm, 20*mm, 25*mm, 30*mm, 30*mm]  # 商品名、数量、単価、金額、備考
    col_positions = [table_left]
    for w in col_widths[:-1]:
        col_positions.append(col_positions[-1] + w)
    
    # ヘッダー背景
    header_height = 8*mm
    pdf.setFillGray(0.85)
    pdf.rect(table_left, table_top - header_height, table_width, header_height, stroke=1, fill=1)
    pdf.setFillGray(0)
    
    # ヘッダーテキスト
    pdf.setFont(font_name, 9)
    header_y = table_top - 6*mm
    headers = ["商品名", "数量", "単価", "金額", "ノルマ"]
    for i, header in enumerate(headers):
        if i == 0:
            pdf.drawString(col_positions[i] + 2*mm, header_y, header)
        else:
            # 右寄せ
            pdf.drawCentredString(col_positions[i] + col_widths[i] / 2, header_y, header)
    
    # 明細データ
    row_height = 6*mm
    y = table_top - header_height
    
    for detail in details:
        y -= row_height
        product = db.query(Product).filter(Product.id == detail.product_id).first()
        
        # 行の描画
        pdf.rect(table_left, y, table_width, row_height, stroke=1, fill=0)
        
        # 縦線
        for i, pos in enumerate(col_positions[1:], 1):
            pdf.line(pos, y, pos, y + row_height)
        
        # データ
        row_text_y = y + 1.5*mm
        pdf.setFont(font_name, 8)
        
        # 商品名
        product_name = product.name if product else ""
        pdf.drawString(col_positions[0] + 2*mm, row_text_y, product_name)
        
        # 数量
        pdf.drawRightString(col_positions[1] + col_widths[1] - 2*mm, row_text_y, f"{detail.total_quantity}")
        
        # 単価
        pdf.drawRightString(col_positions[2] + col_widths[2] - 2*mm, row_text_y, f"¥{detail.unit_price:,}")
        
        # 金額
        pdf.drawRightString(col_positions[3] + col_widths[3] - 2*mm, row_text_y, f"¥{detail.amount:,}")
        
        # ノルマ対象
        if product and product.quota_target_flag:
            pdf.drawCentredString(col_positions[4] + col_widths[4] / 2, row_text_y, "○")
        
        # ページ送り判定
        if y < 60*mm:
            pdf.showPage()
            pdf.setFont(font_name, 8)
            y = height - 30*mm
    
    # ===== 集計部分 =====
    summary_top = y - 5*mm
    summary_left = table_left + 80*mm
    summary_width = table_width - 80*mm
    summary_row_height = 7*mm
    
    discount_rate_percent = float(discount_rate.rate) * 100 if discount_rate else 0
    
    # 集計行データ
    summary_rows = [
        ("ノルマ対象小計", f"¥{invoice.quota_subtotal:,}"),
        ("ノルマ対象外小計", f"¥{invoice.non_quota_subtotal:,}"),
        ("商品小計", f"¥{invoice.quota_subtotal + invoice.non_quota_subtotal:,}"),
        (f"割引額 ({discount_rate_percent:.0f}%)", f"- ¥{invoice.quota_discount_amount + invoice.non_quota_discount_amount:,}"),
        ("税抜合計", f"¥{invoice.quota_total + invoice.non_quota_total:,}"),
        ("消費税 (10%)", f"¥{invoice.tax_amount:,}"),
    ]
    
    pdf.setFont(font_name, 9)
    for i, (label, value) in enumerate(summary_rows):
        row_y = summary_top - (i + 1) * summary_row_height
        
        # 背景（合計行のみ薄いグレー）
        if i == 4:  # 税抜合計
            pdf.setFillGray(0.95)
            pdf.rect(summary_left, row_y, summary_width, summary_row_height, stroke=1, fill=1)
            pdf.setFillGray(0)
        else:
            pdf.rect(summary_left, row_y, summary_width, summary_row_height, stroke=1, fill=0)
        
        # 縦線（ラベルと金額の区切り）
        pdf.line(summary_left + 40*mm, row_y, summary_left + 40*mm, row_y + summary_row_height)
        
        # ラベル
        pdf.drawString(summary_left + 2*mm, row_y + 2*mm, label)
        
        # 金額
        pdf.drawRightString(summary_left + summary_width - 3*mm, row_y + 2*mm, value)
    
    # 税込合計（大きく強調）
    total_row_y = summary_top - (len(summary_rows) + 1) * summary_row_height
    pdf.setLineWidth(2)
    pdf.setFillGray(0.9)
    pdf.rect(summary_left, total_row_y, summary_width, summary_row_height + 2*mm, stroke=1, fill=1)
    pdf.setFillGray(0)
    pdf.setLineWidth(0.5)
    
    pdf.line(summary_left + 40*mm, total_row_y, summary_left + 40*mm, total_row_y + summary_row_height + 2*mm)
    
    pdf.setFont(font_name, 11)
    pdf.drawString(summary_left + 2*mm, total_row_y + 3*mm, "税込合計")
    pdf.setFont(font_name, 14)
    pdf.drawRightString(summary_left + summary_width - 3*mm, total_row_y + 2*mm, f"¥{invoice.total_amount_inc_tax:,}")
    
    # ===== フッター =====
    footer_y = 25*mm
    pdf.setFont(font_name, 8)
    pdf.drawCentredString(width / 2, footer_y, "上記の通りご請求申し上げます。")
    
    # 割引率情報
    if discount_rate:
        pdf.drawString(20*mm, footer_y - 8*mm, 
                       f"適用割引率: {discount_rate_percent:.0f}%（下限額: ¥{discount_rate.threshold_amount:,}以上）")
    
    pdf.save()
    buffer.seek(0)
    
    return buffer
