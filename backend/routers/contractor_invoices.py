# -*- coding: utf-8 -*-
"""委託先請求書API"""
from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from database import get_db
from models import (
    ContractorInvoice, 
    ContractorInvoiceDetail, 
    DiscountRate,
    TaxRate,
    Product,
    Contractor
)
from dependencies import get_current_user
from pdf_generator import generate_contractor_invoice_pdf

router = APIRouter()


# Helper function to create ContractorInvoiceResponse
def create_invoice_response(invoice: ContractorInvoice) -> "ContractorInvoiceResponse":
    """委託先請求書レスポンスを作成"""
    return ContractorInvoiceResponse(
        id=invoice.id,
        contractor_id=invoice.contractor_id,
        contractor_name=invoice.contractor.name,
        discount_rate=float(invoice.discount_rate.rate),
        tax_rate=float(invoice.tax_rate.rate),
        invoice_date=invoice.invoice_date,
        payment_due_date=invoice.payment_due_date,
        payment_term=invoice.payment_term,
        note=invoice.note,
        non_discountable_amount=invoice.non_discountable_amount,
        quota_subtotal=invoice.quota_subtotal,
        quota_discount_amount=invoice.quota_discount_amount,
        quota_total=invoice.quota_total,
        non_quota_subtotal=invoice.non_quota_subtotal,
        non_quota_discount_amount=invoice.non_quota_discount_amount,
        non_quota_total=invoice.non_quota_total,
        total_amount_ex_tax=invoice.total_amount_ex_tax,
        total_discount_amount=invoice.total_discount_amount,
        total_after_discount=invoice.total_after_discount,
        tax_amount=invoice.tax_amount,
        total_amount_inc_tax=invoice.total_amount_inc_tax,
        details=[
            ContractorInvoiceDetailResponse(
                id=d.id,
                product_id=d.product_id,
                product_name=d.product.name,
                total_quantity=d.total_quantity,
                unit_price=d.unit_price,
                amount=d.amount
            )
            for d in invoice.details
        ]
    )


# Helper function to calculate optimal discount rate for contractors
def calculate_contractor_discount_rate(total_amount: int, db: Session) -> DiscountRate:
    """Calculate optimal discount rate for contractors based on total amount
    
    Rules:
    - >= 400,000: 40%
    - >= 200,000: 30%
    - >= 0: 20%
    """
    # Get all contractor discount rates ordered by threshold desc
    discount_rates = db.query(DiscountRate).filter(
        DiscountRate.customer_flag == False,  # 委託先フラグ
        DiscountRate.deleted_flag == False
    ).order_by(DiscountRate.threshold_amount.desc()).all()
    
    # Find the highest applicable rate
    for rate in discount_rates:
        if total_amount >= rate.threshold_amount:
            return rate
    
    # Default to 20% (0.20) if nothing found
    default_rate = db.query(DiscountRate).filter(
        DiscountRate.customer_flag == False,
        DiscountRate.rate == 0.20,
        DiscountRate.deleted_flag == False
    ).first()
    
    return default_rate


class ContractorInvoiceDetailRequest(BaseModel):
    """委託先請求書明細リクエスト"""
    product_id: int
    total_quantity: int
    unit_price: Optional[int] = None


class ContractorInvoiceCreateRequest(BaseModel):
    """委託先請求書作成リクエスト"""
    contractor_id: int
    tax_rate_id: int
    invoice_date: date
    payment_due_date: Optional[date] = None
    payment_term: Optional[str] = None
    note: Optional[str] = None
    details: List[ContractorInvoiceDetailRequest]


class ContractorInvoiceUpdateRequest(BaseModel):
    """委託先請求書更新リクエスト"""
    discount_rate_id: Optional[int] = None
    tax_rate_id: Optional[int] = None
    invoice_date: Optional[date] = None
    payment_due_date: Optional[date] = None
    payment_term: Optional[str] = None
    note: Optional[str] = None
    details: Optional[List[ContractorInvoiceDetailRequest]] = None


class ContractorInvoiceDetailResponse(BaseModel):
    """委託先請求書明細レスポンス"""
    id: str
    product_id: int
    product_name: str
    total_quantity: int
    unit_price: int
    amount: int


class ContractorInvoiceResponse(BaseModel):
    """委託先請求書レスポンス"""
    id: str
    contractor_id: int
    contractor_name: str
    discount_rate: float
    tax_rate: float
    invoice_date: date
    payment_due_date: Optional[date]
    payment_term: Optional[str]
    note: Optional[str]
    non_discountable_amount: int
    quota_subtotal: int
    quota_discount_amount: int
    quota_total: int
    non_quota_subtotal: int
    non_quota_discount_amount: int
    non_quota_total: int
    total_amount_ex_tax: int
    total_discount_amount: int
    total_after_discount: int
    tax_amount: int
    total_amount_inc_tax: int
    details: List[ContractorInvoiceDetailResponse]


