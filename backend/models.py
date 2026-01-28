from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, TIMESTAMP, Text, func, ForeignKey, JSON, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class SalesPerson(Base):
    __tablename__ = "sales_persons"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    deleted_flag = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    price = Column(Integer, nullable=False)
    discount_exclusion_flag = Column(Boolean, default=False)
    quota_exclusion_flag = Column(Boolean, default=False)
    quota_target_flag = Column(Boolean, default=False)
    deleted_flag = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Contractor(Base):
    __tablename__ = "contractors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    deleted_flag = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class TaxRate(Base):
    __tablename__ = "tax_rates"

    id = Column(Integer, primary_key=True, index=True)
    rate = Column(DECIMAL(4, 2), nullable=False)
    display_name = Column(String(20), nullable=False)
    deleted_flag = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class DiscountRate(Base):
    __tablename__ = "discount_rates"

    id = Column(Integer, primary_key=True, index=True)
    rate = Column(DECIMAL(4, 2), nullable=False)
    threshold_amount = Column(Integer, default=0)  # 下限額
    customer_flag = Column(Boolean, default=True)
    deleted_flag = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class DeliveryNote(Base):
    __tablename__ = "delivery_notes"

    id = Column(Integer, primary_key=True, index=True)
    sales_person_id = Column(Integer, ForeignKey("sales_persons.id"))
    tax_rate_id = Column(Integer, ForeignKey("tax_rates.id"))
    quota_amount = Column(Integer, default=0)
    non_quota_amount = Column(Integer, default=0)
    tax_amount = Column(Integer, default=0)
    total_amount_ex_tax = Column(Integer, default=0)
    total_amount_inc_tax = Column(Integer, default=0)
    remarks = Column(Text)
    delivery_note_number = Column(String(50), unique=True, nullable=False)
    file_path = Column(String(500))
    delivery_date = Column(TIMESTAMP, nullable=False)
    billing_date = Column(TIMESTAMP, nullable=False)
    image_recognition_data = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    sales_person = relationship("SalesPerson")
    tax_rate = relationship("TaxRate")
    details = relationship("DeliveryNoteDetail", back_populates="delivery_note")

class DeliveryNoteDetail(Base):
    __tablename__ = "delivery_note_details"

    id = Column(Integer, primary_key=True, index=True)
    delivery_note_id = Column(Integer, ForeignKey("delivery_notes.id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)
    remarks = Column(String(200))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    delivery_note = relationship("DeliveryNote", back_populates="details")
    product = relationship("Product")

# 請求書テーブル
class SalesInvoice(Base):
    __tablename__ = "sales_invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    sales_person_id = Column(Integer, ForeignKey("sales_persons.id"), nullable=False)
    invoice_number = Column(String(50), default="T5810180900550", nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    discount_rate_id = Column(Integer, ForeignKey("discount_rates.id"), nullable=False)
    
    # 追加フィールド
    invoice_date = Column(Date, nullable=True)  # 請求日
    receipt_date = Column(Date, nullable=True)  # 領収日
    non_discountable_amount = Column(Integer, default=0, nullable=False)  # 割引対象外金額
    note = Column(String(500), nullable=True)  # 但（ただし書き）
    
    # ノルマ対象
    quota_subtotal = Column(Integer, default=0, nullable=False)
    quota_discount_amount = Column(Integer, default=0, nullable=False)
    quota_total = Column(Integer, default=0, nullable=False)
    
    # ノルマ対象外
    non_quota_subtotal = Column(Integer, default=0, nullable=False)
    non_quota_discount_amount = Column(Integer, default=0, nullable=False)
    non_quota_total = Column(Integer, default=0, nullable=False)
    
    # 合計
    total_amount_ex_tax = Column(Integer, default=0, nullable=False)
    tax_amount = Column(Integer, default=0, nullable=False)
    total_amount_inc_tax = Column(Integer, default=0, nullable=False)
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    sales_person = relationship("SalesPerson")
    discount_rate = relationship("DiscountRate")
    details = relationship("SalesInvoiceDetail", back_populates="sales_invoice", cascade="all, delete-orphan")

class SalesInvoiceDetail(Base):
    __tablename__ = "sales_invoice_details"
    
    id = Column(Integer, primary_key=True, index=True)
    sales_invoice_id = Column(Integer, ForeignKey("sales_invoices.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    total_quantity = Column(Integer, default=0, nullable=False)
    unit_price = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    sales_invoice = relationship("SalesInvoice", back_populates="details")
    product = relationship("Product")

class ContractorInvoice(Base):
    __tablename__ = "contractor_invoices"
    id = Column(Integer, primary_key=True, index=True)
    # 詳細は後で定義