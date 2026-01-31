# -*- coding: utf-8 -*-
"""販売員請求書API"""
from datetime import date, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
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
from pdf_generator import generate_sales_invoice_pdf

router = APIRouter()


class InvoiceUpdateRequest(BaseModel):
    discount_rate_id: Optional[int] = None
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
        DiscountRate.customer_flag == True,
        DiscountRate.deleted_flag == False
    ).order_by(DiscountRate.threshold_amount.desc()).all()
    
    # Find the highest applicable rate
    for rate in discount_rates:
        if total_amount >= rate.threshold_amount and rate.rate > 0:
            return rate
    
    # If no rate >= 20% applies, return 0% rate
    zero_rate = db.query(DiscountRate).filter(
        DiscountRate.customer_flag == True,
        DiscountRate.rate == 0,
        DiscountRate.deleted_flag == False
    ).first()
    
    return zero_rate


class InvoiceGenerateRequest(BaseModel):
    """請求書生成リクエスト"""
    sales_person_id: int
    start_date: date
    end_date: date
    discount_rate_id: int


class BulkInvoiceGenerateRequest(BaseModel):
    """一括請求書生成リクエスト"""
    closing_date: date  # 締め日（必須）
    sales_person_ids: Optional[List[int]] = None  # None=全販売員、指定=特定販売員のみ


class DiscountRateUpdateRequest(BaseModel):
    """割引率変更リクエスト"""
    discount_rate_id: int


class InvoiceDetailResponse(BaseModel):
    """請求書明細レスポンス"""
    id: int
    product_id: int
    product_name: str
    total_quantity: int
    unit_price: int
    amount: int


