"""PDF逕滓・繝倥Ν繝代・ - 雋ｩ螢ｲ蜩｡隲区ｱよ嶌髀｡繝・Φ繝励Ξ繝ｼ繝域ｺ匁侠"""
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

# 莨夂､ｾ諠・ｱ・亥崋螳壼､・・
COMPANY_INFO = {
    "name": "[COMPANY_NAME]",
    "representative": "蜑埼ｼｻ 蜥檎ｾ・,
    "postal_code": "縲・04-0063",
    "address1": "[COMPANY_ADDRESS1]",
    "address2": "[COMPANY_ADDRESS2]",
}

# 謖ｯ霎ｼ蜈域ュ蝣ｱ
BANK_INFO = {
    "bank_name": "繧・≧縺｡繧・橿陦・,
    "branch_name": "908・医く繝･繧ｦ繧ｼ繝ｭ繝上メ・・,
    "account_type": "譎ｮ騾・,
    "account_number": "420025",
    "account_holder": "繝槭お繝上リ 繧ｫ繧ｺ繝・,
    "yucho_symbol": "[BANK_YUCHO_SYMBOL]",
    "yucho_number": "[BANK_ACCOUNT_NUMBER]1",
}

def setup_japanese_font():
    """譌･譛ｬ隱槭ヵ繧ｩ繝ｳ繝医・險ｭ螳夲ｼ医Γ繝｢繝ｪ譛驕ｩ蛹也沿・・""
    font_name = 'Helvetica'
    
    # 繝輔か繝ｳ繝医′譌｢縺ｫ逋ｻ骭ｲ縺輔ｌ縺ｦ縺・ｋ蝣ｴ蜷医・繧ｹ繧ｭ繝・・
    if 'Japanese' in pdfmetrics.getRegisteredFontNames():
        return 'Japanese'
    
    try:
        # Linux迺ｰ蠅・ｼ・ocker繧ｳ繝ｳ繝・リ・峨・繝輔か繝ｳ繝医ヱ繧ｹ繧貞━蜈・
        # 螳滄圀縺ｫ蟄伜惠縺吶ｋ繝輔ぃ繧､繝ｫ縺ｮ縺ｿ隧ｦ陦・
        linux_font_path = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
        if os.path.exists(linux_font_path):
            pdfmetrics.registerFont(TTFont('Japanese', linux_font_path))
            return 'Japanese'
        
        # Windows迺ｰ蠅・・繝輔か繝ｼ繝ｫ・ｽ・ｽ繝・け
        windows_font_path = "C:\\Windows\\Fonts\\msgothic.ttc"
        if os.path.exists(windows_font_path):
            pdfmetrics.registerFont(TTFont('Japanese', windows_font_path))
            return 'Japanese'
        
        # 縺昴・莉悶・Linux迺ｰ蠅・ヵ繧ｩ繝ｳ繝・
        other_paths = [
            "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
            "/usr/share/fonts/truetype/ipafont/ipag.ttf",
        ]
        for fp in other_paths:
            if os.path.exists(fp):
                pdfmetrics.registerFont(TTFont('Japanese', fp))
                return 'Japanese'
        
        print("WARNING: Japanese font not found, using Helvetica")
    except Exception as e:
        print(f"Font loading error: {e}, using Helvetica")
    
    return font_name


def generate_sales_receipt_pdf(invoice: SalesInvoice, db: Session) -> BytesIO:
    """雋ｩ螢ｲ蜩｡逕ｨ鬆伜庶譖ｸPDF逕滓・
    
    Args:
        invoice: 隲区ｱよ嶌繝・・繧ｿ
        db: 繝・・繧ｿ繝吶・繧ｹ繧ｻ繝・す繝ｧ繝ｳ
        
    Returns:
        BytesIO: PDF 繝・・繧ｿ
    """
    # 繝・・繧ｿ蜿門ｾ・
    sales_person = db.query(SalesPerson).filter(
        SalesPerson.sales_person_id == invoice.sales_person_id
    ).first()
    
    # PDF逕滓・・域ｨｪ蜷代″・・
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # 繝輔か繝ｳ繝郁ｨｭ螳・
    font_name = setup_japanese_font()
    
    # 繧ｿ繧､繝医Ν
    pdf.setFont(font_name, 24)
    title = "鬆・蜿・譖ｸ"
    title_width = pdf.stringWidth(title, font_name, 24)
    pdf.drawString((width - title_width) / 2, height - 40*mm, title)
    
    # 螳帛錐
    pdf.setFont(font_name, 14)
    sales_person_name = sales_person.name if sales_person else ""
    pdf.drawString(30*mm, height - 70*mm, f"{sales_person_name}縲讒・)
    
    # 驥鷹｡阪・繝・け繧ｹ
    box_y = height - 100*mm
    box_height = 20*mm
    box_width = 140*mm
    box_x = (width - box_width) / 2
    
    pdf.setLineWidth(2)
    pdf.rect(box_x, box_y, box_width, box_height, stroke=1, fill=0)
    pdf.setLineWidth(0.5)
    
    pdf.setFont(font_name, 22)
    total_amount = f"ﾂ･{invoice.total_amount_inc_tax:,}-"
    pdf.drawRightString(box_x + box_width - 10*mm, box_y + 6*mm, total_amount)
    
    # 菴・＠譖ｸ縺・
    pdf.setFont(font_name, 11)
    note_text = invoice.note
    pdf.drawString(30*mm, box_y - 15*mm, f"菴・＋note_text}")
    
    # 鬆伜庶譌･
    receipt_date = invoice.receipt_date if invoice.receipt_date else invoice.invoice_date
    if isinstance(receipt_date, str):
        receipt_date = datetime.strptime(receipt_date, "%Y-%m-%d").date()
    pdf.drawString(30*mm, box_y - 30*mm, f"鬆伜庶譌･: {receipt_date.strftime('%Y蟷ｴ%m譛・d譌･')}")
    
    # 逋ｺ陦瑚・ュ蝣ｱ
    issuer_y = box_y - 45*mm
    pdf.setFont(font_name, 11)
    pdf.drawString(30*mm, issuer_y, COMPANY_INFO["name"])
    pdf.setFont(font_name, 9)
    pdf.drawString(30*mm, issuer_y - 7*mm, "譁ｰ譛ｭ蟷御ｻ｣逅・ｺ・)
    pdf.drawString(30*mm, issuer_y - 14*mm, f"莉｣陦ｨ閠・ {COMPANY_INFO['representative']}")
    pdf.drawString(30*mm, issuer_y - 21*mm, "逋ｻ骭ｲ逡ｪ蜿ｷ: [COMPANY_REGISTRATION_NUMBER]")
    pdf.drawString(30*mm, issuer_y - 28*mm, COMPANY_INFO["postal_code"])
    pdf.drawString(30*mm, issuer_y - 35*mm, COMPANY_INFO["address1"])
    pdf.drawString(30*mm, issuer_y - 42*mm, COMPANY_INFO["address2"])
    
    # 繝上Φ繧ｳ逕ｻ蜒上ｒ霑ｽ蜉・井ｼ夂､ｾ蜷阪・荳驛ｨ縺ｫ驥阪・繧具ｼ・
    stamp_path = os.path.join(os.path.dirname(__file__), "static", "stamp.png")
    if os.path.exists(stamp_path):
        # 莨夂､ｾ蜷阪・讓ｪ縺ｫ繝上Φ繧ｳ繧帝・鄂ｮ・域枚蟄励↓蟆代＠縺九°繧九ｈ縺・↓・・
        stamp_size = 16*mm
        stamp_x = 72*mm  # 莨夂､ｾ蜷阪・蜿ｳ蛛ｴ
        stamp_y = issuer_y - 10*mm  # 莨夂､ｾ蜷阪↓蟆代＠縺九°繧矩ｫ倥＆
        pdf.drawImage(stamp_path, stamp_x, stamp_y, width=stamp_size, height=stamp_size)
    
    # 繝輔ャ繧ｿ繝ｼ
    footer_y = 30*mm
    pdf.setFont(font_name, 8)
    pdf.drawCentredString(width / 2, footer_y, "荳願ｨ倥・驥鷹｡阪ｒ豁｣縺ｫ鬆伜庶縺・◆縺励∪縺励◆縲・)
    
    pdf.save()
    buffer.seek(0)
    
    return buffer


def generate_contractor_receipt_pdf(invoice: ContractorInvoice, db: Session) -> BytesIO:
    """蟋碑ｨ怜・逕ｨ鬆伜庶譖ｸPDF逕滓・
    
    Args:
        invoice: 蟋碑ｨ怜・隲区ｱよ嶌繝・・繧ｿ
        db: 繝・・繧ｿ繝吶・繧ｹ繧ｻ繝・す繝ｧ繝ｳ
        
    Returns:
        BytesIO: PDF 繝・・繧ｿ
    """
    # 繝・・繧ｿ蜿門ｾ・
    contractor = db.query(Contractor).filter(
        Contractor.contractor_id == invoice.contractor_id
    ).first()
    
    # PDF逕滓・・域ｨｪ蜷代″・・
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # 繝輔か繝ｳ繝郁ｨｭ螳・
    font_name = setup_japanese_font()
    
    # 繧ｿ繧､繝医Ν
    pdf.setFont(font_name, 24)
    title = "鬆・蜿・譖ｸ"
    title_width = pdf.stringWidth(title, font_name, 24)
    pdf.drawString((width - title_width) / 2, height - 40*mm, title)
    
    # 螳帛錐
    pdf.setFont(font_name, 14)
    contractor_name = contractor.name if contractor else ""
    pdf.drawString(30*mm, height - 70*mm, f"{contractor_name}縲讒・)
    
    # 驥鷹｡阪・繝・け繧ｹ
    box_y = height - 100*mm
    box_height = 20*mm
    box_width = 140*mm
    box_x = (width - box_width) / 2
    
    pdf.setLineWidth(2)
    pdf.rect(box_x, box_y, box_width, box_height, stroke=1, fill=0)
    pdf.setLineWidth(0.5)
    
    pdf.setFont(font_name, 22)
    total_amount = f"ﾂ･{invoice.total_amount_inc_tax:,}-"
    pdf.drawRightString(box_x + box_width - 10*mm, box_y + 6*mm, total_amount)
    
    # 菴・＠譖ｸ縺・
    pdf.setFont(font_name, 11)
    note_text = invoice.note if invoice.note else "蠕｡蜩∽ｻ｣縺ｨ縺励※"
    pdf.drawString(30*mm, box_y - 15*mm, f"菴・＠縲＋note_text}")
    
    # 鬆伜庶譌･
    receipt_date = invoice.receipt_date if invoice.receipt_date else invoice.invoice_date
    if isinstance(receipt_date, str):
        receipt_date = datetime.strptime(receipt_date, "%Y-%m-%d").date()
    pdf.drawString(30*mm, box_y - 30*mm, f"鬆伜庶譌･: {receipt_date.strftime('%Y蟷ｴ%m譛・d譌･')}")
    
    # 逋ｺ陦瑚・ュ蝣ｱ
    issuer_y = box_y - 45*mm
    pdf.setFont(font_name, 11)
    pdf.drawString(30*mm, issuer_y, COMPANY_INFO["name"])
    pdf.setFont(font_name, 9)
    pdf.drawString(30*mm, issuer_y - 7*mm, "譁ｰ譛ｭ蟷御ｻ｣逅・ｺ・)
    pdf.drawString(30*mm, issuer_y - 14*mm, f"莉｣陦ｨ閠・ {COMPANY_INFO['representative']}")
    pdf.drawString(30*mm, issuer_y - 21*mm, "逋ｻ骭ｲ逡ｪ蜿ｷ: [COMPANY_REGISTRATION_NUMBER]")
    pdf.drawString(30*mm, issuer_y - 28*mm, COMPANY_INFO["postal_code"])
    pdf.drawString(30*mm, issuer_y - 35*mm, COMPANY_INFO["address1"])
    pdf.drawString(30*mm, issuer_y - 42*mm, COMPANY_INFO["address2"])
    
    # 繝上Φ繧ｳ逕ｻ蜒上ｒ霑ｽ蜉・井ｼ夂､ｾ蜷阪・荳驛ｨ縺ｫ驥阪・繧具ｼ・
    stamp_path = os.path.join(os.path.dirname(__file__), "static", "stamp.png")
    if os.path.exists(stamp_path):
        # 莨夂､ｾ蜷阪・讓ｪ縺ｫ繝上Φ繧ｳ繧帝・鄂ｮ・域枚蟄励↓蟆代＠縺九°繧九ｈ縺・↓・・
        stamp_size = 16*mm
        stamp_x = 72*mm  # 莨夂､ｾ蜷阪・蜿ｳ蛛ｴ
        stamp_y = issuer_y - 10*mm  # 莨夂､ｾ蜷阪↓蟆代＠縺九°繧矩ｫ倥＆
        pdf.drawImage(stamp_path, stamp_x, stamp_y, width=stamp_size, height=stamp_size)
    
    # 繝輔ャ繧ｿ繝ｼ
    footer_y = 30*mm
    pdf.setFont(font_name, 8)
    pdf.drawCentredString(width / 2, footer_y, "荳願ｨ倥・驥鷹｡阪ｒ豁｣縺ｫ鬆伜庶縺・◆縺励∪縺励◆縲・)
    
    pdf.save()
    buffer.seek(0)
    
    return buffer


def generate_sales_invoice_pdf(invoice: SalesInvoice, db: Session) -> BytesIO:
    """雋ｩ螢ｲ蜩｡隲区ｱよ嶌PDF逕滓・・郁ｲｩ螢ｲ蜩｡隲区ｱよ嶌髀｡繝・Φ繝励Ξ繝ｼ繝域ｺ匁侠・・
    
    Args:
        invoice: 隲区ｱよ嶌繝・・繧ｿ
        db: 繝・・繧ｿ繝吶・繧ｹ繧ｻ繝・す繝ｧ繝ｳ
        
    Returns:
        BytesIO: PDF 繝・・繧ｿ
    """
    # 繝・・繧ｿ蜿門ｾ・
    sales_person = db.query(SalesPerson).filter(
        SalesPerson.sales_person_id == invoice.sales_person_id
    ).first()
    
    discount_rate = db.query(DiscountRate).filter(
        DiscountRate.discount_rate_id == invoice.discount_rate_id
    ).first()
    
    details = db.query(SalesInvoiceDetail).filter(
        SalesInvoiceDetail.sales_invoice_id == invoice.sales_invoice_id
    ).all()
    
    # PDF逕滓・
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # 繝輔か繝ｳ繝郁ｨｭ螳・
    font_name = setup_japanese_font()
    pdf.setFont(font_name, 10)
    pdf.setLineWidth(0.5)
    
    # 隲区ｱよ律繝ｻ謾ｯ謇墓悄譌･縺ｮ險育ｮ・
    billing_date = invoice.invoice_date if invoice.invoice_date else datetime.now().date()
    # 謾ｯ謇墓悄譌･・夂ｷ繧∵律縺ｮ譛医・25譌･
    payment_due = billing_date.replace(day=25)
    
    # ===== 繝倥ャ繝繝ｼ驛ｨ蛻・=====
    # 隲区ｱよ嶌繧ｿ繧､繝医Ν・井ｸｭ螟ｮ荳企Κ縲∝､ｧ縺阪￥・・
    pdf.setFont(font_name, 24)
    title = "隲・豎・譖ｸ"
    title_width = pdf.stringWidth(title, font_name, 24)
    pdf.drawString((width - title_width) / 2, height - 25*mm, title)
    
    # # 隲区ｱよ嶌逡ｪ蜿ｷ・亥承荳奇ｼ・
    # pdf.setFont(font_name, 10)
    # pdf.drawRightString(width - 15*mm, height - 15*mm, f"No. {invoice.invoice_number}")
    
    # ===== 蟾ｦ蛛ｴ・壼ｮ帛錐驛ｨ蛻・=====
    y_left = height - 45*mm
    pdf.setFont(font_name, 14)
    sales_person_name = sales_person.name if sales_person else ""
    pdf.drawString(20*mm, y_left, f"{sales_person_name}縲讒・)
    
    # 荳狗ｷ・
    pdf.setLineWidth(1)
    pdf.line(20*mm, y_left - 2*mm, 80*mm, y_left - 2*mm)
    pdf.setLineWidth(0.5)
    
    # 隲区ｱよ律繝ｻ謾ｯ謇墓悄譌･
    pdf.setFont(font_name, 10)
    pdf.drawString(20*mm, y_left - 12*mm, f"隲区ｱよ律: {billing_date.strftime('%Y蟷ｴ%m譛・d譌･')}")
    pdf.drawString(20*mm, y_left - 20*mm, f"謾ｯ謇墓悄譌･: {payment_due.strftime('%Y蟷ｴ%m譛・d譌･')}")
    
    # ===== 蜿ｳ蛛ｴ・壻ｼ夂､ｾ諠・ｱ =====
    y_right = height - 45*mm
    right_x = width - 80*mm
    pdf.setFont(font_name, 11)
    pdf.drawString(right_x, y_right, COMPANY_INFO["name"])
    pdf.setFont(font_name, 9)
    pdf.drawString(right_x, y_right - 6*mm, "譁ｰ譛ｭ蟷御ｻ｣逅・ｺ・)
    pdf.drawString(right_x, y_right - 12*mm, COMPANY_INFO['representative'])
    pdf.drawString(right_x, y_right - 18*mm, "逋ｻ骭ｲ逡ｪ蜿ｷ: [COMPANY_REGISTRATION_NUMBER]")
    pdf.drawString(right_x, y_right - 24*mm, COMPANY_INFO["postal_code"])
    pdf.drawString(right_x, y_right - 30*mm, COMPANY_INFO["address1"])
    pdf.drawString(right_x, y_right - 36*mm, COMPANY_INFO["address2"])
    
    # 繝上Φ繧ｳ逕ｻ蜒・
    stamp_x = right_x + 50*mm
    stamp_y = y_right - 1*mm
    stamp_width = 16*mm
    stamp_height = 16*mm
    
    # 逕ｻ蜒上ヵ繧｡繧､繝ｫ縺ｮ繝代せ
    stamp_image_path = os.path.join(os.path.dirname(__file__), "static", "stamp.png")
    
    try:
        # 逕ｻ蜒上ｒ謠冗判
        pdf.drawImage(stamp_image_path, 
                     stamp_x - stamp_width/2, 
                     stamp_y - stamp_height/2, 
                     width=stamp_width, 
                     height=stamp_height,
                     preserveAspectRatio=True,
                     )
    except Exception as e:
        # 逕ｻ蜒上′隕九▽縺九ｉ縺ｪ縺・ｴ蜷医・蠕捺擂縺ｮ蜀・→繝・く繧ｹ繝医〒謠冗判
        print(f"Warning: Stamp image not found at {stamp_image_path}, using text fallback: {e}")
        stamp_radius = 8*mm
        pdf.circle(stamp_x, stamp_y, stamp_radius, stroke=1, fill=0)
        pdf.setFont(font_name, 7)
        pdf.drawCentredString(stamp_x, stamp_y + 2*mm, "繝峨け繧ｿ繝ｼ")
        pdf.drawCentredString(stamp_x, stamp_y - 3*mm, "繝輔ぉ繝ｪ繧ｹ")
    
    # ===== 隲区ｱる≡鬘阪・繝・け繧ｹ =====
    box_y = height - 105*mm
    box_height = 18*mm
    box_width = 130*mm
    box_x = (width - box_width) / 2
    
    # 螟匁棧
    pdf.setLineWidth(2)
    pdf.rect(box_x, box_y, box_width, box_height, stroke=1, fill=0)
    pdf.setLineWidth(0.5)
    
    # 縲後＃隲区ｱる≡鬘阪阪Λ繝吶Ν
    pdf.setFont(font_name, 12)
    pdf.drawString(box_x + 5*mm, box_y + 11*mm, "縺碑ｫ区ｱる≡鬘・)
    
    # 驥鷹｡・
    pdf.setFont(font_name, 22)
    total_amount = f"ﾂ･{invoice.total_amount_inc_tax:,}-"
    pdf.drawRightString(box_x + box_width - 10*mm, box_y + 5*mm, total_amount)
    
    # 遞手ｾｼ陦ｨ遉ｺ
    pdf.setFont(font_name, 9)
    pdf.drawRightString(box_x + box_width - 10*mm, box_y + 14*mm, "・育ｨ手ｾｼ・・)
    
    # ===== 譏守ｴｰ繝・・繝悶Ν =====
    table_top = box_y - 10*mm
    table_left = 10*mm
    table_right = width - 10*mm
    table_width = table_right - table_left
    
    # 蛻怜ｹ・ｮ夂ｾｩ・亥膚蜩∝錐縲∵焚驥上∝腰萓｡縲・≡鬘阪∝牡蠑慕紫縲∝牡蠑暮｡阪∝牡蠑募ｾ碁≡鬘搾ｼ・
    col_widths = [50*mm, 12*mm, 20*mm, 24*mm, 14*mm, 22*mm, 26*mm, 12*mm]  # 譛蠕後・繝弱Ν繝・
    col_positions = [table_left]
    for w in col_widths[:-1]:
        col_positions.append(col_positions[-1] + w)
    
    # 繝倥ャ繝繝ｼ閭梧勹
    header_height = 8*mm
    pdf.setFillGray(0.85)
    pdf.rect(table_left, table_top - header_height, table_width, header_height, stroke=1, fill=1)
    pdf.setFillGray(0)
    
    # 繝倥ャ繝繝ｼ繝・く繧ｹ繝・
    pdf.setFont(font_name, 7)
    header_y = table_top - 6*mm
    headers = ["蝠・刀蜷・, "謨ｰ驥・, "蜊倅ｾ｡", "驥鷹｡・, "蜑ｲ蠑慕紫", "蜑ｲ蠑暮｡・, "蜑ｲ蠑募ｾ・, "繝弱Ν繝・]
    for i, header in enumerate(headers):
        if i == 0:
            pdf.drawString(col_positions[i] + 1*mm, header_y, header)
        else:
            pdf.drawCentredString(col_positions[i] + col_widths[i] / 2, header_y, header)
    
    # 邵ｦ邱夲ｼ医・繝・ム繝ｼ・・
    for pos in col_positions[1:]:
        pdf.line(pos, table_top - header_height, pos, table_top)
    
    # 蜑ｲ蠑慕紫縺ｮ蜿門ｾ・
    # rate縺・莉･荳翫↑繧峨ヱ繝ｼ繧ｻ繝ｳ繝亥､・井ｾ具ｼ・0=20%・峨・譛ｪ貅縺ｪ繧牙ｰ乗焚蛟､・井ｾ具ｼ・.20=20%・峨→縺励※謇ｱ縺・
    raw_rate = float(discount_rate.rate) if discount_rate else 0
    print(f"[DEBUG PDF] raw_rate from DB: {raw_rate}, type: {type(discount_rate.rate) if discount_rate else None}")
    if raw_rate >= 1:
        # 繝代・繧ｻ繝ｳ繝亥､縺ｨ縺励※菫晏ｭ倥＆繧後※縺・ｋ蝣ｴ蜷茨ｼ井ｾ具ｼ・0 = 20%・・
        discount_rate_percent = raw_rate
        discount_rate_decimal = raw_rate / 100
        print(f"[DEBUG PDF] Using as percent value: percent={discount_rate_percent}, decimal={discount_rate_decimal}")
    else:
        # 蟆乗焚蛟､縺ｨ縺励※菫晏ｭ倥＆繧後※縺・ｋ蝣ｴ蜷茨ｼ井ｾ具ｼ・.20 = 20%・・
        discount_rate_percent = raw_rate * 100
        discount_rate_decimal = raw_rate
        print(f"[DEBUG PDF] Using as decimal value: percent={discount_rate_percent}, decimal={discount_rate_decimal}")
    
    # 譏守ｴｰ繝・・繧ｿ
    row_height = 6*mm
    y = table_top - header_height
    
    for detail in details:
        y -= row_height
        product = db.query(Product).filter(Product.product_id == detail.product_id).first()
        
        # 陦後・謠冗判
        pdf.rect(table_left, y, table_width, row_height, stroke=1, fill=0)
        
        # 邵ｦ邱・
        for pos in col_positions[1:]:
            pdf.line(pos, y, pos, y + row_height)
        
        # 繝・・繧ｿ
        row_text_y = y + 1.5*mm
        pdf.setFont(font_name, 7)
        
        # 蝠・刀蜷・
        product_name = product.name if product else ""
        pdf.drawString(col_positions[0] + 1*mm, row_text_y, product_name)
        
        # 謨ｰ驥・
        pdf.drawRightString(col_positions[1] + col_widths[1] - 1*mm, row_text_y, f"{detail.total_quantity}")
        
        # 蜊倅ｾ｡
        pdf.drawRightString(col_positions[2] + col_widths[2] - 1*mm, row_text_y, f"ﾂ･{detail.unit_price:,}")
        
        # 驥鷹｡搾ｼ育ｨ取栢・・
        amount = detail.amount
        pdf.drawRightString(col_positions[3] + col_widths[3] - 1*mm, row_text_y, f"ﾂ･{amount:,}")
        
        # 蜑ｲ蠑戊ｨ育ｮ暦ｼ亥牡蠑募ｯｾ雎｡螟悶ヵ繝ｩ繧ｰ繧偵メ繧ｧ繝・け・・
        is_discount_excluded = product.discount_exclusion_flag if product else False
        if is_discount_excluded:
            # 蜑ｲ蠑募ｯｾ雎｡螟・
            item_discount_rate = 0
            item_discount_amount = 0
            item_after_discount = amount
            pdf.drawCentredString(col_positions[4] + col_widths[4] / 2, row_text_y, "-")
            pdf.drawCentredString(col_positions[5] + col_widths[5] / 2, row_text_y, "-")
        else:
            # 蜑ｲ蠑暮←逕ｨ
            item_discount_rate = discount_rate_percent
            item_discount_amount = int(amount * discount_rate_decimal)
            item_after_discount = amount - item_discount_amount
            pdf.drawCentredString(col_positions[4] + col_widths[4] / 2, row_text_y, f"{item_discount_rate:.0f}%")
            pdf.drawRightString(col_positions[5] + col_widths[5] - 1*mm, row_text_y, f"ﾂ･{item_discount_amount:,}")
        
        # 蜑ｲ蠑募ｾ碁≡鬘・
        pdf.drawRightString(col_positions[6] + col_widths[6] - 1*mm, row_text_y, f"ﾂ･{item_after_discount:,}")
        
        # 繝弱Ν繝槫ｯｾ雎｡
        if product and product.quota_target_flag:
            pdf.drawCentredString(col_positions[7] + col_widths[7] / 2, row_text_y, "笳・)
        
        # 繝壹・繧ｸ騾√ｊ蛻､螳・
        if y < 100*mm:
            pdf.showPage()
            pdf.setFont(font_name, 7)
            y = height - 30*mm
    
    # ===== 髮・ｨ磯Κ蛻・ｼ郁ｩｳ邏ｰ迚茨ｼ・=====
    summary_top = y - 8*mm
    summary_left = table_left
    summary_width = table_width
    summary_row_height = 6*mm
    
    # 髮・ｨ医ユ繝ｼ繝悶Ν縺ｮ繝倥ャ繝繝ｼ
    pdf.setFillGray(0.85)
    pdf.rect(summary_left, summary_top - summary_row_height, summary_width, summary_row_height, stroke=1, fill=1)
    pdf.setFillGray(0)
    
    # 髮・ｨ医・繝・ム繝ｼ蛻怜ｹ・
    sum_col_widths = [50*mm, 35*mm, 18*mm, 35*mm, 42*mm]  # 鬆・岼縲・≡鬘阪∝牡蠑慕紫縲∝牡蠑暮｡阪∝牡蠑募ｾ碁≡鬘・
    sum_col_positions = [summary_left]
    for w in sum_col_widths[:-1]:
        sum_col_positions.append(sum_col_positions[-1] + w)
    
    pdf.setFont(font_name, 8)
    sum_header_y = summary_top - summary_row_height + 1.5*mm
    sum_headers = ["鬆・岼", "蟆剰ｨ磯≡鬘・, "蜑ｲ蠑慕紫", "蜑ｲ蠑暮｡・, "蜑ｲ蠑募ｾ碁≡鬘・]
    for i, header in enumerate(sum_headers):
        if i == 0:
            pdf.drawString(sum_col_positions[i] + 2*mm, sum_header_y, header)
        else:
            pdf.drawCentredString(sum_col_positions[i] + sum_col_widths[i] / 2, sum_header_y, header)
    
    # 邵ｦ邱夲ｼ磯寔險医・繝・ム繝ｼ・・
    for pos in sum_col_positions[1:]:
        pdf.line(pos, summary_top - summary_row_height, pos, summary_top)
    
    # 髮・ｨ郁｡後ョ繝ｼ繧ｿ・医ヮ繝ｫ繝槫ｯｾ雎｡縲√ヮ繝ｫ繝槫ｯｾ雎｡螟悶∝牡蠑募ｯｾ雎｡螟悶∝膚蜩∝ｰ剰ｨ医∝粋險磯≡鬘搾ｼ・
    # 繝弱Ν繝槫ｯｾ雎｡: quota_subtotal, quota_discount_amount, quota_total
    # 繝弱Ν繝槫ｯｾ雎｡螟・ non_quota_subtotal, non_quota_discount_amount, non_quota_total
    # 蜑ｲ蠑募ｯｾ雎｡螟・ non_discountable_amount
    
    product_subtotal = invoice.quota_subtotal + invoice.non_quota_subtotal + invoice.non_discountable_amount
    total_discount_amount = invoice.quota_discount_amount + invoice.non_quota_discount_amount
    total_after_discount = invoice.quota_total + invoice.non_quota_total + invoice.non_discountable_amount
    
    summary_data = [
        ("繝弱Ν繝槫ｯｾ雎｡蟆剰ｨ・, invoice.quota_subtotal, f"{discount_rate_percent:.0f}%", invoice.quota_discount_amount, invoice.quota_total),
        ("繝弱Ν繝槫ｯｾ雎｡螟門ｰ剰ｨ・, invoice.non_quota_subtotal, f"{discount_rate_percent:.0f}%", invoice.non_quota_discount_amount, invoice.non_quota_total),
        ("蜑ｲ蠑募ｯｾ雎｡螟門ｰ剰ｨ・, invoice.non_discountable_amount, "-", 0, invoice.non_discountable_amount),
        ("蝠・刀蟆剰ｨ・, product_subtotal, "-", total_discount_amount, total_after_discount),
    ]
    
    pdf.setFont(font_name, 8)
    sum_y = summary_top - summary_row_height
    
    for i, (label, subtotal, rate_str, disc_amt, after_disc) in enumerate(summary_data):
        sum_y -= summary_row_height
        
        # 閭梧勹・亥膚蜩∝ｰ剰ｨ医・蠑ｷ隱ｿ・・
        if i == 3:  # 蝠・刀蟆剰ｨ・
            pdf.setFillGray(0.92)
            pdf.rect(summary_left, sum_y, summary_width, summary_row_height, stroke=1, fill=1)
            pdf.setFillGray(0)
        else:
            pdf.rect(summary_left, sum_y, summary_width, summary_row_height, stroke=1, fill=0)
        
        # 邵ｦ邱・
        for pos in sum_col_positions[1:]:
            pdf.line(pos, sum_y, pos, sum_y + summary_row_height)
        
        row_text_y = sum_y + 1.5*mm
        
        # 繝ｩ繝吶Ν
        pdf.drawString(sum_col_positions[0] + 2*mm, row_text_y, label)
        
        # 蟆剰ｨ磯≡鬘・
        pdf.drawRightString(sum_col_positions[1] + sum_col_widths[1] - 2*mm, row_text_y, f"ﾂ･{subtotal:,}")
        
        # 蜑ｲ蠑慕紫
        pdf.drawCentredString(sum_col_positions[2] + sum_col_widths[2] / 2, row_text_y, rate_str)
        
        # 蜑ｲ蠑暮｡・
        if disc_amt > 0:
            pdf.drawRightString(sum_col_positions[3] + sum_col_widths[3] - 2*mm, row_text_y, f"ﾂ･{disc_amt:,}")
        else:
            pdf.drawCentredString(sum_col_positions[3] + sum_col_widths[3] / 2, row_text_y, "-")
        
        # 蜑ｲ蠑募ｾ碁≡鬘・
        pdf.drawRightString(sum_col_positions[4] + sum_col_widths[4] - 2*mm, row_text_y, f"ﾂ･{after_disc:,}")
    
    # 遞取栢蜷郁ｨ郁｡・
    sum_y -= summary_row_height
    pdf.setFillGray(0.88)
    pdf.rect(summary_left, sum_y, summary_width, summary_row_height, stroke=1, fill=1)
    pdf.setFillGray(0)
    for pos in sum_col_positions[1:]:
        pdf.line(pos, sum_y, pos, sum_y + summary_row_height)
    
    pdf.setFont(font_name, 9)
    row_text_y = sum_y + 1.5*mm
    pdf.drawString(sum_col_positions[0] + 2*mm, row_text_y, "蜷郁ｨ磯≡鬘搾ｼ育ｨ取栢・・)
    pdf.drawRightString(sum_col_positions[1] + sum_col_widths[1] - 2*mm, row_text_y, f"ﾂ･{product_subtotal:,}")
    pdf.drawCentredString(sum_col_positions[2] + sum_col_widths[2] / 2, row_text_y, "-")
    pdf.drawRightString(sum_col_positions[3] + sum_col_widths[3] - 2*mm, row_text_y, f"ﾂ･{total_discount_amount:,}")
    pdf.drawRightString(sum_col_positions[4] + sum_col_widths[4] - 2*mm, row_text_y, f"ﾂ･{invoice.total_amount_ex_tax:,}")
    
    # 豸郁ｲｻ遞手｡・
    sum_y -= summary_row_height
    pdf.rect(summary_left, sum_y, summary_width, summary_row_height, stroke=1, fill=0)
    for pos in sum_col_positions[1:]:
        pdf.line(pos, sum_y, pos, sum_y + summary_row_height)
    
    pdf.setFont(font_name, 8)
    row_text_y = sum_y + 1.5*mm
    pdf.drawString(sum_col_positions[0] + 2*mm, row_text_y, "豸郁ｲｻ遞・(10%)")
    pdf.drawRightString(sum_col_positions[4] + sum_col_widths[4] - 2*mm, row_text_y, f"ﾂ･{invoice.tax_amount:,}")
    
    # 遞手ｾｼ蜷郁ｨ郁｡鯉ｼ亥､ｧ縺阪￥蠑ｷ隱ｿ・・
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
    pdf.drawString(sum_col_positions[0] + 2*mm, row_text_y, "遞手ｾｼ蜷郁ｨ・)
    pdf.setFont(font_name, 14)
    pdf.drawRightString(sum_col_positions[4] + sum_col_widths[4] - 2*mm, row_text_y, f"ﾂ･{invoice.total_amount_inc_tax:,}")
    
    # ===== 謖ｯ霎ｼ蜈域ュ蝣ｱ =====
    bank_y = sum_y - 15*mm
    pdf.setFont(font_name, 10)
    pdf.drawString(20*mm, bank_y, "縲舌♀謖ｯ霎ｼ蜈医・)
    pdf.setFont(font_name, 9)
    pdf.drawString(20*mm, bank_y - 7*mm, f"{BANK_INFO['bank_name']}縲{BANK_INFO['branch_name']}")
    pdf.drawString(20*mm, bank_y - 14*mm, f"{BANK_INFO['account_type']}縲{BANK_INFO['account_number']}")
    pdf.drawString(20*mm, bank_y - 21*mm, f"蜿｣蠎ｧ蜷咲ｾｩ: {BANK_INFO['account_holder']}")
    pdf.drawString(20*mm, bank_y - 28*mm, f"險伜捷: {BANK_INFO['yucho_symbol']}縲逡ｪ蜿ｷ: {BANK_INFO['yucho_number']}")
    
    # ===== 蛯呵・ｬ・=====
    remarks_y = bank_y - 42*mm
    pdf.setFont(font_name, 10)
    pdf.drawString(20*mm, remarks_y, "縲仙ｙ閠・・)
    pdf.setFont(font_name, 9)
    
    # 菴・＠譖ｸ縺阪・蜀・ｮｹ繧貞・蜉・
    remark_offset = 7*mm
    if invoice.note:
        pdf.drawString(20*mm, remarks_y - remark_offset, f"繝ｻ{invoice.note}")
        remark_offset += 7*mm
  
    # ===== 繝輔ャ繧ｿ繝ｼ =====
    footer_y = 20*mm
    pdf.setFont(font_name, 9)
    pdf.drawCentredString(width / 2, footer_y, "荳願ｨ倥・騾壹ｊ縺碑ｫ区ｱら筏縺嶺ｸ翫￡縺ｾ縺吶・)
    
    pdf.save()
    buffer.seek(0)
    
    return buffer


def generate_contractor_invoice_pdf(invoice: ContractorInvoice, db: Session) -> BytesIO:
    """蟋碑ｨ怜・隲区ｱよ嶌PDF逕滓・・郁ｲｩ螢ｲ蜩｡隲区ｱよ嶌繝輔か繝ｼ繝槭ャ繝域ｺ匁侠・・
    
    Args:
        invoice: 蟋碑ｨ怜・隲区ｱよ嶌繝・・繧ｿ
        db: 繝・・繧ｿ繝吶・繧ｹ繧ｻ繝・す繝ｧ繝ｳ
        
    Returns:
        BytesIO: PDF 繝・・繧ｿ
    """
    # 繝・・繧ｿ蜿門ｾ・
    contractor = db.query(Contractor).filter(
        Contractor.contractor_id == invoice.contractor_id
    ).first()
    
    discount_rate = db.query(DiscountRate).filter(
        DiscountRate.discount_rate_id == invoice.discount_rate_id
    ).first()
    
    details = db.query(ContractorInvoiceDetail).filter(
        ContractorInvoiceDetail.contractor_invoice_id == invoice.contractor_invoice_id
    ).all()
    
    # PDF逕滓・
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # 繝輔か繝ｳ繝郁ｨｭ螳・
    font_name = setup_japanese_font()
    pdf.setFont(font_name, 10)
    pdf.setLineWidth(0.5)
    
    # 隲区ｱよ律繝ｻ謾ｯ謇墓悄譌･縺ｮ險育ｮ・
    # 隲区ｱよ律・・0譌･邱繧・ｼ・nvoice_date繧・0譌･縺ｫ險ｭ螳夲ｼ・
    billing_date = invoice.invoice_date if invoice.invoice_date else datetime.now().date()
    if isinstance(billing_date, str):
        billing_date = datetime.strptime(billing_date, "%Y-%m-%d").date()
    # 邱繧∵律繧・0譌･縺ｫ蝗ｺ螳・
    billing_date = billing_date.replace(day=20)
    # 謾ｯ謇墓悄譌･・夂ｷ繧∵律縺ｮ譛医・25譌･
    payment_due = billing_date.replace(day=25)
    
    # ===== 繝倥ャ繝繝ｼ驛ｨ蛻・=====
    # 隲区ｱよ嶌繧ｿ繧､繝医Ν・井ｸｭ螟ｮ荳企Κ縲∝､ｧ縺阪￥・・
    pdf.setFont(font_name, 24)
    title = "隲・豎・譖ｸ"
    title_width = pdf.stringWidth(title, font_name, 24)
    pdf.drawString((width - title_width) / 2, height - 25*mm, title)
    
    # # 隲区ｱよ嶌逡ｪ蜿ｷ・亥承荳奇ｼ・
    # pdf.setFont(font_name, 10)
    # invoice_number = f"C-{invoice.id:04d}"  # 蟋碑ｨ怜・隲区ｱよ嶌逡ｪ蜿ｷ
    # pdf.drawRightString(width - 15*mm, height - 15*mm, f"No. {invoice_number}")
    
    # ===== 蟾ｦ蛛ｴ・壼ｮ帛錐驛ｨ蛻・=====
    y_left = height - 45*mm
    pdf.setFont(font_name, 14)
    contractor_name = contractor.name if contractor else ""
    pdf.drawString(20*mm, y_left, f"{contractor_name}縲讒・)
    
    # 荳狗ｷ・
    pdf.setLineWidth(1)
    pdf.line(20*mm, y_left - 2*mm, 80*mm, y_left - 2*mm)
    pdf.setLineWidth(0.5)
    
    # 隲区ｱよ律繝ｻ謾ｯ謇墓悄譌･
    pdf.setFont(font_name, 10)
    pdf.drawString(20*mm, y_left - 12*mm, f"隲区ｱよ律: {billing_date.strftime('%Y蟷ｴ%m譛・d譌･')}")
    pdf.drawString(20*mm, y_left - 20*mm, f"謾ｯ謇墓悄譌･: {payment_due.strftime('%Y蟷ｴ%m譛・d譌･')}")
    
    # ===== 蜿ｳ蛛ｴ・壻ｼ夂､ｾ諠・ｱ =====
    y_right = height - 45*mm
    right_x = width - 80*mm
    pdf.setFont(font_name, 11)
    pdf.drawString(right_x, y_right, COMPANY_INFO["name"])
    pdf.setFont(font_name, 9)
    pdf.drawString(right_x, y_right - 6*mm, "譁ｰ譛ｭ蟷御ｻ｣逅・ｺ・)
    pdf.drawString(right_x, y_right - 12*mm, COMPANY_INFO['representative'])
    pdf.drawString(right_x, y_right - 18*mm, "逋ｻ骭ｲ逡ｪ蜿ｷ: [COMPANY_REGISTRATION_NUMBER]")
    pdf.drawString(right_x, y_right - 24*mm, COMPANY_INFO["postal_code"])
    pdf.drawString(right_x, y_right - 30*mm, COMPANY_INFO["address1"])
    pdf.drawString(right_x, y_right - 36*mm, COMPANY_INFO["address2"])
    
    # 繝上Φ繧ｳ逕ｻ蜒・
    stamp_x = right_x + 50*mm
    stamp_y = y_right - 1*mm
    stamp_width = 16*mm
    stamp_height = 16*mm
    
    # 逕ｻ蜒上ヵ繧｡繧､繝ｫ縺ｮ繝代せ
    stamp_image_path = os.path.join(os.path.dirname(__file__), "static", "stamp.png")
    
    try:
        # 逕ｻ蜒上ｒ謠冗判
        pdf.drawImage(stamp_image_path, 
                     stamp_x - stamp_width/2, 
                     stamp_y - stamp_height/2, 
                     width=stamp_width, 
                     height=stamp_height,
                     preserveAspectRatio=True,
                     )
    except Exception as e:
        # 逕ｻ蜒上′隕九▽縺九ｉ縺ｪ縺・ｴ蜷医・蠕捺擂縺ｮ蜀・→繝・く繧ｹ繝医〒謠冗判
        print(f"Warning: Stamp image not found at {stamp_image_path}, using text fallback: {e}")
        stamp_radius = 8*mm
        pdf.circle(stamp_x, stamp_y, stamp_radius, stroke=1, fill=0)
        pdf.setFont(font_name, 7)
        pdf.drawCentredString(stamp_x, stamp_y + 2*mm, "繝峨け繧ｿ繝ｼ")
        pdf.drawCentredString(stamp_x, stamp_y - 3*mm, "繝輔ぉ繝ｪ繧ｹ")
    
    # ===== 隲区ｱる≡鬘阪・繝・け繧ｹ =====
    box_y = height - 105*mm
    box_height = 18*mm
    box_width = 130*mm
    box_x = (width - box_width) / 2
    
    # 螟匁棧
    pdf.setLineWidth(2)
    pdf.rect(box_x, box_y, box_width, box_height, stroke=1, fill=0)
    pdf.setLineWidth(0.5)
    
    # 縲後＃隲区ｱる≡鬘阪阪Λ繝吶Ν
    pdf.setFont(font_name, 12)
    pdf.drawString(box_x + 5*mm, box_y + 11*mm, "縺碑ｫ区ｱる≡鬘・)
    
    # 驥鷹｡・
    pdf.setFont(font_name, 22)
    total_amount = f"ﾂ･{invoice.total_amount_inc_tax:,}-"
    pdf.drawRightString(box_x + box_width - 10*mm, box_y + 5*mm, total_amount)
    
    # 遞手ｾｼ陦ｨ遉ｺ
    pdf.setFont(font_name, 9)
    pdf.drawRightString(box_x + box_width - 10*mm, box_y + 14*mm, "・育ｨ手ｾｼ・・)
    
    # ===== 譏守ｴｰ繝・・繝悶Ν =====
    table_top = box_y - 10*mm
    table_left = 10*mm
    table_right = width - 10*mm
    table_width = table_right - table_left
    
    # 蛻怜ｹ・ｮ夂ｾｩ・亥膚蜩∝錐縲∵焚驥上∝腰萓｡縲・≡鬘阪∝牡蠑慕紫縲∝牡蠑暮｡阪∝牡蠑募ｾ碁≡鬘搾ｼ・
    col_widths = [50*mm, 12*mm, 20*mm, 24*mm, 14*mm, 22*mm, 26*mm, 12*mm]  # 譛蠕後・繝弱Ν繝・
    col_positions = [table_left]
    for w in col_widths[:-1]:
        col_positions.append(col_positions[-1] + w)
    
    # 繝倥ャ繝繝ｼ閭梧勹
    header_height = 8*mm
    pdf.setFillGray(0.85)
    pdf.rect(table_left, table_top - header_height, table_width, header_height, stroke=1, fill=1)
    pdf.setFillGray(0)
    
    # 繝倥ャ繝繝ｼ繝・く繧ｹ繝・
    pdf.setFont(font_name, 7)
    header_y = table_top - 6*mm
    headers = ["蝠・刀蜷・, "謨ｰ驥・, "蜊倅ｾ｡", "驥鷹｡・, "蜑ｲ蠑慕紫", "蜑ｲ蠑暮｡・, "蜑ｲ蠑募ｾ・, "繝弱Ν繝・]
    for i, header in enumerate(headers):
        if i == 0:
            pdf.drawString(col_positions[i] + 1*mm, header_y, header)
        else:
            pdf.drawCentredString(col_positions[i] + col_widths[i] / 2, header_y, header)
    
    # 邵ｦ邱夲ｼ医・繝・ム繝ｼ・・
    for pos in col_positions[1:]:
        pdf.line(pos, table_top - header_height, pos, table_top)
    
    # 蜑ｲ蠑慕紫縺ｮ蜿門ｾ・
    # rate縺・莉･荳翫↑繧峨ヱ繝ｼ繧ｻ繝ｳ繝亥､・井ｾ具ｼ・0=20%・峨・譛ｪ貅縺ｪ繧牙ｰ乗焚蛟､・井ｾ具ｼ・.20=20%・峨→縺励※謇ｱ縺・
    raw_rate = float(discount_rate.rate) if discount_rate else 0
    print(f"[DEBUG PDF] raw_rate from DB: {raw_rate}, type: {type(discount_rate.rate) if discount_rate else None}")
    if raw_rate >= 1:
        # 繝代・繧ｻ繝ｳ繝亥､縺ｨ縺励※菫晏ｭ倥＆繧後※縺・ｋ蝣ｴ蜷茨ｼ井ｾ具ｼ・0 = 20%・・
        discount_rate_percent = raw_rate
        discount_rate_decimal = raw_rate / 100
        print(f"[DEBUG PDF] Using as percent value: percent={discount_rate_percent}, decimal={discount_rate_decimal}")
    else:
        # 蟆乗焚蛟､縺ｨ縺励※菫晏ｭ倥＆繧後※縺・ｋ蝣ｴ蜷茨ｼ井ｾ具ｼ・.20 = 20%・・
        discount_rate_percent = raw_rate * 100
        discount_rate_decimal = raw_rate
        print(f"[DEBUG PDF] Using as decimal value: percent={discount_rate_percent}, decimal={discount_rate_decimal}")
    
    # 譏守ｴｰ繝・・繧ｿ
    row_height = 6*mm
    y = table_top - header_height
    
    for detail in details:
        y -= row_height
        product = db.query(Product).filter(Product.product_id == detail.product_id).first()
        
        # 陦後・謠冗判
        pdf.rect(table_left, y, table_width, row_height, stroke=1, fill=0)
        
        # 邵ｦ邱・
        for pos in col_positions[1:]:
            pdf.line(pos, y, pos, y + row_height)
        
        # 繝・・繧ｿ
        row_text_y = y + 1.5*mm
        pdf.setFont(font_name, 7)
        
        # 蝠・刀蜷・
        product_name = product.name if product else ""
        pdf.drawString(col_positions[0] + 1*mm, row_text_y, product_name)
        
        # 謨ｰ驥・
        pdf.drawRightString(col_positions[1] + col_widths[1] - 1*mm, row_text_y, f"{detail.total_quantity}")
        
        # 蜊倅ｾ｡
        pdf.drawRightString(col_positions[2] + col_widths[2] - 1*mm, row_text_y, f"ﾂ･{detail.unit_price:,}")
        
        # 驥鷹｡搾ｼ育ｨ取栢・・
        amount = detail.amount
        pdf.drawRightString(col_positions[3] + col_widths[3] - 1*mm, row_text_y, f"ﾂ･{amount:,}")
        
        # 蜑ｲ蠑戊ｨ育ｮ暦ｼ亥牡蠑募ｯｾ雎｡螟悶ヵ繝ｩ繧ｰ繧偵メ繧ｧ繝・け・・
        is_discount_excluded = product.discount_exclusion_flag if product else False
        if is_discount_excluded:
            # 蜑ｲ蠑募ｯｾ雎｡螟・
            item_discount_rate = 0
            item_discount_amount = 0
            item_after_discount = amount
            pdf.drawCentredString(col_positions[4] + col_widths[4] / 2, row_text_y, "-")
            pdf.drawCentredString(col_positions[5] + col_widths[5] / 2, row_text_y, "-")
        else:
            # 蜑ｲ蠑暮←逕ｨ
            item_discount_rate = discount_rate_percent
            item_discount_amount = int(amount * discount_rate_decimal)
            item_after_discount = amount - item_discount_amount
            pdf.drawCentredString(col_positions[4] + col_widths[4] / 2, row_text_y, f"{item_discount_rate:.0f}%")
            pdf.drawRightString(col_positions[5] + col_widths[5] - 1*mm, row_text_y, f"ﾂ･{item_discount_amount:,}")
        
        # 蜑ｲ蠑募ｾ碁≡鬘・
        pdf.drawRightString(col_positions[6] + col_widths[6] - 1*mm, row_text_y, f"ﾂ･{item_after_discount:,}")
        
        # 繝弱Ν繝槫ｯｾ雎｡
        if product and product.quota_target_flag:
            pdf.drawCentredString(col_positions[7] + col_widths[7] / 2, row_text_y, "笳・)
        
        # 繝壹・繧ｸ騾√ｊ蛻､螳・
        if y < 100*mm:
            pdf.showPage()
            pdf.setFont(font_name, 7)
            y = height - 30*mm
    
    # ===== 髮・ｨ磯Κ蛻・ｼ郁ｩｳ邏ｰ迚茨ｼ・=====
    summary_top = y - 8*mm
    summary_left = table_left
    summary_width = table_width
    summary_row_height = 6*mm
    
    # 髮・ｨ医ユ繝ｼ繝悶Ν縺ｮ繝倥ャ繝繝ｼ
    pdf.setFillGray(0.85)
    pdf.rect(summary_left, summary_top - summary_row_height, summary_width, summary_row_height, stroke=1, fill=1)
    pdf.setFillGray(0)
    
    # 髮・ｨ医・繝・ム繝ｼ蛻怜ｹ・
    sum_col_widths = [50*mm, 35*mm, 18*mm, 35*mm, 42*mm]  # 鬆・岼縲・≡鬘阪∝牡蠑慕紫縲∝牡蠑暮｡阪∝牡蠑募ｾ碁≡鬘・
    sum_col_positions = [summary_left]
    for w in sum_col_widths[:-1]:
        sum_col_positions.append(sum_col_positions[-1] + w)
    
    pdf.setFont(font_name, 8)
    sum_header_y = summary_top - summary_row_height + 1.5*mm
    sum_headers = ["鬆・岼", "蟆剰ｨ磯≡鬘・, "蜑ｲ蠑慕紫", "蜑ｲ蠑暮｡・, "蜑ｲ蠑募ｾ碁≡鬘・]
    for i, header in enumerate(sum_headers):
        if i == 0:
            pdf.drawString(sum_col_positions[i] + 2*mm, sum_header_y, header)
        else:
            pdf.drawCentredString(sum_col_positions[i] + sum_col_widths[i] / 2, sum_header_y, header)
    
    # 邵ｦ邱夲ｼ磯寔險医・繝・ム繝ｼ・・
    for pos in sum_col_positions[1:]:
        pdf.line(pos, summary_top - summary_row_height, pos, summary_top)
    
    # 髮・ｨ郁｡後ョ繝ｼ繧ｿ・医ヮ繝ｫ繝槫ｯｾ雎｡縲√ヮ繝ｫ繝槫ｯｾ雎｡螟悶∝牡蠑募ｯｾ雎｡螟悶∝膚蜩∝ｰ剰ｨ医∝粋險磯≡鬘搾ｼ・
    # 繝弱Ν繝槫ｯｾ雎｡: quota_subtotal, quota_discount_amount, quota_total
    # 繝弱Ν繝槫ｯｾ雎｡螟・ non_quota_subtotal, non_quota_discount_amount, non_quota_total
    # 蜑ｲ蠑募ｯｾ雎｡螟・ non_discountable_amount
    
    product_subtotal = invoice.quota_subtotal + invoice.non_quota_subtotal + invoice.non_discountable_amount
    total_discount_amount = invoice.quota_discount_amount + invoice.non_quota_discount_amount
    total_after_discount = invoice.quota_total + invoice.non_quota_total + invoice.non_discountable_amount
    
    summary_data = [
        ("繝弱Ν繝槫ｯｾ雎｡蟆剰ｨ・, invoice.quota_subtotal, f"{discount_rate_percent:.0f}%", invoice.quota_discount_amount, invoice.quota_total),
        ("繝弱Ν繝槫ｯｾ雎｡螟門ｰ剰ｨ・, invoice.non_quota_subtotal, f"{discount_rate_percent:.0f}%", invoice.non_quota_discount_amount, invoice.non_quota_total),
        ("蜑ｲ蠑募ｯｾ雎｡螟門ｰ剰ｨ・, invoice.non_discountable_amount, "-", 0, invoice.non_discountable_amount),
        ("蝠・刀蟆剰ｨ・, product_subtotal, "-", total_discount_amount, total_after_discount),
    ]
    
    pdf.setFont(font_name, 8)
    sum_y = summary_top - summary_row_height
    
    for i, (label, subtotal, rate_str, disc_amt, after_disc) in enumerate(summary_data):
        sum_y -= summary_row_height
        
        # 閭梧勹・亥膚蜩∝ｰ剰ｨ医・蠑ｷ隱ｿ・・
        if i == 3:  # 蝠・刀蟆剰ｨ・
            pdf.setFillGray(0.92)
            pdf.rect(summary_left, sum_y, summary_width, summary_row_height, stroke=1, fill=1)
            pdf.setFillGray(0)
        else:
            pdf.rect(summary_left, sum_y, summary_width, summary_row_height, stroke=1, fill=0)
        
        # 邵ｦ邱・
        for pos in sum_col_positions[1:]:
            pdf.line(pos, sum_y, pos, sum_y + summary_row_height)
        
        row_text_y = sum_y + 1.5*mm
        
        # 繝ｩ繝吶Ν
        pdf.drawString(sum_col_positions[0] + 2*mm, row_text_y, label)
        
        # 蟆剰ｨ磯≡鬘・
        pdf.drawRightString(sum_col_positions[1] + sum_col_widths[1] - 2*mm, row_text_y, f"ﾂ･{subtotal:,}")
        
        # 蜑ｲ蠑慕紫
        pdf.drawCentredString(sum_col_positions[2] + sum_col_widths[2] / 2, row_text_y, rate_str)
        
        # 蜑ｲ蠑暮｡・
        if disc_amt > 0:
            pdf.drawRightString(sum_col_positions[3] + sum_col_widths[3] - 2*mm, row_text_y, f"ﾂ･{disc_amt:,}")
        else:
            pdf.drawCentredString(sum_col_positions[3] + sum_col_widths[3] / 2, row_text_y, "-")
        
        # 蜑ｲ蠑募ｾ碁≡鬘・
        pdf.drawRightString(sum_col_positions[4] + sum_col_widths[4] - 2*mm, row_text_y, f"ﾂ･{after_disc:,}")
    
    # 遞取栢蜷郁ｨ郁｡・
    sum_y -= summary_row_height
    pdf.setFillGray(0.88)
    pdf.rect(summary_left, sum_y, summary_width, summary_row_height, stroke=1, fill=1)
    pdf.setFillGray(0)
    for pos in sum_col_positions[1:]:
        pdf.line(pos, sum_y, pos, sum_y + summary_row_height)
    
    pdf.setFont(font_name, 9)
    row_text_y = sum_y + 1.5*mm
    pdf.drawString(sum_col_positions[0] + 2*mm, row_text_y, "蜷郁ｨ磯≡鬘搾ｼ育ｨ取栢・・)
    pdf.drawRightString(sum_col_positions[1] + sum_col_widths[1] - 2*mm, row_text_y, f"ﾂ･{product_subtotal:,}")
    pdf.drawCentredString(sum_col_positions[2] + sum_col_widths[2] / 2, row_text_y, "-")
    pdf.drawRightString(sum_col_positions[3] + sum_col_widths[3] - 2*mm, row_text_y, f"ﾂ･{total_discount_amount:,}")
    pdf.drawRightString(sum_col_positions[4] + sum_col_widths[4] - 2*mm, row_text_y, f"ﾂ･{invoice.total_amount_ex_tax:,}")
    
    # 豸郁ｲｻ遞手｡・
    sum_y -= summary_row_height
    pdf.rect(summary_left, sum_y, summary_width, summary_row_height, stroke=1, fill=0)
    for pos in sum_col_positions[1:]:
        pdf.line(pos, sum_y, pos, sum_y + summary_row_height)
    
    pdf.setFont(font_name, 8)
    row_text_y = sum_y + 1.5*mm
    pdf.drawString(sum_col_positions[0] + 2*mm, row_text_y, "豸郁ｲｻ遞・(10%)")
    pdf.drawRightString(sum_col_positions[4] + sum_col_widths[4] - 2*mm, row_text_y, f"ﾂ･{invoice.tax_amount:,}")
    
    # 遞手ｾｼ蜷郁ｨ郁｡鯉ｼ亥､ｧ縺阪￥蠑ｷ隱ｿ・・
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
    pdf.drawString(sum_col_positions[0] + 2*mm, row_text_y, "遞手ｾｼ蜷郁ｨ・)
    pdf.setFont(font_name, 14)
    pdf.drawRightString(sum_col_positions[4] + sum_col_widths[4] - 2*mm, row_text_y, f"ﾂ･{invoice.total_amount_inc_tax:,}")
    
    # ===== 謖ｯ霎ｼ蜈域ュ蝣ｱ =====
    bank_y = sum_y - 15*mm
    pdf.setFont(font_name, 10)
    pdf.drawString(20*mm, bank_y, "縲舌♀謖ｯ霎ｼ蜈医・)
    pdf.setFont(font_name, 9)
    pdf.drawString(20*mm, bank_y - 7*mm, f"{BANK_INFO['bank_name']}縲{BANK_INFO['branch_name']}")
    pdf.drawString(20*mm, bank_y - 14*mm, f"{BANK_INFO['account_type']}縲{BANK_INFO['account_number']}")
    pdf.drawString(20*mm, bank_y - 21*mm, f"蜿｣蠎ｧ蜷咲ｾｩ: {BANK_INFO['account_holder']}")
    pdf.drawString(20*mm, bank_y - 28*mm, f"險伜捷: {BANK_INFO['yucho_symbol']}縲逡ｪ蜿ｷ: {BANK_INFO['yucho_number']}")
    
    # ===== 蛯呵・ｬ・=====
    remarks_y = bank_y - 42*mm
    pdf.setFont(font_name, 10)
    pdf.drawString(20*mm, remarks_y, "縲仙ｙ閠・・)
    pdf.setFont(font_name, 9)
    
    # 菴・＠譖ｸ縺阪・蜀・ｮｹ繧貞・蜉・
    remark_offset = 7*mm
    if invoice.note:
        pdf.drawString(20*mm, remarks_y - remark_offset, f"繝ｻ{invoice.note}")
        remark_offset += 7*mm
  
    # ===== 繝輔ャ繧ｿ繝ｼ =====
    footer_y = 20*mm
    pdf.setFont(font_name, 9)
    pdf.drawCentredString(width / 2, footer_y, "荳願ｨ倥・騾壹ｊ縺碑ｫ区ｱら筏縺嶺ｸ翫￡縺ｾ縺吶・)
    
    pdf.save()
    buffer.seek(0)
    
    return buffer