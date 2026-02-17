# -*- coding: utf-8 -*-
"""販売員請求書API"""
from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from pydantic import BaseModel

from database import get_db
from models import (
    SalesInvoice, 
    SalesInvoiceDetail, 
    DeliveryNote, 
    DeliveryNoteDetail,
    DiscountRate,
    TaxRate,
    Product,
    SalesPerson
)
from dependencies import get_current_user
from pdf_generator import generate_sales_invoice_pdf, generate_sales_receipt_pdf

router = APIRouter()


def calculate_period_from_invoice_date(invoice_date: date) -> tuple[date, date]:
    """Calculate billing period from invoice date (closing date)
    
    Period: Previous month 21st ~ invoice_date (20th)
    Example: invoice_date=2026-01-20 -> period: 2025-12-21 ~ 2026-01-20
    """
    # Start date = previous month 21st
    if invoice_date.month == 1:
        start_date = date(invoice_date.year - 1, 12, 21)
    else:
        start_date = date(invoice_date.year, invoice_date.month - 1, 21)
    
    # End date = invoice_date (should be 20th)
    end_date = invoice_date
    
    return start_date, end_date


class InvoiceUpdateRequest(BaseModel):
    discount_rate_id: Optional[int] = None
    receipt_date: Optional[date] = None
    note: Optional[str] = None


# Helper function to calculate optimal discount rate
def calculate_optimal_discount_rate(total_amount: int, db: Session) -> DiscountRate:
    """Calculate optimal discount rate based on total amount
    
    Rules:
    - >= 400,000: 40%
    - >= 200,000: 30%
    - >= 42,000: 20%
    - < 42,000: 0% (can be manually changed to 10% later)
    """
    # Get all sales person discount rates ordered by threshold desc
    discount_rates = db.query(DiscountRate).filter(
        DiscountRate.sales_person_flag == True,
        DiscountRate.deleted_flag == False
    ).order_by(DiscountRate.threshold_amount.desc()).all()
    
    # Find the highest applicable rate
    for rate in discount_rates:
        if total_amount >= rate.threshold_amount and rate.rate > 0:
            return rate
    
    # If no rate >= 20% applies, return 0% rate
    zero_rate = db.query(DiscountRate).filter(
        DiscountRate.sales_person_flag == True,
        DiscountRate.rate == 0,
        DiscountRate.deleted_flag == False
    ).first()
    
    return zero_rate


class InvoiceGenerateRequest(BaseModel):
    """請求書生成リクエスト"""
    sales_person_id: int
    invoice_date: date  # 請求日（締め日）= 20日


class BulkInvoiceGenerateRequest(BaseModel):
    """一括請求書生成リクエスト"""
    closing_date: date  # 締め日（必須）
    sales_person_ids: Optional[List[int]] = None  # None=全販売員、指定=特定販売員のみ


class DiscountRateUpdateRequest(BaseModel):
    """割引率変更リクエスト"""
    discount_rate_id: int


class InvoiceDetailResponse(BaseModel):
    """請求書明細レスポンス"""
    id: str
    product_id: int
    product_name: str
    total_quantity: int
    unit_price: int
    amount: int


class InvoiceResponse(BaseModel):
    """請求書レスポンス"""
    id: str
    sales_person_id: int
    sales_person_name: str
    invoice_number: str
    tax_rate_id: int
    invoice_date: date
    receipt_date: Optional[date] = None
    discount_rate_id: int
    discount_rate: float
    note: Optional[str] = None
    non_discountable_amount: int = 0
    quota_subtotal: int
    quota_discount_amount: int
    quota_total: int
    non_quota_subtotal: int
    non_quota_discount_amount: int
    non_quota_total: int
    total_amount_ex_tax: int
    tax_amount: int
    total_amount_inc_tax: int
    details: List[InvoiceDetailResponse]


