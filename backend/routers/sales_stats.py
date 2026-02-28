# -*- coding: utf-8 -*-
"""売上統計API"""
from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from pydantic import BaseModel

from database import get_db
from models import (
    SalesInvoice,
    SalesInvoiceDetail,
    ContractorInvoice,
    ContractorInvoiceDetail,
    Product,
)
from dependencies import get_current_user

router = APIRouter()


class MonthlyTotalResponse(BaseModel):
    year_month: str               # "YYYY-MM"
    sales_invoice_total: int      # 販売員請求書 税込合計
    contractor_invoice_total: int # 委託先請求書 税込合計
    grand_total: int              # 合計

    class Config:
        from_attributes = True


class MonthlyProductQuantityResponse(BaseModel):
    product_id: int
    product_name: str
    display_order: int
    sales_total_quantity: int      # 販売員請求書明細の数量合計
    contractor_total_quantity: int  # 委託先請求書明細の数量合計
    grand_total_quantity: int

    class Config:
        from_attributes = True


@router.get(
    "/monthly-totals",
    response_model=List[MonthlyTotalResponse],
    summary="月別売上合計取得",
    description="指定した年の月別・請求書種別の税込合計金額を返します。削除済み請求書は除外します。",
)
def get_monthly_totals(
    year: Optional[int] = Query(default=None, description="集計対象年（省略時: 現在年）"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    target_year = year if year else date.today().year

    # 販売員請求書: 月ごとの税込合計
    sales_rows = (
        db.query(
            func.to_char(SalesInvoice.invoice_date, "YYYY-MM").label("year_month"),
            func.coalesce(func.sum(SalesInvoice.total_amount_inc_tax), 0).label("total"),
        )
        .filter(
            SalesInvoice.deleted_flag == False,
            SalesInvoice.invoice_date != None,
            extract("year", SalesInvoice.invoice_date) == target_year,
        )
        .group_by(func.to_char(SalesInvoice.invoice_date, "YYYY-MM"))
        .all()
    )
    sales_map = {r.year_month: int(r.total) for r in sales_rows}

    # 委託先請求書: 月ごとの税込合計
    contractor_rows = (
        db.query(
            func.to_char(ContractorInvoice.invoice_date, "YYYY-MM").label("year_month"),
            func.coalesce(func.sum(ContractorInvoice.total_amount_inc_tax), 0).label("total"),
        )
        .filter(
            ContractorInvoice.deleted_flag == False,
            extract("year", ContractorInvoice.invoice_date) == target_year,
        )
        .group_by(func.to_char(ContractorInvoice.invoice_date, "YYYY-MM"))
        .all()
    )
    contractor_map = {r.year_month: int(r.total) for r in contractor_rows}

    # 両方のキーをマージして月順に並べ替え
    all_months = sorted(set(list(sales_map.keys()) + list(contractor_map.keys())))

    result = []
    for ym in all_months:
        s = sales_map.get(ym, 0)
        c = contractor_map.get(ym, 0)
        result.append(
            MonthlyTotalResponse(
                year_month=ym,
                sales_invoice_total=s,
                contractor_invoice_total=c,
                grand_total=s + c,
            )
        )

    return result


@router.get(
    "/monthly-product-quantities",
    response_model=List[MonthlyProductQuantityResponse],
    summary="月別商品別数量合計取得",
    description="指定した年月の商品ごとの数量合計を返します。合計0の商品は除外します。",
)
def get_monthly_product_quantities(
    year: int = Query(..., description="集計対象年"),
    month: int = Query(..., ge=1, le=12, description="集計対象月（1〜12）"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 販売員請求書明細: 商品ごとの数量合計
    sales_rows = (
        db.query(
            SalesInvoiceDetail.product_id,
            func.coalesce(func.sum(SalesInvoiceDetail.total_quantity), 0).label("qty"),
        )
        .join(SalesInvoice, SalesInvoice.sales_invoice_id == SalesInvoiceDetail.sales_invoice_id)
        .filter(
            SalesInvoice.deleted_flag == False,
            SalesInvoice.invoice_date != None,
            extract("year", SalesInvoice.invoice_date) == year,
            extract("month", SalesInvoice.invoice_date) == month,
        )
        .group_by(SalesInvoiceDetail.product_id)
        .all()
    )
    sales_qty_map = {r.product_id: int(r.qty) for r in sales_rows}

    # 委託先請求書明細: 商品ごとの数量合計
    contractor_rows = (
        db.query(
            ContractorInvoiceDetail.product_id,
            func.coalesce(func.sum(ContractorInvoiceDetail.total_quantity), 0).label("qty"),
        )
        .join(
            ContractorInvoice,
            ContractorInvoice.contractor_invoice_id == ContractorInvoiceDetail.contractor_invoice_id,
        )
        .filter(
            ContractorInvoice.deleted_flag == False,
            extract("year", ContractorInvoice.invoice_date) == year,
            extract("month", ContractorInvoice.invoice_date) == month,
        )
        .group_by(ContractorInvoiceDetail.product_id)
        .all()
    )
    contractor_qty_map = {r.product_id: int(r.qty) for r in contractor_rows}

    # 両方に登場する商品IDを収集
    all_product_ids = set(list(sales_qty_map.keys()) + list(contractor_qty_map.keys()))

    if not all_product_ids:
        return []

    # 商品マスタ取得（display_order順）
    products = (
        db.query(Product)
        .filter(Product.product_id.in_(all_product_ids))
        .order_by(Product.display_order, Product.product_id)
        .all()
    )

    result = []
    for product in products:
        s = sales_qty_map.get(product.product_id, 0)
        c = contractor_qty_map.get(product.product_id, 0)
        total = s + c
        if total == 0:
            continue
        result.append(
            MonthlyProductQuantityResponse(
                product_id=product.product_id,
                product_name=product.name,
                display_order=product.display_order,
                sales_total_quantity=s,
                contractor_total_quantity=c,
                grand_total_quantity=total,
            )
        )

    return result
