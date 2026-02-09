"""PDF生成ヘルパー - 販売員請求書テンプレート準拠"""
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