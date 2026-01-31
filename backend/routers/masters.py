from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import SalesPerson, Product, Contractor, DiscountRate
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
    sales_persons = db.query(SalesPerson).all()
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
    sales_person = db.query(SalesPerson).filter(SalesPerson.id == sales_person_id).first()
    if sales_person is None:
        raise HTTPException(status_code=404, detail="Sales person not found")
    return sales_person

@router.put("/sales-persons/{sales_person_id}", response_model=SalesPersonResponse)
async def update_sales_person(sales_person_id: int, sales_person: SalesPersonCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_sales_person = db.query(SalesPerson).filter(SalesPerson.id == sales_person_id).first()
    if db_sales_person is None:
        raise HTTPException(status_code=404, detail="Sales person not found")
    for key, value in sales_person.dict().items():
        setattr(db_sales_person, key, value)
    db.commit()
    db.refresh(db_sales_person)
    return db_sales_person

@router.delete("/sales-persons/{sales_person_id}")
async def delete_sales_person(sales_person_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_sales_person = db.query(SalesPerson).filter(SalesPerson.id == sales_person_id).first()
    if db_sales_person is None:
        raise HTTPException(status_code=404, detail="Sales person not found")
    db.delete(db_sales_person)
    db.commit()
    return {"message": "Sales person deleted"}

# Product endpoints
@router.get("/products", response_model=List[ProductResponse])
async def get_products(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    products = db.query(Product).all()
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
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in product.dict().items():
        setattr(db_product, key, value)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/products/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted"}

# Contractor endpoints
@router.get("/contractors", response_model=List[ContractorResponse])
async def get_contractors(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    contractors = db.query(Contractor).all()
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
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if contractor is None:
        raise HTTPException(status_code=404, detail="Contractor not found")
    return contractor

@router.put("/contractors/{contractor_id}", response_model=ContractorResponse)
async def update_contractor(contractor_id: int, contractor: ContractorCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if db_contractor is None:
        raise HTTPException(status_code=404, detail="Contractor not found")
    for key, value in contractor.dict().items():
        setattr(db_contractor, key, value)
    db.commit()
    db.refresh(db_contractor)
    return db_contractor

@router.delete("/contractors/{contractor_id}")
async def delete_contractor(contractor_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    if db_contractor is None:
        raise HTTPException(status_code=404, detail="Contractor not found")
    db.delete(db_contractor)
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
        
    @classmethod
    def model_validate(cls, obj, **kwargs):
        # Explicitly convert Decimal to float to avoid any precision issues
        if hasattr(obj, 'rate'):
            rate_value = float(obj.rate) if obj.rate is not None else 0.0
            return cls(
                id=obj.id,
                rate=rate_value,
                threshold_amount=obj.threshold_amount,
                customer_flag=obj.customer_flag
            )
        return super().model_validate(obj, **kwargs)

@router.get("/discount-rates", response_model=List[DiscountRateResponse])
async def get_discount_rates(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    rates = db.query(DiscountRate).filter(DiscountRate.deleted_flag == False).all()
    print(f"[DEBUG] Returning {len(rates)} discount rates")
    for rate in rates:
        print(f"[DEBUG]   ID={rate.id}, rate={rate.rate} ({type(rate.rate).__name__}), threshold={rate.threshold_amount}")
    return rates