class InvoiceResponse(BaseModel):
    """請求書レスポンス"""
    id: int
    sales_person_id: int
    sales_person_name: str
    invoice_number: str
    start_date: date
    end_date: date
    invoice_date: Optional[date] = None
    receipt_date: Optional[date] = None
    discount_rate_id: int
    discount_rate: float
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
    start_date: date,
    end_date: date,
    db: Session
) -> Optional[InvoiceResponse]:
    """Generate invoice for a specific sales person"""
    
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
    
    delivery_note_ids = [dn.id for dn in delivery_notes]
    
    # Aggregate by product
    aggregated_data = db.query(
        DeliveryNoteDetail.product_id,
        Product.quota_target_flag,
        func.sum(DeliveryNoteDetail.quantity).label('total_quantity'),
        DeliveryNoteDetail.unit_price
    ).join(
        Product, DeliveryNoteDetail.product_id == Product.id
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
    quota_discount_amount = int(quota_subtotal * discount_rate_value)
    non_quota_discount_amount = int(non_quota_subtotal * discount_rate_value)
    
    quota_total = quota_subtotal - quota_discount_amount
    non_quota_total = non_quota_subtotal - non_quota_discount_amount
    
    total_amount_ex_tax = quota_total + non_quota_total
    
    # Calculate tax (floor rounding)
    tax_amount = int(quota_total * float(tax_rate.rate))
    
    total_amount_inc_tax = total_amount_ex_tax + tax_amount
    
    # Calculate invoice_date and receipt_date
    # 請求日 = 締め日と同じ
    invoice_date = end_date
    # 領収日 = 請求日当月の25日
    receipt_date = end_date.replace(day=25)
    
    # Check if invoice already exists for this sales person and period
    existing_invoice = db.query(SalesInvoice).filter(
        SalesInvoice.sales_person_id == sales_person_id,
        SalesInvoice.start_date == start_date,
        SalesInvoice.end_date == end_date
    ).first()
    
    if existing_invoice:
        # Update existing invoice
        existing_invoice.discount_rate_id = discount_rate.id
        existing_invoice.invoice_date = invoice_date
        existing_invoice.receipt_date = receipt_date
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
            SalesInvoiceDetail.sales_invoice_id == existing_invoice.id
        ).delete()
        
        invoice = existing_invoice
    else:
        # Create new invoice record
        invoice = SalesInvoice(
            sales_person_id=sales_person_id,
            invoice_number="T5810180900550",
            start_date=start_date,
            end_date=end_date,
            invoice_date=invoice_date,
            receipt_date=receipt_date,
            discount_rate_id=discount_rate.id,
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
            sales_invoice_id=invoice.id,
            **detail_data
        )
        db.add(detail)
        db.flush()
        
        product = db.query(Product).filter(Product.id == detail.product_id).first()
        detail_responses.append(InvoiceDetailResponse(
            id=detail.id,
            product_id=detail.product_id,
            product_name=product.name if product else "",
            total_quantity=detail.total_quantity,
            unit_price=detail.unit_price,
            amount=detail.amount
        ))
    
    db.commit()
    
    # Get sales person name
    sales_person = db.query(SalesPerson).filter(
        SalesPerson.id == sales_person_id
    ).first()
    
    return InvoiceResponse(
        id=invoice.id,
        sales_person_id=invoice.sales_person_id,
        sales_person_name=sales_person.name if sales_person else "",
        invoice_number=invoice.invoice_number,
        start_date=invoice.start_date,
        end_date=invoice.end_date,
        invoice_date=invoice.invoice_date,
        receipt_date=invoice.receipt_date,
        discount_rate_id=invoice.discount_rate_id,
        discount_rate=discount_rate_value,
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


@router.post("/sales-invoices/bulk-generate")
async def bulk_generate_sales_invoices(
    request: BulkInvoiceGenerateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Bulk generate sales invoices
    
    Generate invoices for all or selected sales persons for a specific closing date.
    Period is automatically calculated: (previous month 21st) to (closing date)
    """
    # Calculate start date (21st of previous month)
    if request.closing_date.day >= 21:
        # If closing date is >= 21st, start from same month 21st
        start_date = request.closing_date.replace(day=21)
    else:
        # If closing date is < 21st, start from previous month 21st
        if request.closing_date.month == 1:
            start_date = request.closing_date.replace(year=request.closing_date.year - 1, month=12, day=21)
        else:
            prev_month = request.closing_date.month - 1
            start_date = request.closing_date.replace(month=prev_month, day=21)
    
    # Get target sales persons
    if request.sales_person_ids:
        sales_persons = db.query(SalesPerson).filter(
            SalesPerson.id.in_(request.sales_person_ids),
            SalesPerson.deleted_flag == False
        ).all()
    else:
        sales_persons = db.query(SalesPerson).filter(
            SalesPerson.deleted_flag == False
        ).all()
    
    if not sales_persons:
        raise HTTPException(status_code=404, detail="No sales persons found")
    
    # Generate invoices
    generated_invoices = []
    skipped_persons = []
    
    for sales_person in sales_persons:
        invoice = generate_invoice_for_sales_person(
            sales_person.id,
            start_date,
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
            "end_date": request.closing_date.isoformat()
        }
    }


@router.patch("/sales-invoices/{invoice_id}")
async def update_invoice_fields(
    invoice_id: int,
    update_data: InvoiceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update invoice fields like discount_rate_id and note"""
    invoice = db.query(SalesInvoice).filter(SalesInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Update fields if provided
    if update_data.discount_rate_id is not None:
        # 割引率を変更する場合は、金額も再計算
        discount_rate = db.query(DiscountRate).filter(DiscountRate.id == update_data.discount_rate_id).first()
        if not discount_rate:
            raise HTTPException(status_code=404, detail="Discount rate not found")
        
        invoice.discount_rate_id = update_data.discount_rate_id
        
        # 割引額と合計を再計算
        invoice.quota_discount_amount = int(invoice.quota_subtotal * discount_rate.rate / 100)
        invoice.quota_total = invoice.quota_subtotal - invoice.quota_discount_amount
        invoice.non_quota_discount_amount = int(invoice.non_quota_subtotal * discount_rate.rate / 100)
        invoice.non_quota_total = invoice.non_quota_subtotal - invoice.non_quota_discount_amount
        invoice.total_amount_ex_tax = invoice.quota_total + invoice.non_quota_total + (invoice.non_discountable_amount or 0)
        
        # 消費税を計算
        tax_rate = db.query(TaxRate).filter(TaxRate.deleted_flag == False).first()
        if tax_rate:
            invoice.tax_amount = int(invoice.total_amount_ex_tax * tax_rate.rate / 100)
        invoice.total_amount_inc_tax = invoice.total_amount_ex_tax + invoice.tax_amount
    
    if update_data.note is not None:
        invoice.note = update_data.note
    
    db.commit()
    db.refresh(invoice)
    
    # 請求書データを取得して返す（JOINでリレーション情報も含める）
    sales_person = db.query(SalesPerson).filter(SalesPerson.id == invoice.sales_person_id).first()
    discount_rate = db.query(DiscountRate).filter(DiscountRate.id == invoice.discount_rate_id).first()
    details = db.query(SalesInvoiceDetail).filter(SalesInvoiceDetail.sales_invoice_id == invoice.id).all()
    
    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "sales_person_id": invoice.sales_person_id,
        "sales_person_name": sales_person.name if sales_person else None,
        "start_date": invoice.start_date.isoformat() if invoice.start_date else None,
        "end_date": invoice.end_date.isoformat() if invoice.end_date else None,
        "invoice_date": invoice.invoice_date.isoformat() if invoice.invoice_date else None,
        "receipt_date": invoice.receipt_date.isoformat() if invoice.receipt_date else None,
        "discount_rate_id": invoice.discount_rate_id,
        "discount_rate": discount_rate.rate if discount_rate else 0,
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
                "id": detail.id,
                "product_id": detail.product_id,
                "product_name": db.query(Product).filter(Product.id == detail.product_id).first().name,
                "total_quantity": detail.total_quantity,
                "unit_price": detail.unit_price,
                "amount": detail.amount
            }
            for detail in details
        ]
    }


