from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import SalesPerson, Product, Contractor, DiscountRate, TaxRate
from dependencies import get_current_user
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/masters", tags=["masters"])

# Pydantic schemas
class SalesPersonBase(BaseModel):
    name: str

class SalesPersonCreate(SalesPersonBase):
    pass

class SalesPersonResponse(SalesPersonBase):
    id: int

    class Config:
        from_attributes = True

class ProductBase(BaseModel):
    name: str
    price: int

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int

    class Config:
        from_attributes = True

class ContractorBase(BaseModel):
    name: str

class ContractorCreate(ContractorBase):
    pass

class ContractorResponse(ContractorBase):
    id: int

    class Config:
        from_attributes = True

# SalesPerson endpoints
@router.get("/sales-persons", response_model=List[SalesPersonResponse])
async def get_sales_persons(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # 削除フラグがFalseの販売員のみ取得、表示順でソート
    sales_persons = db.query(SalesPerson).filter(SalesPerson.deleted_flag == False).order_by(SalesPerson.display_order).all()
    return sales_persons

@router.post("/sales-persons", response_model=SalesPersonResponse)
async def create_sales_person(sales_person: SalesPersonCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_sales_person = SalesPerson(**sales_person.dict())
    db.add(db_sales_person)
    db.commit()
    db.refresh(db_sales_person)
    return db_sales_person

@router.get("/sales-persons/{sales_person_id}", response_model=SalesPersonResponse)
async def get_sales_person(sales_person_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    sales_person = db.query(SalesPerson).filter(
        SalesPerson.id == sales_person_id,
        SalesPerson.deleted_flag == False
    ).first()
    if sales_person is None:
        raise HTTPException(status_code=404, detail="Sales person not found")
    return sales_person

@router.put("/sales-persons/{sales_person_id}", response_model=SalesPersonResponse)
async def update_sales_person(sales_person_id: int, sales_person: SalesPersonCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_sales_person = db.query(SalesPerson).filter(
        SalesPerson.id == sales_person_id,
        SalesPerson.deleted_flag == False
    ).first()
    if db_sales_person is None:
        raise HTTPException(status_code=404, detail="Sales person not found")
    for key, value in sales_person.dict().items():
        setattr(db_sales_person, key, value)
    db.commit()
    db.refresh(db_sales_person)
    return db_sales_person

@router.delete("/sales-persons/{sales_person_id}")
async def delete_sales_person(sales_person_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_sales_person = db.query(SalesPerson).filter(
        SalesPerson.id == sales_person_id,
        SalesPerson.deleted_flag == False
    ).first()
    if db_sales_person is None:
        raise HTTPException(status_code=404, detail="Sales person not found")
    # 論理削除
    db_sales_person.deleted_flag = True
    db.commit()
    return {"message": "Sales person deleted"}

# Product endpoints
@router.get("/products", response_model=List[ProductResponse])
async def get_products(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # 削除フラグがFalseの商品のみ取得、表示順でソート
    products = db.query(Product).filter(Product.deleted_flag == False).order_by(Product.display_order).all()
    return products

@router.post("/products", response_model=ProductResponse)
async def create_product(product: ProductCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.deleted_flag == False
    ).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_product = db.query(Product).filter(
        Product.id == product_id,
        Product.deleted_flag == False
    ).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product.dict().items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/products/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_product = db.query(Product).filter(
        Product.id == product_id,
        Product.deleted_flag == False
    ).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    # 論理削除
    db_product.deleted_flag = True
    db.commit()
    return {"message": "Product deleted"}

# Contractor endpoints
@router.get("/contractors", response_model=List[ContractorResponse])
async def get_contractors(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # 削除フラグがFalseの委託先のみ取得、表示順でソート
    contractors = db.query(Contractor).filter(Contractor.deleted_flag == False).order_by(Contractor.display_order).all()
    return contractors

@router.post("/contractors", response_model=ContractorResponse)
async def create_contractor(contractor: ContractorCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_contractor = Contractor(**contractor.dict())
    db.add(db_contractor)
    db.commit()
    db.refresh(db_contractor)
    return db_contractor

@router.get("/contractors/{contractor_id}", response_model=ContractorResponse)
async def get_contractor(contractor_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    contractor = db.query(Contractor).filter(
        Contractor.id == contractor_id,
        Contractor.deleted_flag == False
    ).first()
    if contractor is None:
        raise HTTPException(status_code=404, detail="Contractor not found")
    return contractor

@router.put("/contractors/{contractor_id}", response_model=ContractorResponse)
async def update_contractor(contractor_id: int, contractor: ContractorCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_contractor = db.query(Contractor).filter(
        Contractor.id == contractor_id,
        Contractor.deleted_flag == False
    ).first()
    if db_contractor is None:
        raise HTTPException(status_code=404, detail="Contractor not found")
    for key, value in contractor.dict().items():
        setattr(db_contractor, key, value)
    db.commit()
    db.refresh(db_contractor)
    return db_contractor

@router.delete("/contractors/{contractor_id}")
async def delete_contractor(contractor_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_contractor = db.query(Contractor).filter(
        Contractor.id == contractor_id,
        Contractor.deleted_flag == False
    ).first()
    if db_contractor is None:
        raise HTTPException(status_code=404, detail="Contractor not found")
    # 論理削除
    db_contractor.deleted_flag = True
    db.commit()
    return {"message": "Contractor deleted"}

# Discount Rate endpoints
class DiscountRateResponse(BaseModel):
    id: int
    rate: float
    threshold_amount: int
    customer_flag: bool

    class Config:
        from_attributes = True

@router.get("/discount-rates", response_model=List[DiscountRateResponse])
async def get_discount_rates(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    rates = db.query(DiscountRate).filter(DiscountRate.deleted_flag == False).all()
    print(f"[DEBUG] Returning {len(rates)} discount rates")
    
    # Convert rates: if stored as percentage (>=1), convert to decimal
    result = []
    for rate in rates:
        raw_rate = float(rate.rate)
        # If rate >= 1, it's stored as percentage (10 = 10%), convert to decimal
        converted_rate = raw_rate / 100 if raw_rate >= 1 else raw_rate
        print(f"[DEBUG]   ID={rate.id}, raw_rate={raw_rate}, converted_rate={converted_rate}")
        
        result.append(DiscountRateResponse(
            id=rate.id,
            rate=converted_rate,
            threshold_amount=rate.threshold_amount,
            customer_flag=rate.customer_flag
        ))
    
    return result

# Tax Rate endpoints
class TaxRateResponse(BaseModel):
    id: int
    rate: float
    display_name: str

    class Config:
        from_attributes = True

@router.get("/tax-rates", response_model=List[TaxRateResponse])
async def get_tax_rates(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    rates = db.query(TaxRate).filter(TaxRate.deleted_flag == False).all()
    
    # Convert rates: if stored as percentage (>=1), convert to decimal
    result = []
    for rate in rates:
        raw_rate = float(rate.rate)
        # If rate >= 1, it's stored as percentage (10 = 10%), convert to decimal
        converted_rate = raw_rate / 100 if raw_rate >= 1 else raw_rate
        
        result.append(TaxRateResponse(
            id=rate.id,
            rate=converted_rate,
            display_name=rate.display_name
        ))
    
    return result