@router.post("/", response_model=ContractorInvoiceResponse)
def create_contractor_invoice(
    request: ContractorInvoiceCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """委託先請求書を手動作成"""
    
    # 委託先の存在確認
    contractor = db.query(Contractor).filter(
        Contractor.id == request.contractor_id,
        Contractor.deleted_flag == False
    ).first()
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    
    # 税率取得
    tax_rate = db.query(TaxRate).filter(
        TaxRate.id == request.tax_rate_id,
        TaxRate.deleted_flag == False
    ).first()
    if not tax_rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")
    
    # 商品明細の計算
    quota_subtotal = 0
    non_quota_subtotal = 0
    non_discountable_amount = 0
    details_data = []
    
    for detail in request.details:
        product = db.query(Product).filter(Product.id == detail.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {detail.product_id} not found")
        
        quantity = detail.total_quantity
        unit_price = detail.unit_price if detail.unit_price is not None else product.price
        amount = quantity * unit_price
        
        # 割引対象外の判定
        if product.discount_exclusion_flag:
            non_discountable_amount += amount
        # ノルマ対象/対象外の判定
        elif product.quota_target_flag:
            quota_subtotal += amount
        else:
            non_quota_subtotal += amount
        
        details_data.append({
            "product_id": product.id,
            "total_quantity": quantity,
            "unit_price": unit_price,
            "amount": amount
        })
    
    # 合計金額で割引率を自動判定
    total_subtotal = quota_subtotal + non_quota_subtotal
    discount_rate = calculate_contractor_discount_rate(total_subtotal, db)
    
    if not discount_rate:
        raise HTTPException(status_code=500, detail="Could not determine discount rate")
    
    # 割引額の計算（rateは既に小数値：0.20=20%）
    discount_rate_value = float(discount_rate.rate)
    quota_discount_amount = int(quota_subtotal * discount_rate_value)
    non_quota_discount_amount = int(non_quota_subtotal * discount_rate_value)
    
    # 割引後金額
    quota_total = quota_subtotal - quota_discount_amount
    non_quota_total = non_quota_subtotal - non_quota_discount_amount
    total_amount_ex_tax = quota_total + non_quota_total + non_discountable_amount
    
    # 割引額合計と割引後合計金額
    total_discount_amount = quota_discount_amount + non_quota_discount_amount
    total_after_discount = total_amount_ex_tax
    
    # 消費税額
    tax_amount = int(total_amount_ex_tax * float(tax_rate.rate) / 100)
    total_amount_inc_tax = total_amount_ex_tax + tax_amount
    
    # 請求書作成
    invoice = ContractorInvoice(
        contractor_id=request.contractor_id,
        discount_rate_id=discount_rate.id,
        tax_rate_id=request.tax_rate_id,
        invoice_date=request.invoice_date,
        payment_due_date=request.payment_due_date,
        payment_term=request.payment_term,
        note=request.note,
        non_discountable_amount=non_discountable_amount,
        quota_subtotal=quota_subtotal,
        quota_discount_amount=quota_discount_amount,
        quota_total=quota_total,
        non_quota_subtotal=non_quota_subtotal,
        non_quota_discount_amount=non_quota_discount_amount,
        non_quota_total=non_quota_total,
        total_amount_ex_tax=total_amount_ex_tax,
        total_discount_amount=total_discount_amount,
        total_after_discount=total_after_discount,
        tax_amount=tax_amount,
        total_amount_inc_tax=total_amount_inc_tax
    )
    
    db.add(invoice)
    db.flush()
    
    # 明細作成
    for detail_data in details_data:
        detail = ContractorInvoiceDetail(
            contractor_invoice_id=invoice.id,
            **detail_data
        )
        db.add(detail)
    
    db.commit()
    db.refresh(invoice)
    
    # レスポンス作成
    return create_invoice_response(invoice)


@router.get("/", response_model=List[ContractorInvoiceResponse])
def get_contractor_invoices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """委託先請求書一覧取得"""
    invoices = db.query(ContractorInvoice).filter(
        ContractorInvoice.deleted_flag == False
    ).order_by(
        ContractorInvoice.invoice_date.desc()
    ).offset(skip).limit(limit).all()
    
    return [create_invoice_response(inv) for inv in invoices]


@router.get("/{invoice_id}", response_model=ContractorInvoiceResponse)
def get_contractor_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """委託先請求書詳細取得"""
    invoice = db.query(ContractorInvoice).filter(
        ContractorInvoice.id == invoice_id,
        ContractorInvoice.deleted_flag == False
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return create_invoice_response(invoice)


@router.put("/{invoice_id}", response_model=ContractorInvoiceResponse)
def update_contractor_invoice(
    invoice_id: str,
    request: ContractorInvoiceUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """委託先請求書更新"""
    invoice = db.query(ContractorInvoice).filter(ContractorInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # 更新可能なフィールド
    if request.discount_rate_id is not None:
        invoice.discount_rate_id = request.discount_rate_id
        # 割引率変更時は金額を再計算
        discount_rate = db.query(DiscountRate).filter(DiscountRate.id == request.discount_rate_id).first()
        if discount_rate:
            discount_rate_value = float(discount_rate.rate) / 100
            invoice.quota_discount_amount = int(invoice.quota_subtotal * discount_rate_value)
            invoice.non_quota_discount_amount = int(invoice.non_quota_subtotal * discount_rate_value)
            invoice.quota_total = invoice.quota_subtotal - invoice.quota_discount_amount
            invoice.non_quota_total = invoice.non_quota_subtotal - invoice.non_quota_discount_amount
            invoice.total_amount_ex_tax = invoice.quota_total + invoice.non_quota_total + invoice.non_discountable_amount
            
            # 割引額合計と割引後合計金額
            invoice.total_discount_amount = invoice.quota_discount_amount + invoice.non_quota_discount_amount
            invoice.total_after_discount = invoice.total_amount_ex_tax
            
            # 税率取得
            tax_rate = db.query(TaxRate).filter(TaxRate.id == invoice.tax_rate_id).first()
            if tax_rate:
                invoice.tax_amount = int(invoice.total_amount_ex_tax * float(tax_rate.rate) / 100)
                invoice.total_amount_inc_tax = invoice.total_amount_ex_tax + invoice.tax_amount
    
    if request.tax_rate_id is not None:
        invoice.tax_rate_id = request.tax_rate_id
    
    if request.invoice_date is not None:
        invoice.invoice_date = request.invoice_date
    
    if request.payment_due_date is not None:
        invoice.payment_due_date = request.payment_due_date
    
    if request.payment_term is not None:
        invoice.payment_term = request.payment_term
    
    if request.note is not None:
        invoice.note = request.note
    
    if request.details is not None:
        # 既存の明細を削除
        db.query(ContractorInvoiceDetail).filter(
            ContractorInvoiceDetail.contractor_invoice_id == invoice_id
        ).delete()
        
        # 新しい明細を追加し、金額を再計算
        quota_subtotal = 0
        non_quota_subtotal = 0
        non_discountable_amount = 0
        
        for detail in request.details:
            product = db.query(Product).filter(Product.id == detail.product_id).first()
            if not product:
                continue
            
            quantity = detail.total_quantity
            unit_price = detail.unit_price if detail.unit_price is not None else product.price
            amount = quantity * unit_price
            
            # 割引対象外の判定
            if product.discount_exclusion_flag:
                non_discountable_amount += amount
            # ノルマ対象/対象外の判定
            elif product.quota_target_flag:
                quota_subtotal += amount
            else:
                non_quota_subtotal += amount
            
            new_detail = ContractorInvoiceDetail(
                contractor_invoice_id=invoice_id,
                product_id=product.id,
                total_quantity=quantity,
                unit_price=unit_price,
                amount=amount
            )
            db.add(new_detail)
        
        # 金額の再計算
        invoice.non_discountable_amount = non_discountable_amount
        invoice.quota_subtotal = quota_subtotal
        invoice.non_quota_subtotal = non_quota_subtotal
        
        discount_rate_value = float(invoice.discount_rate.rate)
        invoice.quota_discount_amount = int(quota_subtotal * discount_rate_value)
        invoice.non_quota_discount_amount = int(non_quota_subtotal * discount_rate_value)
        invoice.quota_total = quota_subtotal - invoice.quota_discount_amount
        invoice.non_quota_total = non_quota_subtotal - invoice.non_quota_discount_amount
        invoice.total_amount_ex_tax = invoice.quota_total + invoice.non_quota_total + non_discountable_amount
        
        # 割引額合計と割引後合計金額
        invoice.total_discount_amount = invoice.quota_discount_amount + invoice.non_quota_discount_amount
        invoice.total_after_discount = invoice.total_amount_ex_tax
        
        tax_rate = db.query(TaxRate).filter(TaxRate.id == invoice.tax_rate_id).first()
        if tax_rate:
            invoice.tax_amount = int(invoice.total_amount_ex_tax * float(tax_rate.rate) / 100)
            invoice.total_amount_inc_tax = invoice.total_amount_ex_tax + invoice.tax_amount
    
    db.commit()
    db.refresh(invoice)
    
    return create_invoice_response(invoice)


@router.get("/{invoice_id}/pdf")
async def generate_contractor_invoice_pdf_endpoint(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """委託先請求書PDF生成"""
    invoice = db.query(ContractorInvoice).filter(ContractorInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    pdf_buffer = generate_contractor_invoice_pdf(invoice, db)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=contractor_invoice_{invoice.id}.pdf"
        }
    )


@router.delete("/{invoice_id}")
def delete_contractor_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """委託先請求書削除"""
    invoice = db.query(ContractorInvoice).filter(ContractorInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    db.delete(invoice)
    db.commit()
    
    return {"message": "Invoice deleted successfully"}