@router.patch("/sales-invoices/{invoice_id}/discount-rate")
async def update_invoice_discount_rate(
    invoice_id: int,
    request: DiscountRateUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update discount rate of an existing invoice and recalculate amounts
    
    This is typically used to change 0% invoices to 10%.
    """
    # Get invoice
    invoice = db.query(SalesInvoice).filter(SalesInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get new discount rate
    discount_rate = db.query(DiscountRate).filter(
        DiscountRate.id == request.discount_rate_id,
        DiscountRate.customer_flag == True,
        DiscountRate.deleted_flag == False
    ).first()
    if not discount_rate:
        raise HTTPException(status_code=404, detail="Discount rate not found")
    
    # Recalculate with new discount rate
    discount_rate_value = float(discount_rate.rate)
    quota_discount_amount = int(invoice.quota_subtotal * discount_rate_value)
    non_quota_discount_amount = int(invoice.non_quota_subtotal * discount_rate_value)
    
    quota_total = invoice.quota_subtotal - quota_discount_amount
    non_quota_total = invoice.non_quota_subtotal - non_quota_discount_amount
    
    total_amount_ex_tax = quota_total + non_quota_total
    
    # Get tax rate
    tax_rate = db.query(TaxRate).filter(
        TaxRate.is_active == True
    ).order_by(TaxRate.effective_date.desc()).first()
    tax_amount = int(quota_total * float(tax_rate.rate))
    
    total_amount_inc_tax = total_amount_ex_tax + tax_amount
    
    # Update invoice
    invoice.discount_rate_id = discount_rate.id
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
        "invoice_id": invoice.id,
        "old_rate": float(db.query(DiscountRate).filter(DiscountRate.id == invoice.discount_rate_id).first().rate),
        "new_rate": discount_rate_value,
        "new_total_amount_inc_tax": total_amount_inc_tax
    }


@router.get("/sales-invoices", response_model=List[InvoiceResponse])
async def get_sales_invoices(
    sales_person_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get sales invoices list"""
    query = db.query(SalesInvoice)
    
    if sales_person_id:
        query = query.filter(SalesInvoice.sales_person_id == sales_person_id)
    
    invoices = query.order_by(SalesInvoice.created_at.desc()).all()
    
    result = []
    for invoice in invoices:
        details = db.query(SalesInvoiceDetail).filter(
            SalesInvoiceDetail.sales_invoice_id == invoice.id
        ).all()
        
        # Get discount rate
        discount_rate = db.query(DiscountRate).filter(
            DiscountRate.id == invoice.discount_rate_id
        ).first()
        
        # Get sales person
        sales_person = db.query(SalesPerson).filter(
            SalesPerson.id == invoice.sales_person_id
        ).first()
        
        detail_responses = []
        for detail in details:
            product = db.query(Product).filter(Product.id == detail.product_id).first()
            detail_responses.append(InvoiceDetailResponse(
                id=detail.id,
                product_id=detail.product_id,
                product_name=product.name if product else "",
                total_quantity=detail.total_quantity,
                unit_price=detail.unit_price,
                amount=detail.amount
            ))
        
        discount_rate_value = float(discount_rate.rate) if discount_rate else 0.0
        print(f"[DEBUG API] Invoice {invoice.id}: discount_rate.rate={discount_rate.rate if discount_rate else None}, discount_rate_value={discount_rate_value}")
        
        result.append(InvoiceResponse(
            id=invoice.id,
            sales_person_id=invoice.sales_person_id,
            sales_person_name=sales_person.name if sales_person else "",
            invoice_number=invoice.invoice_number,
            start_date=invoice.start_date,
            end_date=invoice.end_date,
            invoice_date=invoice.invoice_date,
            receipt_date=invoice.receipt_date,
            discount_rate_id=invoice.discount_rate_id,
            discount_rate=discount_rate_value,
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


@router.get("/sales-invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_sales_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get sales invoice detail"""
    invoice = db.query(SalesInvoice).filter(SalesInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    details = db.query(SalesInvoiceDetail).filter(
        SalesInvoiceDetail.sales_invoice_id == invoice.id
    ).all()
    
    # Get discount rate
    discount_rate = db.query(DiscountRate).filter(
        DiscountRate.id == invoice.discount_rate_id
    ).first()
    
    # Get sales person
    sales_person = db.query(SalesPerson).filter(
        SalesPerson.id == invoice.sales_person_id
    ).first()
    
    detail_responses = []
    for detail in details:
        product = db.query(Product).filter(Product.id == detail.product_id).first()
        detail_responses.append(InvoiceDetailResponse(
            id=detail.id,
            product_id=detail.product_id,
            product_name=product.name if product else "",
            total_quantity=detail.total_quantity,
            unit_price=detail.unit_price,
            amount=detail.amount
        ))
    
    return InvoiceResponse(
        id=invoice.id,
        sales_person_id=invoice.sales_person_id,
        sales_person_name=sales_person.name if sales_person else "",
        invoice_number=invoice.invoice_number,
        start_date=invoice.start_date,
        end_date=invoice.end_date,
        invoice_date=invoice.invoice_date,
        receipt_date=invoice.receipt_date,
        discount_rate_id=invoice.discount_rate_id,
        discount_rate=float(discount_rate.rate) if discount_rate else 0.0,
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


@router.delete("/sales-invoices/{invoice_id}")
async def delete_sales_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete sales invoice"""
    invoice = db.query(SalesInvoice).filter(SalesInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Delete invoice details first (cascade)
    db.query(SalesInvoiceDetail).filter(
        SalesInvoiceDetail.sales_invoice_id == invoice_id
    ).delete()
    
    # Delete invoice
    db.delete(invoice)
    db.commit()
    
    return {
        "success": True,
        "message": "Invoice deleted successfully",
        "invoice_id": invoice_id
    }


@router.get("/sales-invoices/{invoice_id}/pdf")
async def generate_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate sales invoice PDF"""
    invoice = db.query(SalesInvoice).filter(SalesInvoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    pdf_buffer = generate_sales_invoice_pdf(invoice, db)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoice_{invoice.id}.pdf"
        }
    )
