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

router = APIRouter()


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
    
    # Default to 20% if nothing found
    default_rate = db.query(DiscountRate).filter(
        DiscountRate.customer_flag == False,
        DiscountRate.rate == 20,
        DiscountRate.deleted_flag == False
    ).first()
    
    return default_rate


class ContractorInvoiceCreateRequest(BaseModel):
    """委託先請求書作成リクエスト"""
    contractor_id: int
    start_date: date
    end_date: date
    invoice_date: Optional[date] = None
    note: Optional[str] = None
    details: List[dict]  # [{"product_id": 1, "quantity": 10, "unit_price": 1000}, ...]


class ContractorInvoiceUpdateRequest(BaseModel):
    """委託先請求書更新リクエスト"""
    discount_rate_id: Optional[int] = None
    invoice_date: Optional[date] = None
    receipt_date: Optional[date] = None
    note: Optional[str] = None
    details: Optional[List[dict]] = None


class ContractorInvoiceDetailResponse(BaseModel):
    """委託先請求書明細レスポンス"""
    id: int
    product_id: int
    product_name: str
    total_quantity: int
    unit_price: int
    amount: int


class ContractorInvoiceResponse(BaseModel):
    """委託先請求書レスポンス"""
    id: int
    contractor_id: int
    contractor_name: str
    invoice_number: str
    start_date: date
    end_date: date
    discount_rate: float
    invoice_date: Optional[date]
    receipt_date: Optional[date]
    note: Optional[str]
    quota_subtotal: int
    quota_discount_amount: int
    quota_total: int
    non_quota_subtotal: int
    non_quota_discount_amount: int
    non_quota_total: int
    total_amount_ex_tax: int
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
    
    # 税率取得（10%固定）
    tax_rate = db.query(TaxRate).filter(TaxRate.deleted_flag == False).first()
    if not tax_rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")
    
    # 商品明細の計算
    quota_subtotal = 0
    non_quota_subtotal = 0
    details_data = []
    
    for detail in request.details:
        product = db.query(Product).filter(Product.id == detail["product_id"]).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {detail['product_id']} not found")
        
        quantity = detail["quantity"]
        unit_price = detail.get("unit_price", product.price)
        amount = quantity * unit_price
        
        # ノルマ対象/対象外の判定
        if product.quota_target_flag:
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
    
    # 割引額の計算
    discount_rate_value = float(discount_rate.rate) / 100
    quota_discount_amount = int(quota_subtotal * discount_rate_value)
    non_quota_discount_amount = int(non_quota_subtotal * discount_rate_value)
    
    # 割引後金額
    quota_total = quota_subtotal - quota_discount_amount
    non_quota_total = non_quota_subtotal - non_quota_discount_amount
    total_amount_ex_tax = quota_total + non_quota_total
    
    # 消費税額
    tax_amount = int(total_amount_ex_tax * float(tax_rate.rate) / 100)
    total_amount_inc_tax = total_amount_ex_tax + tax_amount
    
    # 請求書作成
    invoice = ContractorInvoice(
        contractor_id=request.contractor_id,
        invoice_number="[COMPANY_REGISTRATION_NUMBER]",
        start_date=request.start_date,
        end_date=request.end_date,
        discount_rate_id=discount_rate.id,
        invoice_date=request.invoice_date,
        note=request.note,
        quota_subtotal=quota_subtotal,
        quota_discount_amount=quota_discount_amount,
        quota_total=quota_total,
        non_quota_subtotal=non_quota_subtotal,
        non_quota_discount_amount=non_quota_discount_amount,
        non_quota_total=non_quota_total,
        total_amount_ex_tax=total_amount_ex_tax,
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
    return ContractorInvoiceResponse(
        id=invoice.id,
        contractor_id=invoice.contractor_id,
        contractor_name=contractor.name,
        invoice_number=invoice.invoice_number,
        start_date=invoice.start_date,
        end_date=invoice.end_date,
        discount_rate=float(discount_rate.rate),
        invoice_date=invoice.invoice_date,
        receipt_date=invoice.receipt_date,
        note=invoice.note,
        quota_subtotal=invoice.quota_subtotal,
        quota_discount_amount=invoice.quota_discount_amount,
        quota_total=invoice.quota_total,
        non_quota_subtotal=invoice.non_quota_subtotal,
        non_quota_discount_amount=invoice.non_quota_discount_amount,
        non_quota_total=invoice.non_quota_total,
        total_amount_ex_tax=invoice.total_amount_ex_tax,
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


@router.get("/", response_model=List[ContractorInvoiceResponse])
def get_contractor_invoices(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """委託先請求書一覧取得"""
    invoices = db.query(ContractorInvoice).order_by(
        ContractorInvoice.end_date.desc()
    ).offset(skip).limit(limit).all()
    
    return [
        ContractorInvoiceResponse(
            id=inv.id,
            contractor_id=inv.contractor_id,
            contractor_name=inv.contractor.name,
            invoice_number=inv.invoice_number,
            start_date=inv.start_date,
            end_date=inv.end_date,
            discount_rate=float(inv.discount_rate.rate),
            invoice_date=inv.invoice_date,
            receipt_date=inv.receipt_date,
            note=inv.note,
            quota_subtotal=inv.quota_subtotal,
            quota_discount_amount=inv.quota_discount_amount,
            quota_total=inv.quota_total,
            non_quota_subtotal=inv.non_quota_subtotal,
            non_quota_discount_amount=inv.non_quota_discount_amount,
            non_quota_total=inv.non_quota_total,
            total_amount_ex_tax=inv.total_amount_ex_tax,
            tax_amount=inv.tax_amount,
            total_amount_inc_tax=inv.total_amount_inc_tax,
            details=[
                ContractorInvoiceDetailResponse(
                    id=d.id,
                    product_id=d.product_id,
                    product_name=d.product.name,
                    total_quantity=d.total_quantity,
                    unit_price=d.unit_price,
                    amount=d.amount
                )
                for d in inv.details
            ]
        )
        for inv in invoices
    ]


@router.get("/{invoice_id}", response_model=ContractorInvoiceResponse)
def get_contractor_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """委託先請求書詳細取得"""
    invoice = db.query(ContractorInvoice).filter(ContractorInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return ContractorInvoiceResponse(
        id=invoice.id,
        contractor_id=invoice.contractor_id,
        contractor_name=invoice.contractor.name,
        invoice_number=invoice.invoice_number,
        start_date=invoice.start_date,
        end_date=invoice.end_date,
        discount_rate=float(invoice.discount_rate.rate),
        invoice_date=invoice.invoice_date,
        receipt_date=invoice.receipt_date,
        note=invoice.note,
        quota_subtotal=invoice.quota_subtotal,
        quota_discount_amount=invoice.quota_discount_amount,
        quota_total=invoice.quota_total,
        non_quota_subtotal=invoice.non_quota_subtotal,
        non_quota_discount_amount=invoice.non_quota_discount_amount,
        non_quota_total=invoice.non_quota_total,
        total_amount_ex_tax=invoice.total_amount_ex_tax,
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


@router.put("/{invoice_id}", response_model=ContractorInvoiceResponse)
def update_contractor_invoice(
    invoice_id: int,
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
            invoice.total_amount_ex_tax = invoice.quota_total + invoice.non_quota_total
            
            # 税率取得
            tax_rate = db.query(TaxRate).filter(TaxRate.deleted_flag == False).first()
            if tax_rate:
                invoice.tax_amount = int(invoice.total_amount_ex_tax * float(tax_rate.rate) / 100)
                invoice.total_amount_inc_tax = invoice.total_amount_ex_tax + invoice.tax_amount
    
    if request.invoice_date is not None:
        invoice.invoice_date = request.invoice_date
    
    if request.receipt_date is not None:
        invoice.receipt_date = request.receipt_date
    
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
        
        for detail in request.details:
            product = db.query(Product).filter(Product.id == detail["product_id"]).first()
            if not product:
                continue
            
            quantity = detail["quantity"]
            unit_price = detail.get("unit_price", product.price)
            amount = quantity * unit_price
            
            if product.quota_target_flag:
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
        invoice.quota_subtotal = quota_subtotal
        invoice.non_quota_subtotal = non_quota_subtotal
        
        discount_rate_value = float(invoice.discount_rate.rate) / 100
        invoice.quota_discount_amount = int(quota_subtotal * discount_rate_value)
        invoice.non_quota_discount_amount = int(non_quota_subtotal * discount_rate_value)
        invoice.quota_total = quota_subtotal - invoice.quota_discount_amount
        invoice.non_quota_total = non_quota_subtotal - invoice.non_quota_discount_amount
        invoice.total_amount_ex_tax = invoice.quota_total + invoice.non_quota_total
        
        tax_rate = db.query(TaxRate).filter(TaxRate.deleted_flag == False).first()
        if tax_rate:
            invoice.tax_amount = int(invoice.total_amount_ex_tax * float(tax_rate.rate) / 100)
            invoice.total_amount_inc_tax = invoice.total_amount_ex_tax + invoice.tax_amount
    
    db.commit()
    db.refresh(invoice)
    
    return ContractorInvoiceResponse(
        id=invoice.id,
        contractor_id=invoice.contractor_id,
        contractor_name=invoice.contractor.name,
        invoice_number=invoice.invoice_number,
        start_date=invoice.start_date,
        end_date=invoice.end_date,
        discount_rate=float(invoice.discount_rate.rate),
        invoice_date=invoice.invoice_date,
        receipt_date=invoice.receipt_date,
        note=invoice.note,
        quota_subtotal=invoice.quota_subtotal,
        quota_discount_amount=invoice.quota_discount_amount,
        quota_total=invoice.quota_total,
        non_quota_subtotal=invoice.non_quota_subtotal,
        non_quota_discount_amount=invoice.non_quota_discount_amount,
        non_quota_total=invoice.non_quota_total,
        total_amount_ex_tax=invoice.total_amount_ex_tax,
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


@router.delete("/{invoice_id}")
def delete_contractor_invoice(
    invoice_id: int,
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
