import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import auth_router, masters_router, delivery_notes_router
from routers.sales_invoices import router as sales_invoices_router

app = FastAPI(title="Invoice Management API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://172.16.0.71:3000", 
        "https://biz-pilot.vercel.app"  # Vercel本番環境
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(masters_router, prefix="/api")
app.include_router(delivery_notes_router, prefix="/api")
app.include_router(sales_invoices_router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "Invoice Management API"}

@app.get("/health")
async def health():
    return {"status": "healthy"}