def generate_invoice_for_sales_person(
    sales_person_id: int,
    invoice_date: date,
    db: Session
) -> Optional[InvoiceResponse]:
    """Generate invoice for a specific sales person
    
    Args:
        sales_person_id: Sales person ID
        invoice_date: Invoice date (closing date, should be 20th)
        db: Database session
    
    Returns:
        InvoiceResponse or None if no delivery notes found
    """
    # Calculate period from invoice_date
    start_date, end_date = calculate_period_from_invoice_date(invoice_date)
    
    # Get delivery notes for the period
    delivery_notes = db.query(DeliveryNote).filter(
        DeliveryNote.sales_person_id == sales_person_id,
        DeliveryNote.delivery_date >= start_date,
        DeliveryNote.delivery_date <= end_date
    ).all()
    
    if not delivery_notes:
        return None  # No delivery notes, skip this sales person
    
    # Get tax rate
    tax_rate = db.query(TaxRate).filter(
        TaxRate.deleted_flag == False
    ).first()
    if not tax_rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")
    
    delivery_note_ids = [dn.delivery_note_id for dn in delivery_notes]
    
    # Aggregate by product
    aggregated_data = db.query(
        DeliveryNoteDetail.product_id,
        Product.quota_target_flag,
        func.sum(DeliveryNoteDetail.quantity).label('total_quantity'),
        DeliveryNoteDetail.unit_price
    ).join(
        Product, DeliveryNoteDetail.product_id == Product.product_id
    ).filter(
        DeliveryNoteDetail.delivery_note_id.in_(delivery_note_ids)
    ).group_by(
        DeliveryNoteDetail.product_id,
        Product.quota_target_flag,
        DeliveryNoteDetail.unit_price
    ).all()
    
    quota_subtotal = 0
    non_quota_subtotal = 0
    invoice_details = []
    
    for item in aggregated_data:
        amount = item.total_quantity * item.unit_price
        
        if item.quota_target_flag:
            quota_subtotal += amount
        else:
            non_quota_subtotal += amount
        
        invoice_details.append({
            'product_id': item.product_id,
            'total_quantity': item.total_quantity,
            'unit_price': item.unit_price,
            'amount': amount
        })
    
    # Calculate total for discount determination
    total_subtotal = quota_subtotal + non_quota_subtotal
    
    # Auto-calculate optimal discount rate
    discount_rate = calculate_optimal_discount_rate(total_subtotal, db)
    
    # Calculate discount
    discount_rate_value = float(discount_rate.rate)
    # If rate >= 1, it's stored as percentage (10 = 10%), convert to decimal
    if discount_rate_value >= 1:
        discount_rate_value = discount_rate_value / 100
    
    quota_discount_amount = int(quota_subtotal * discount_rate_value)
    non_quota_discount_amount = int(non_quota_subtotal * discount_rate_value)
    
    quota_total = quota_subtotal - quota_discount_amount
    non_quota_total = non_quota_subtotal - non_quota_discount_amount
    
    total_amount_ex_tax = quota_total + non_quota_total
    
    # Calculate tax (floor rounding) - apply to total amount excluding tax
    tax_rate_value = float(tax_rate.rate)
    # If tax rate >= 1, it's stored as percentage (10 = 10%), convert to decimal
    if tax_rate_value >= 1:
        tax_rate_value = tax_rate_value / 100
    tax_amount = int(total_amount_ex_tax * tax_rate_value)
    
    total_amount_inc_tax = total_amount_ex_tax + tax_amount
    
    # Calculate receipt_date = 25th of invoice_date month
    receipt_date = invoice_date.replace(day=25)
    
    # Check if invoice already exists for this sales person and invoice_date
    existing_invoice = db.query(SalesInvoice).filter(
        SalesInvoice.sales_person_id == sales_person_id,
        SalesInvoice.invoice_date == invoice_date
    ).first()
    
    if existing_invoice:
        # Update existing invoice
        existing_invoice.discount_rate_id = discount_rate.discount_rate_id
        existing_invoice.receipt_date = receipt_date
        existing_invoice.note = '御品代として'
        existing_invoice.quota_subtotal = quota_subtotal
        existing_invoice.quota_discount_amount = quota_discount_amount
        existing_invoice.quota_total = quota_total
        existing_invoice.non_quota_subtotal = non_quota_subtotal
        existing_invoice.non_quota_discount_amount = non_quota_discount_amount
        existing_invoice.non_quota_total = non_quota_total
        existing_invoice.total_amount_ex_tax = total_amount_ex_tax
        existing_invoice.tax_amount = tax_amount
        existing_invoice.total_amount_inc_tax = total_amount_inc_tax
        
        # Delete old details
        db.query(SalesInvoiceDetail).filter(
            SalesInvoiceDetail.sales_invoice_id == existing_invoice.sales_invoice_id
        ).delete()
        
        invoice = existing_invoice
    else:
        # Create new invoice record
        invoice = SalesInvoice(
            sales_person_id=sales_person_id,
            tax_rate_id=tax_rate.tax_rate_id,
            invoice_date=invoice_date,
            receipt_date=receipt_date,
            discount_rate_id=discount_rate.discount_rate_id,
            note='御品代として',
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
    
    db.commit()
    db.refresh(invoice)
    
    # Create invoice details
    detail_responses = []
    for detail_data in invoice_details:
        detail = SalesInvoiceDetail(
            sales_invoice_id=invoice.sales_invoice_id,
            **detail_data
        )
        db.add(detail)
        db.flush()
        
        product = db.query(Product).filter(Product.product_id == detail.product_id).first()
        detail_responses.append(InvoiceDetailResponse(
            id=str(detail.sales_invoice_detail_id),
            product_id=detail.product_id,
            product_name=product.name if product else "",
            total_quantity=detail.total_quantity,
            unit_price=detail.unit_price,
            amount=detail.amount
        ))
    
    db.commit()
    
    # Get sales person name
    sales_person = db.query(SalesPerson).filter(
        SalesPerson.sales_person_id == sales_person_id
    ).first()
    
    return InvoiceResponse(
        id=str(invoice.sales_invoice_id),
        sales_person_id=invoice.sales_person_id,
        sales_person_name=sales_person.name if sales_person else "",
        invoice_number="[COMPANY_REGISTRATION_NUMBER]",
        tax_rate_id=invoice.tax_rate_id,
        invoice_date=invoice.invoice_date,
        receipt_date=invoice.receipt_date,
        discount_rate_id=invoice.discount_rate_id,
        discount_rate=discount_rate_value,
        note=invoice.note,
        non_discountable_amount=invoice.non_discountable_amount or 0,
        quota_subtotal=invoice.quota_subtotal,
        quota_discount_amount=invoice.quota_discount_amount,
        quota_total=invoice.quota_total,
        non_quota_subtotal=invoice.non_quota_subtotal,
        non_quota_discount_amount=invoice.non_quota_discount_amount,
        non_quota_total=invoice.non_quota_total,
        total_amount_ex_tax=invoice.total_amount_ex_tax,
        tax_amount=invoice.tax_amount,
        total_amount_inc_tax=invoice.total_amount_inc_tax,
        details=detail_responses
    )



@router.post("/bulk-generate")
async def bulk_generate_sales_invoices(
    request: BulkInvoiceGenerateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Bulk generate sales invoices
    
    Generate invoices for all or selected sales persons for a specific closing date.
    Period is automatically calculated: (previous month 21st) to (closing date)
    """
    # Get target sales persons
    if request.sales_person_ids:
        sales_persons = db.query(SalesPerson).filter(
            SalesPerson.sales_person_id.in_(request.sales_person_ids),
            SalesPerson.deleted_flag == False
        ).all()
    else:
        sales_persons = db.query(SalesPerson).filter(
            SalesPerson.deleted_flag == False
        ).all()
    
    if not sales_persons:
        raise HTTPException(status_code=404, detail="No sales persons found")
    
    # Calculate period from closing_date
    start_date, end_date = calculate_period_from_invoice_date(request.closing_date)
    
    # Generate invoices
    generated_invoices = []
    skipped_persons = []
    
    for sales_person in sales_persons:
        invoice = generate_invoice_for_sales_person(
            sales_person.sales_person_id,
            request.closing_date,
            db
        )
        if invoice:
            generated_invoices.append(invoice)
        else:
            skipped_persons.append(sales_person.name)
    
    return {
        "success": True,
        "generated_count": len(generated_invoices),
        "skipped_count": len(skipped_persons),
        "skipped_persons": skipped_persons,
        "invoices": generated_invoices,
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
    }


@router.patch("/{invoice_id}")
async def update_invoice_fields(
    invoice_id: str,
    update_data: InvoiceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update invoice fields like discount_rate_id and note"""
    invoice = db.query(SalesInvoice).filter(
        SalesInvoice.sales_invoice_id == invoice_id,
        SalesInvoice.deleted_flag == False
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Update fields if provided
    if update_data.discount_rate_id is not None:
        # 割引率を変更する場合は、金額も再計算
        discount_rate = db.query(DiscountRate).filter(DiscountRate.discount_rate_id == update_data.discount_rate_id).first()
        if not discount_rate:
            raise HTTPException(status_code=404, detail="Discount rate not found")
        
        invoice.discount_rate_id = update_data.discount_rate_id
        
        # 割引額と合計を再計算
        discount_rate_value = float(discount_rate.rate)
        if discount_rate_value >= 1:
            discount_rate_value = discount_rate_value / 100
        invoice.quota_discount_amount = int(invoice.quota_subtotal * discount_rate_value)
        invoice.quota_total = invoice.quota_subtotal - invoice.quota_discount_amount
        invoice.non_quota_discount_amount = int(invoice.non_quota_subtotal * discount_rate_value)
        invoice.non_quota_total = invoice.non_quota_subtotal - invoice.non_quota_discount_amount
        invoice.total_amount_ex_tax = invoice.quota_total + invoice.non_quota_total + (invoice.non_discountable_amount or 0)
        
        # 消費税を計算
        tax_rate = db.query(TaxRate).filter(TaxRate.deleted_flag == False).first()
        if tax_rate:
            tax_rate_value = float(tax_rate.rate)
            if tax_rate_value >= 1:
                tax_rate_value = tax_rate_value / 100
            invoice.tax_amount = int(invoice.total_amount_ex_tax * tax_rate_value)
        invoice.total_amount_inc_tax = invoice.total_amount_ex_tax + invoice.tax_amount
    
    if update_data.note is not None:
        invoice.note = update_data.note
    
    if update_data.receipt_date is not None:
        invoice.receipt_date = update_data.receipt_date
    
    db.commit()
    db.refresh(invoice)
    
    # 請求書データを取得して返す（JOINでリレーション情報も含める）
    sales_person = db.query(SalesPerson).filter(SalesPerson.sales_person_id == invoice.sales_person_id).first()
    discount_rate = db.query(DiscountRate).filter(DiscountRate.discount_rate_id == invoice.discount_rate_id).first()
    details = db.query(SalesInvoiceDetail).filter(SalesInvoiceDetail.sales_invoice_id == invoice.sales_invoice_id).all()
    
    # Calculate discount rate value
    if discount_rate:
        raw_rate = float(discount_rate.rate)
        # If rate >= 1, it's stored as percentage (10 = 10%), convert to decimal
        discount_rate_value = raw_rate / 100 if raw_rate >= 1 else raw_rate
    else:
        discount_rate_value = 0.0
    
    return {
        "id": invoice.sales_invoice_id,
        "invoice_number": "[COMPANY_REGISTRATION_NUMBER]",
        "sales_person_id": invoice.sales_person_id,
        "sales_person_name": sales_person.name if sales_person else None,
        "tax_rate_id": invoice.tax_rate_id,
        "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
        "receipt_date": invoice.receipt_date.isoformat() if invoice.receipt_date else None,
        "discount_rate_id": invoice.discount_rate_id,
        "discount_rate": discount_rate_value,
        "quota_subtotal": invoice.quota_subtotal,
        "quota_discount_amount": invoice.quota_discount_amount,
        "quota_total": invoice.quota_total,
        "non_quota_subtotal": invoice.non_quota_subtotal,
        "non_quota_discount_amount": invoice.non_quota_discount_amount,
        "non_quota_total": invoice.non_quota_total,
        "non_discountable_amount": invoice.non_discountable_amount,
        "total_amount_ex_tax": invoice.total_amount_ex_tax,
        "tax_amount": invoice.tax_amount,
        "total_amount_inc_tax": invoice.total_amount_inc_tax,
        "note": invoice.note,
        "details": [
            {
                "id": detail.sales_invoice_detail_id,
                "product_id": detail.product_id,
                "product_name": db.query(Product).filter(Product.product_id == detail.product_id).first().name,
                "total_quantity": detail.total_quantity,
                "unit_price": detail.unit_price,
                "amount": detail.amount
            }
            for detail in details
        ]
    }


@router.patch("/{invoice_id}/discount-rate")
async def update_invoice_discount_rate(
    invoice_id: str,
    request: DiscountRateUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update discount rate of an existing invoice and recalculate amounts
    
    This is typically used to change 0% invoices to 10%.
    """
    # Get invoice
    invoice = db.query(SalesInvoice).filter(
        SalesInvoice.sales_invoice_id == invoice_id,
        SalesInvoice.deleted_flag == False
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get new discount rate
    discount_rate = db.query(DiscountRate).filter(
        DiscountRate.discount_rate_id == request.discount_rate_id,
        DiscountRate.sales_person_flag == True,
        DiscountRate.deleted_flag == False
    ).first()
    if not discount_rate:
        raise HTTPException(status_code=404, detail="Discount rate not found")
    
    # Recalculate with new discount rate
    discount_rate_value = float(discount_rate.rate)
    if discount_rate_value >= 1:
        discount_rate_value = discount_rate_value / 100
    quota_discount_amount = int(invoice.quota_subtotal * discount_rate_value)
    non_quota_discount_amount = int(invoice.non_quota_subtotal * discount_rate_value)
    
    quota_total = invoice.quota_subtotal - quota_discount_amount
    non_quota_total = invoice.non_quota_subtotal - non_quota_discount_amount
    
    total_amount_ex_tax = quota_total + non_quota_total
    
    # Get tax rate
    tax_rate = db.query(TaxRate).filter(
        TaxRate.is_active == True
    ).order_by(TaxRate.effective_date.desc()).first()
    tax_rate_value = float(tax_rate.rate)
    if tax_rate_value >= 1:
        tax_rate_value = tax_rate_value / 100
    tax_amount = int(total_amount_ex_tax * tax_rate_value)
    
    total_amount_inc_tax = total_amount_ex_tax + tax_amount
    
    # Update invoice
    invoice.discount_rate_id = discount_rate.discount_rate_id
    invoice.quota_discount_amount = quota_discount_amount
    invoice.non_quota_discount_amount = non_quota_discount_amount
    invoice.quota_total = quota_total
    invoice.non_quota_total = non_quota_total
    invoice.total_amount_ex_tax = total_amount_ex_tax
    invoice.tax_amount = tax_amount
    invoice.total_amount_inc_tax = total_amount_inc_tax
    
    db.commit()
    db.refresh(invoice)
    
    return {
        "success": True,
        "message": "Discount rate updated successfully",
        "invoice_id": invoice.sales_invoice_id,
        "old_rate": float(db.query(DiscountRate).filter(DiscountRate.discount_rate_id == invoice.discount_rate_id).first().rate),
        "new_rate": discount_rate_value,
        "new_total_amount_inc_tax": total_amount_inc_tax
    }


@router.get("", response_model=List[InvoiceResponse])
async def get_sales_invoices(
    sales_person_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get sales invoices list with optimized queries (prevents N+1 problem)"""
    query = db.query(SalesInvoice)\
        .options(
            joinedload(SalesInvoice.details).joinedload(SalesInvoiceDetail.product),
            joinedload(SalesInvoice.sales_person),
            joinedload(SalesInvoice.discount_rate)
        )\
        .filter(SalesInvoice.deleted_flag == False)
    
    if sales_person_id:
        query = query.filter(SalesInvoice.sales_person_id == sales_person_id)
    
    invoices = query.order_by(SalesInvoice.created_at.desc()).all()
    
    result = []
    for invoice in invoices:
        # Calculate discount rate value
        if invoice.discount_rate:
            raw_rate = float(invoice.discount_rate.rate)
            # If rate >= 1, it's stored as percentage (10 = 10%), convert to decimal
            discount_rate_value = raw_rate / 100 if raw_rate >= 1 else raw_rate
        else:
            # Fallback: discount_rate not found, default to 0
            discount_rate_value = 0.0
        
        print(f"[DEBUG API] Invoice {invoice.sales_invoice_id}: discount_rate_id={invoice.discount_rate_id}, raw_rate={raw_rate if invoice.discount_rate else 'N/A'}, discount_rate_value={discount_rate_value}")
        
        detail_responses = []
        for detail in invoice.details:
            detail_responses.append(InvoiceDetailResponse(
                id=str(detail.sales_invoice_detail_id),
                product_id=detail.product_id,
                product_name=detail.product.name if detail.product else "",
                total_quantity=detail.total_quantity,
                unit_price=detail.unit_price,
                amount=detail.amount
            ))
        
        result.append(InvoiceResponse(
            id=str(invoice.sales_invoice_id),
            sales_person_id=invoice.sales_person_id,
            sales_person_name=invoice.sales_person.name if invoice.sales_person else "",
            invoice_number="[COMPANY_REGISTRATION_NUMBER]",
            tax_rate_id=invoice.tax_rate_id,
            invoice_date=invoice.invoice_date,
            receipt_date=invoice.receipt_date,
            discount_rate_id=invoice.discount_rate_id,
            discount_rate=discount_rate_value,
            note=invoice.note,
            non_discountable_amount=invoice.non_discountable_amount or 0,
            quota_subtotal=invoice.quota_subtotal,
            quota_discount_amount=invoice.quota_discount_amount,
            quota_total=invoice.quota_total,
            non_quota_subtotal=invoice.non_quota_subtotal,
            non_quota_discount_amount=invoice.non_quota_discount_amount,
            non_quota_total=invoice.non_quota_total,
            total_amount_ex_tax=invoice.total_amount_ex_tax,
            tax_amount=invoice.tax_amount,
            total_amount_inc_tax=invoice.total_amount_inc_tax,
            details=detail_responses
        ))
    
    return result


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_sales_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get sales invoice detail"""
    invoice = db.query(SalesInvoice).filter(
        SalesInvoice.sales_invoice_id == invoice_id,
        SalesInvoice.deleted_flag == False
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    details = db.query(SalesInvoiceDetail).filter(
        SalesInvoiceDetail.sales_invoice_id == invoice.sales_invoice_id
    ).all()
    
    # Get discount rate
    discount_rate = db.query(DiscountRate).filter(
        DiscountRate.discount_rate_id == invoice.discount_rate_id
    ).first()
    
    # Calculate discount rate value
    if discount_rate:
        raw_rate = float(discount_rate.rate)
        # If rate >= 1, it's stored as percentage (10 = 10%), convert to decimal
        discount_rate_value = raw_rate / 100 if raw_rate >= 1 else raw_rate
    else:
        discount_rate_value = 0.0
    
    # Get sales person
    sales_person = db.query(SalesPerson).filter(
        SalesPerson.sales_person_id == invoice.sales_person_id
    ).first()
    
    detail_responses = []
    for detail in details:
        product = db.query(Product).filter(Product.product_id == detail.product_id).first()
        detail_responses.append(InvoiceDetailResponse(
            id=detail.sales_invoice_detail_id,
            product_id=detail.product_id,
            product_name=product.name if product else "",
            total_quantity=detail.total_quantity,
            unit_price=detail.unit_price,
            amount=detail.amount
        ))
    
    return InvoiceResponse(
        id=invoice.sales_invoice_id,
        sales_person_id=invoice.sales_person_id,
        sales_person_name=sales_person.name if sales_person else "",
        invoice_number="[COMPANY_REGISTRATION_NUMBER]",
        tax_rate_id=invoice.tax_rate_id,
        invoice_date=invoice.invoice_date,
        receipt_date=invoice.receipt_date,
        discount_rate_id=invoice.discount_rate_id,
        discount_rate=discount_rate_value,
        note=invoice.note,
        non_discountable_amount=invoice.non_discountable_amount or 0,
        quota_subtotal=invoice.quota_subtotal,
        quota_discount_amount=invoice.quota_discount_amount,
        quota_total=invoice.quota_total,
        non_quota_subtotal=invoice.non_quota_subtotal,
        non_quota_discount_amount=invoice.non_quota_discount_amount,
        non_quota_total=invoice.non_quota_total,
        total_amount_ex_tax=invoice.total_amount_ex_tax,
        tax_amount=invoice.tax_amount,
        total_amount_inc_tax=invoice.total_amount_inc_tax,
        details=detail_responses
    )


@router.delete("/{invoice_id}")
async def delete_sales_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete sales invoice (soft delete)"""
    invoice = db.query(SalesInvoice).filter(
        SalesInvoice.sales_invoice_id == invoice_id,
        SalesInvoice.deleted_flag == False
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # 論理削除: deleted_flagをTrueに設定
    invoice.deleted_flag = True
    
    # 明細も論理削除
    db.query(SalesInvoiceDetail).filter(
        SalesInvoiceDetail.sales_invoice_id == invoice_id
    ).update({SalesInvoiceDetail.deleted_flag: True}, synchronize_session=False)
    
    db.commit()
    
    return {
        "success": True,
        "message": "Invoice deleted successfully",
        "invoice_id": invoice_id
    }


@router.get("/{invoice_id}/pdf")
async def generate_invoice_pdf(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate sales invoice PDF"""
    invoice = db.query(SalesInvoice).filter(
        SalesInvoice.sales_invoice_id == invoice_id,
        SalesInvoice.deleted_flag == False
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    pdf_buffer = generate_sales_invoice_pdf(invoice, db)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoice_{invoice.sales_invoice_id}.pdf"
        }
    )


@router.get("/{invoice_id}/receipt-pdf")
def get_sales_receipt_pdf(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate sales receipt PDF"""
    invoice = db.query(SalesInvoice).filter(
        SalesInvoice.sales_invoice_id == invoice_id,
        SalesInvoice.deleted_flag == False
    ).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    pdf_buffer = generate_sales_receipt_pdf(invoice, db)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=receipt_{invoice.sales_invoice_id}.pdf"
        }
    )
