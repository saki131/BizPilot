"""PDF生成ヘルパー - 販売員請求書鏡テンプレート準拠"""
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import black, white
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os

from models import SalesInvoice, SalesInvoiceDetail, Product, SalesPerson, DiscountRate

# 会社情報（固定値）
COMPANY_INFO = {
    "name": "株式会社ドクターフェリス",
    "representative": "前鼻 和美",
    "postal_code": "〒004-0063",
    "address1": "北海道札幌市厚別区",
    "address2": "厚別西3条3丁目4-1",
}

# 振込先情報
BANK_INFO = {
    "bank_name": "ゆうちょ銀行",
    "branch_name": "908（キュウゼロハチ）",
    "account_type": "普通",
    "account_number": "420025",
    "account_holder": "マエハナ カズミ",
    "yucho_symbol": "19060",  # ゆうちょ記号
    "yucho_number": "42000251",  # ゆうちょ番号
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
                print("WARNING: Japanese font not found, using Helvetica (Japanese characters will not display)")
                import glob
                ttf_fonts = glob.glob("/usr/share/fonts/**/*.ttf", recursive=True)
                print(f"Available TTF fonts: {ttf_fonts[:10]}")
        except Exception as e:
            print(f"Font loading error: {e}")
    return font_name


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
    
    # 請求日・支払期日の計算
    billing_date = invoice.end_date if invoice.end_date else datetime.now().date()
    # 支払期日：請求日の翌月末
    if billing_date.month == 12:
        payment_due = billing_date.replace(year=billing_date.year + 1, month=1, day=28)
    else:
        next_month = billing_date.month + 1
        if next_month in [1, 3, 5, 7, 8, 10, 12]:
            payment_due = billing_date.replace(month=next_month, day=31)
        elif next_month in [4, 6, 9, 11]:
            payment_due = billing_date.replace(month=next_month, day=30)
        else:  # 2月
            payment_due = billing_date.replace(month=next_month, day=28)
    
    # ===== ヘッダー部分 =====
    # 請求書タイトル（中央上部、大きく）
    pdf.setFont(font_name, 24)
    title = "請 求 書"
    title_width = pdf.stringWidth(title, font_name, 24)
    pdf.drawString((width - title_width) / 2, height - 25*mm, title)
    
    # 請求書番号（右上）
    pdf.setFont(font_name, 10)
    pdf.drawRightString(width - 15*mm, height - 15*mm, f"No. {invoice.invoice_number}")
    
    # ===== 左側：宛名部分 =====
    y_left = height - 45*mm
    pdf.setFont(font_name, 14)
    sales_person_name = sales_person.name if sales_person else ""
    pdf.drawString(20*mm, y_left, f"{sales_person_name}　様")
    
    # 下線
    pdf.setLineWidth(1)
    pdf.line(20*mm, y_left - 2*mm, 80*mm, y_left - 2*mm)
    pdf.setLineWidth(0.5)
    
    # 請求日・支払期日
    pdf.setFont(font_name, 10)
    pdf.drawString(20*mm, y_left - 12*mm, f"請求日: {billing_date.strftime('%Y年%m月%d日')}")
    pdf.drawString(20*mm, y_left - 20*mm, f"支払期日: {payment_due.strftime('%Y年%m月%d日')}")
    
    # ===== 右側：会社情報 =====
    y_right = height - 45*mm
    right_x = width - 80*mm
    pdf.setFont(font_name, 11)
    pdf.drawString(right_x, y_right, COMPANY_INFO["name"])
    pdf.setFont(font_name, 9)
    pdf.drawString(right_x, y_right - 6*mm, COMPANY_INFO['representative'])
    pdf.drawString(right_x, y_right - 12*mm, COMPANY_INFO["postal_code"])
    pdf.drawString(right_x, y_right - 18*mm, COMPANY_INFO["address1"])
    pdf.drawString(right_x, y_right - 24*mm, COMPANY_INFO["address2"])
    
    # ハンコ枠（丸）
    stamp_x = width - 25*mm
    stamp_y = y_right - 15*mm
    stamp_radius = 8*mm
    pdf.circle(stamp_x, stamp_y, stamp_radius, stroke=1, fill=0)
    pdf.setFont(font_name, 7)
    pdf.drawCentredString(stamp_x, stamp_y + 2*mm, "ドクター")
    pdf.drawCentredString(stamp_x, stamp_y - 3*mm, "フェリス")
    
    # ===== 請求金額ボックス =====
    box_y = height - 95*mm
    box_height = 18*mm
    box_width = 130*mm
    box_x = (width - box_width) / 2
    
    # 外枠
    pdf.setLineWidth(2)
    pdf.rect(box_x, box_y, box_width, box_height, stroke=1, fill=0)
    pdf.setLineWidth(0.5)
    
    # 「ご請求金額」ラベル
    pdf.setFont(font_name, 12)
    pdf.drawString(box_x + 5*mm, box_y + 11*mm, "ご請求金額")
    
    # 金額
    pdf.setFont(font_name, 22)
    total_amount = f"¥{invoice.total_amount_inc_tax:,}-"
    pdf.drawRightString(box_x + box_width - 10*mm, box_y + 5*mm, total_amount)
    
    # 税込表示
    pdf.setFont(font_name, 9)
    pdf.drawRightString(box_x + box_width - 10*mm, box_y + 14*mm, "（税込）")
    
    # ===== 明細テーブル =====
    table_top = box_y - 10*mm
    table_left = 10*mm
    table_right = width - 10*mm
    table_width = table_right - table_left
    
    # 列幅定義（商品名、数量、単価、金額、割引率、割引額、割引後金額）
    col_widths = [50*mm, 12*mm, 20*mm, 24*mm, 14*mm, 22*mm, 26*mm, 12*mm]  # 最後はノルマ
    col_positions = [table_left]
    for w in col_widths[:-1]:
        col_positions.append(col_positions[-1] + w)
    
    # ヘッダー背景
    header_height = 8*mm
    pdf.setFillGray(0.85)
    pdf.rect(table_left, table_top - header_height, table_width, header_height, stroke=1, fill=1)
    pdf.setFillGray(0)
    
    # ヘッダーテキスト
    pdf.setFont(font_name, 7)
    header_y = table_top - 6*mm
    headers = ["商品名", "数量", "単価", "金額", "割引率", "割引額", "割引後", "ノルマ"]
    for i, header in enumerate(headers):
        if i == 0:
            pdf.drawString(col_positions[i] + 1*mm, header_y, header)
        else:
            pdf.drawCentredString(col_positions[i] + col_widths[i] / 2, header_y, header)
    
    # 縦線（ヘッダー）
    for pos in col_positions[1:]:
        pdf.line(pos, table_top - header_height, pos, table_top)
    
    # 割引率の取得
    # rateが1以上ならパーセント値（例：20=20%）、1未満なら小数値（例：0.20=20%）として扱う
    raw_rate = float(discount_rate.rate) if discount_rate else 0
    print(f"[DEBUG PDF] raw_rate from DB: {raw_rate}, type: {type(discount_rate.rate) if discount_rate else None}")
    if raw_rate >= 1:
        # パーセント値として保存されている場合（例：20 = 20%）
        discount_rate_percent = raw_rate
        discount_rate_decimal = raw_rate / 100
        print(f"[DEBUG PDF] Using as percent value: percent={discount_rate_percent}, decimal={discount_rate_decimal}")
    else:
        # 小数値として保存されている場合（例：0.20 = 20%）
        discount_rate_percent = raw_rate * 100
        discount_rate_decimal = raw_rate
        print(f"[DEBUG PDF] Using as decimal value: percent={discount_rate_percent}, decimal={discount_rate_decimal}")
    
    # 明細データ
    row_height = 6*mm
    y = table_top - header_height
    
    for detail in details:
        y -= row_height
        product = db.query(Product).filter(Product.id == detail.product_id).first()
        
        # 行の描画
        pdf.rect(table_left, y, table_width, row_height, stroke=1, fill=0)
        
        # 縦線
        for pos in col_positions[1:]:
            pdf.line(pos, y, pos, y + row_height)
        
        # データ
        row_text_y = y + 1.5*mm
        pdf.setFont(font_name, 7)
        
        # 商品名
        product_name = product.name if product else ""
        pdf.drawString(col_positions[0] + 1*mm, row_text_y, product_name)
        
        # 数量
        pdf.drawRightString(col_positions[1] + col_widths[1] - 1*mm, row_text_y, f"{detail.total_quantity}")
        
        # 単価
        pdf.drawRightString(col_positions[2] + col_widths[2] - 1*mm, row_text_y, f"¥{detail.unit_price:,}")
        
        # 金額（税抜）
        amount = detail.amount
        pdf.drawRightString(col_positions[3] + col_widths[3] - 1*mm, row_text_y, f"¥{amount:,}")
        
        # 割引計算（割引対象外フラグをチェック）
        is_discount_excluded = product.discount_exclusion_flag if product else False
        if is_discount_excluded:
            # 割引対象外
            item_discount_rate = 0
            item_discount_amount = 0
            item_after_discount = amount
            pdf.drawCentredString(col_positions[4] + col_widths[4] / 2, row_text_y, "-")
            pdf.drawCentredString(col_positions[5] + col_widths[5] / 2, row_text_y, "-")
        else:
            # 割引適用
            item_discount_rate = discount_rate_percent
            item_discount_amount = int(amount * discount_rate_decimal)
            item_after_discount = amount - item_discount_amount
            pdf.drawCentredString(col_positions[4] + col_widths[4] / 2, row_text_y, f"{item_discount_rate:.0f}%")
            pdf.drawRightString(col_positions[5] + col_widths[5] - 1*mm, row_text_y, f"¥{item_discount_amount:,}")
        
        # 割引後金額
        pdf.drawRightString(col_positions[6] + col_widths[6] - 1*mm, row_text_y, f"¥{item_after_discount:,}")
        
        # ノルマ対象
        if product and product.quota_target_flag:
            pdf.drawCentredString(col_positions[7] + col_widths[7] / 2, row_text_y, "○")
        
        # ページ送り判定
        if y < 100*mm:
            pdf.showPage()
            pdf.setFont(font_name, 7)
            y = height - 30*mm
    
    # ===== 集計部分（詳細版） =====
    summary_top = y - 8*mm
    summary_left = table_left
    summary_width = table_width
    summary_row_height = 6*mm
    
    # 集計テーブルのヘッダー
    pdf.setFillGray(0.85)
    pdf.rect(summary_left, summary_top - summary_row_height, summary_width, summary_row_height, stroke=1, fill=1)
    pdf.setFillGray(0)
    
    # 集計ヘッダー列幅
    sum_col_widths = [50*mm, 35*mm, 18*mm, 35*mm, 42*mm]  # 項目、金額、割引率、割引額、割引後金額
    sum_col_positions = [summary_left]
    for w in sum_col_widths[:-1]:
        sum_col_positions.append(sum_col_positions[-1] + w)
    
    pdf.setFont(font_name, 8)
    sum_header_y = summary_top - summary_row_height + 1.5*mm
    sum_headers = ["項目", "小計金額", "割引率", "割引額", "割引後金額"]
    for i, header in enumerate(sum_headers):
        if i == 0:
            pdf.drawString(sum_col_positions[i] + 2*mm, sum_header_y, header)
        else:
            pdf.drawCentredString(sum_col_positions[i] + sum_col_widths[i] / 2, sum_header_y, header)
    
    # 縦線（集計ヘッダー）
    for pos in sum_col_positions[1:]:
        pdf.line(pos, summary_top - summary_row_height, pos, summary_top)
    
    # 集計行データ（ノルマ対象、ノルマ対象外、割引対象外、商品小計、合計金額）
    # ノルマ対象: quota_subtotal, quota_discount_amount, quota_total
    # ノルマ対象外: non_quota_subtotal, non_quota_discount_amount, non_quota_total
    # 割引対象外: non_discountable_amount
    
    product_subtotal = invoice.quota_subtotal + invoice.non_quota_subtotal + invoice.non_discountable_amount
    total_discount_amount = invoice.quota_discount_amount + invoice.non_quota_discount_amount
    total_after_discount = invoice.quota_total + invoice.non_quota_total + invoice.non_discountable_amount
    
    summary_data = [
        ("ノルマ対象小計", invoice.quota_subtotal, f"{discount_rate_percent:.0f}%", invoice.quota_discount_amount, invoice.quota_total),
        ("ノルマ対象外小計", invoice.non_quota_subtotal, f"{discount_rate_percent:.0f}%", invoice.non_quota_discount_amount, invoice.non_quota_total),
        ("割引対象外小計", invoice.non_discountable_amount, "-", 0, invoice.non_discountable_amount),
        ("商品小計", product_subtotal, "-", total_discount_amount, total_after_discount),
    ]
    
    pdf.setFont(font_name, 8)
    sum_y = summary_top - summary_row_height
    
    for i, (label, subtotal, rate_str, disc_amt, after_disc) in enumerate(summary_data):
        sum_y -= summary_row_height
        
        # 背景（商品小計は強調）
        if i == 3:  # 商品小計
            pdf.setFillGray(0.92)
            pdf.rect(summary_left, sum_y, summary_width, summary_row_height, stroke=1, fill=1)
            pdf.setFillGray(0)
        else:
            pdf.rect(summary_left, sum_y, summary_width, summary_row_height, stroke=1, fill=0)
        
        # 縦線
        for pos in sum_col_positions[1:]:
            pdf.line(pos, sum_y, pos, sum_y + summary_row_height)
        
        row_text_y = sum_y + 1.5*mm
        
        # ラベル
        pdf.drawString(sum_col_positions[0] + 2*mm, row_text_y, label)
        
        # 小計金額
        pdf.drawRightString(sum_col_positions[1] + sum_col_widths[1] - 2*mm, row_text_y, f"¥{subtotal:,}")
        
        # 割引率
        pdf.drawCentredString(sum_col_positions[2] + sum_col_widths[2] / 2, row_text_y, rate_str)
        
        # 割引額
        if disc_amt > 0:
            pdf.drawRightString(sum_col_positions[3] + sum_col_widths[3] - 2*mm, row_text_y, f"¥{disc_amt:,}")
        else:
            pdf.drawCentredString(sum_col_positions[3] + sum_col_widths[3] / 2, row_text_y, "-")
        
        # 割引後金額
        pdf.drawRightString(sum_col_positions[4] + sum_col_widths[4] - 2*mm, row_text_y, f"¥{after_disc:,}")
    
    # 税抜合計行
    sum_y -= summary_row_height
    pdf.setFillGray(0.88)
    pdf.rect(summary_left, sum_y, summary_width, summary_row_height, stroke=1, fill=1)
    pdf.setFillGray(0)
    for pos in sum_col_positions[1:]:
        pdf.line(pos, sum_y, pos, sum_y + summary_row_height)
    
    pdf.setFont(font_name, 9)
    row_text_y = sum_y + 1.5*mm
    pdf.drawString(sum_col_positions[0] + 2*mm, row_text_y, "合計金額（税抜）")
    pdf.drawRightString(sum_col_positions[1] + sum_col_widths[1] - 2*mm, row_text_y, f"¥{product_subtotal:,}")
    pdf.drawCentredString(sum_col_positions[2] + sum_col_widths[2] / 2, row_text_y, "-")
    pdf.drawRightString(sum_col_positions[3] + sum_col_widths[3] - 2*mm, row_text_y, f"¥{total_discount_amount:,}")
    pdf.drawRightString(sum_col_positions[4] + sum_col_widths[4] - 2*mm, row_text_y, f"¥{invoice.total_amount_ex_tax:,}")
    
    # 消費税行
    sum_y -= summary_row_height
    pdf.rect(summary_left, sum_y, summary_width, summary_row_height, stroke=1, fill=0)
    for pos in sum_col_positions[1:]:
        pdf.line(pos, sum_y, pos, sum_y + summary_row_height)
    
    pdf.setFont(font_name, 8)
    row_text_y = sum_y + 1.5*mm
    pdf.drawString(sum_col_positions[0] + 2*mm, row_text_y, "消費税 (10%)")
    pdf.drawRightString(sum_col_positions[4] + sum_col_widths[4] - 2*mm, row_text_y, f"¥{invoice.tax_amount:,}")
    
    # 税込合計行（大きく強調）
    sum_y -= summary_row_height + 2*mm
    pdf.setLineWidth(2)
    pdf.setFillGray(0.85)
    pdf.rect(summary_left, sum_y, summary_width, summary_row_height + 2*mm, stroke=1, fill=1)
    pdf.setFillGray(0)
    pdf.setLineWidth(0.5)
    
    for pos in sum_col_positions[1:]:
        pdf.line(pos, sum_y, pos, sum_y + summary_row_height + 2*mm)
    
    pdf.setFont(font_name, 11)
    row_text_y = sum_y + 2.5*mm
    pdf.drawString(sum_col_positions[0] + 2*mm, row_text_y, "税込合計")
    pdf.setFont(font_name, 14)
    pdf.drawRightString(sum_col_positions[4] + sum_col_widths[4] - 2*mm, row_text_y, f"¥{invoice.total_amount_inc_tax:,}")
    
    # ===== 振込先情報 =====
    bank_y = sum_y - 15*mm
    pdf.setFont(font_name, 10)
    pdf.drawString(20*mm, bank_y, "【お振込先】")
    pdf.setFont(font_name, 9)
    pdf.drawString(20*mm, bank_y - 7*mm, f"{BANK_INFO['bank_name']}　{BANK_INFO['branch_name']}")
    pdf.drawString(20*mm, bank_y - 14*mm, f"{BANK_INFO['account_type']}　{BANK_INFO['account_number']}")
    pdf.drawString(20*mm, bank_y - 21*mm, f"口座名義: {BANK_INFO['account_holder']}")
    pdf.drawString(20*mm, bank_y - 28*mm, f"記号: {BANK_INFO['yucho_symbol']}　番号: {BANK_INFO['yucho_number']}")
    
    # ===== 備考欄 =====
    remarks_y = bank_y - 42*mm
    pdf.setFont(font_name, 10)
    pdf.drawString(20*mm, remarks_y, "【備考】")
    pdf.setFont(font_name, 9)
    
    # 但し書きの内容を出力
    remark_offset = 7*mm
    if invoice.note:
        pdf.drawString(20*mm, remarks_y - remark_offset, f"・{invoice.note}")
        remark_offset += 7*mm
  
    # ===== フッター =====
    footer_y = 20*mm
    pdf.setFont(font_name, 9)
    pdf.drawCentredString(width / 2, footer_y, "上記の通りご請求申し上げます。")
    
    pdf.save()
    buffer.seek(0)
    
    return buffer
