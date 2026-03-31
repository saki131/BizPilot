import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth_router, masters_router, delivery_notes_router, admin_router
from routers.sales_invoices import router as sales_invoices_router
from routers.contractor_invoices import router as contractor_invoices_router
from routers.sales_stats import router as sales_stats_router
from routers.customer_orders import router as customer_orders_router

app = FastAPI(title="Invoice Management API", version="1.0.0")

# CORS設定
allowed_origins = [
    "http://localhost:3000",
    "http://172.16.0.71:3000", 
    "https://biz-pilot.vercel.app",  # Vercel本番環境（旧）
    "https://biz-pilot-mu.vercel.app"  # Vercel本番環境（新）
]

# Vercelプレビューデプロイメント用の動的CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Vercelの全プレビュー/本番URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(masters_router, prefix="/api")
app.include_router(delivery_notes_router, prefix="/api")
app.include_router(sales_invoices_router, prefix="/api/sales-invoices", tags=["sales-invoices"])
app.include_router(contractor_invoices_router, prefix="/api/contractor-invoices", tags=["contractor-invoices"])
app.include_router(sales_stats_router, prefix="/api/sales-stats", tags=["sales-stats"])
app.include_router(customer_orders_router, prefix="/api/customer-orders", tags=["customer-orders"])
app.include_router(admin_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Invoice Management API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}