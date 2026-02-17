from sqlalchemy import Column, Integer, String, Boolean, DECIMAL, TIMESTAMP, Text, func, ForeignKey, JSON, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import uuid

class User(Base):
    __tablename__ = "users"

    # Columns:
    # id: 主キー（整数）
    # username: ユーザー名（ログインID）
    # hashed_password: ハッシュ化されたパスワード
    # created_at: 作成日時
    # updated_at: 更新日時
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    deleted_flag = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class SalesPerson(Base):
    __tablename__ = "sales_persons"
    # Columns:
    # id: 主キー（販売員ID）
    # name: 販売員氏名
    # deleted_flag: 削除フラグ
    # display_order: 表示順
    # created_at: 作成日時
    # updated_at: 更新日時
    sales_person_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    deleted_flag = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Product(Base):
    __tablename__ = "products"
    # Columns:
    # id: 主キー（商品ID）
    # name: 商品名
    # price: 単価（整数、税抜）
    # discount_exclusion_flag: 割引対象外フラグ
    # quota_exclusion_flag: ノルマ算定除外フラグ
    # quota_target_flag: ノルマ対象フラグ
    # deleted_flag: 削除フラグ
    # display_order: 表示順
    # created_at: 作成日時
    # updated_at: 更新日時
    product_id = Column(Integer, primary_key=True, index=True)
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
    # Columns:
    # id: 主キー（委託先ID）
    # name: 委託先名
    # deleted_flag: 削除フラグ
    # display_order: 表示順
    # created_at: 作成日時
    # updated_at: 更新日時
    contractor_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    deleted_flag = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class TaxRate(Base):
    __tablename__ = "tax_rates"
    # Columns:
    # id: 主キー（税率ID）
    # rate: 税率（例: 0.10）
    # display_name: 表示名（例: 10%）
    # deleted_flag: 削除フラグ
    # created_at: 作成日時
    # updated_at: 更新日時
    tax_rate_id = Column(Integer, primary_key=True, index=True)
    rate = Column(DECIMAL(4, 2), nullable=False)
    display_name = Column(String(20), nullable=False)
    deleted_flag = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class DiscountRate(Base):
    __tablename__ = "discount_rates"
    # Columns:
    # id: 主キー（割引率ID）
    # rate: 割引率（小数、例: 0.20 = 20%）
    # threshold_amount: 割引適用下限金額
    # sales_person_flag: 顧客種別フラグ（True=販売員向け、False=委託先向け）
    # deleted_flag: 削除フラグ
    # created_at: 作成日時
    # updated_at: 更新日時
    discount_rate_id = Column(Integer, primary_key=True, index=True)
    rate = Column(DECIMAL(4, 2), nullable=False)
    threshold_amount = Column(Integer, default=0)  # 下限額
    sales_person_flag = Column(Boolean, default=True)
    deleted_flag = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class DeliveryNote(Base):
    __tablename__ = "delivery_notes"
    # Columns:
    # id: 主キー（納品書ID, UUID）
    # sales_person_id: 販売員ID（外部キー）
    # tax_rate_id: 税率ID（外部キー）
    # quota_amount: ノルマ対象合計（税抜）
    # non_quota_amount: ノルマ対象外合計（税抜）
    # tax_amount: 消費税額
    # total_amount_ex_tax: 合計（税抜）
    # total_amount_inc_tax: 合計（税込）
    # remarks: 備考／但し書き
    # file_path: ファイルパス（PDF等）
    # delivery_date: 納品日
    # billing_date: 請求日／締め日
    # image_recognition_data: 画像OCRデータ（JSON）
    # image_filename: 画像ファイル名
    # created_at: 作成日時
    # updated_at: 更新日時
    delivery_note_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    sales_person_id = Column(Integer, ForeignKey("sales_persons.sales_person_id"))
    tax_rate_id = Column(Integer, ForeignKey("tax_rates.tax_rate_id"))
    quota_amount = Column(Integer, default=0)
    non_quota_amount = Column(Integer, default=0)
    tax_amount = Column(Integer, default=0)
    total_amount_ex_tax = Column(Integer, default=0)
    total_amount_inc_tax = Column(Integer, default=0)
    remarks = Column(Text)
    file_path = Column(String(500))
    delivery_date = Column(TIMESTAMP, nullable=False)
    billing_date = Column(TIMESTAMP, nullable=False)
    image_recognition_data = Column(JSON)
    image_filename = Column(String(500))  # 画像ファイル名
    deleted_flag = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    sales_person = relationship("SalesPerson")
    tax_rate = relationship("TaxRate")
    details = relationship("DeliveryNoteDetail", back_populates="delivery_note")

class DeliveryNoteDetail(Base):
    __tablename__ = "delivery_note_details"
    # Columns:
    # id: 主キー（納品書明細ID, UUID）
    # delivery_note_id: 納品書ID（外部キー）
    # product_id: 商品ID（外部キー）
    # quantity: 数量
    # unit_price: 単価
    # amount: 金額（税抜）
    # remarks: 備考
    # created_at: 作成日時
    # updated_at: 更新日時
    delivery_note_detail_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    delivery_note_id = Column(UUID(as_uuid=True), ForeignKey("delivery_notes.delivery_note_id", ondelete="CASCADE"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)
    remarks = Column(String(200))
    deleted_flag = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    delivery_note = relationship("DeliveryNote", back_populates="details")
    product = relationship("Product")

# 請求書テーブル
class SalesInvoice(Base):
    __tablename__ = "sales_invoices"
    # Columns:
    # id: 主キー（販売員請求書ID, UUID）
    # sales_person_id: 販売員ID（外部キー）
    # tax_rate_id: 税率ID（外部キー）
    # discount_rate_id: 割引率ID（外部キー）
    sales_invoice_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    sales_person_id = Column(Integer, ForeignKey("sales_persons.sales_person_id"), nullable=False)
    tax_rate_id = Column(Integer, ForeignKey("tax_rates.tax_rate_id"), nullable=False)
    discount_rate_id = Column(Integer, ForeignKey("discount_rates.discount_rate_id"), nullable=False)

    # invoice_date: 請求日
    # receipt_date: 領収日
    # non_discountable_amount: 割引対象外金額
    # note: 但し書き
    invoice_date = Column(Date, nullable=True)  # 請求日
    receipt_date = Column(Date, nullable=True)  # 領収日
    non_discountable_amount = Column(Integer, default=0, nullable=False)  # 割引対象外金額
    note = Column(String(500), nullable=True)  # 但（ただし書き）
    
    # ノルマ対象
    # quota_subtotal: ノルマ対象小計（税抜）
    # quota_discount_amount: ノルマ対象割引額
    # quota_total: ノルマ対象割引後金額
    quota_subtotal = Column(Integer, default=0, nullable=False)
    quota_discount_amount = Column(Integer, default=0, nullable=False)
    quota_total = Column(Integer, default=0, nullable=False)
    
    # ノルマ対象外
    # non_quota_subtotal: ノルマ対象外小計（税抜）
    # non_quota_discount_amount: ノルマ対象外割引額
    # non_quota_total: ノルマ対象外割引後金額
    non_quota_subtotal = Column(Integer, default=0, nullable=False)
    non_quota_discount_amount = Column(Integer, default=0, nullable=False)
    non_quota_total = Column(Integer, default=0, nullable=False)
    
    # 合計
    # total_amount_ex_tax: 合計（税抜）
    # tax_amount: 消費税額
    # total_amount_inc_tax: 合計（税込）
    total_amount_ex_tax = Column(Integer, default=0, nullable=False)
    tax_amount = Column(Integer, default=0, nullable=False)
    total_amount_inc_tax = Column(Integer, default=0, nullable=False)
    deleted_flag = Column(Boolean, default=False)
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    sales_person = relationship("SalesPerson")
    tax_rate = relationship("TaxRate")
    discount_rate = relationship("DiscountRate")
    details = relationship("SalesInvoiceDetail", back_populates="sales_invoice", cascade="all, delete-orphan")

class SalesInvoiceDetail(Base):
    __tablename__ = "sales_invoice_details"
    # Columns:
    # id: 主キー（販売員請求書明細ID, UUID）
    # sales_invoice_id: 販売員請求書ID（外部キー）
    # product_id: 商品ID（外部キー）
    # total_quantity: 数量
    # unit_price: 単価
    # amount: 金額（税抜）
    # created_at: 作成日時
    # updated_at: 更新日時
    sales_invoice_detail_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    sales_invoice_id = Column(UUID(as_uuid=True), ForeignKey("sales_invoices.sales_invoice_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    total_quantity = Column(Integer, default=0, nullable=False)
    unit_price = Column(Integer, nullable=False)
    amount = Column(Integer, nullable=False)
    deleted_flag = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    sales_invoice = relationship("SalesInvoice", back_populates="details")
    product = relationship("Product")

class ContractorInvoice(Base):
    __tablename__ = "contractor_invoices"
    # Columns:
    # id: 主キー（委託先請求書ID, UUID）
    # contractor_id: 委託先ID（外部キー）
    # discount_rate_id: 割引率ID（外部キー）
    # tax_rate_id: 税率ID（外部キー）
    contractor_invoice_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    contractor_id = Column(Integer, ForeignKey("contractors.contractor_id"), nullable=False)
    discount_rate_id = Column(Integer, ForeignKey("discount_rates.discount_rate_id"), nullable=False)
    tax_rate_id = Column(Integer, ForeignKey("tax_rates.tax_rate_id"), nullable=False)
    
    # 金額フィールド
    # non_discountable_amount: 割引対象外金額
    non_discountable_amount = Column(Integer, default=0, nullable=False)  # 割引対象外金額
    
    # ノルマ対象
    quota_subtotal = Column(Integer, default=0, nullable=False)  # ノルマ対象金額
    quota_discount_amount = Column(Integer, default=0, nullable=False)  # ノルマ対象割引額
    quota_total = Column(Integer, default=0, nullable=False)  # ノルマ対象割引後金額
    
    # ノルマ対象外
    non_quota_subtotal = Column(Integer, default=0, nullable=False)  # ノルマ対象外金額
    non_quota_discount_amount = Column(Integer, default=0, nullable=False)  # ノルマ対象外割引額
    non_quota_total = Column(Integer, default=0, nullable=False)  # ノルマ対象外割引後金額
    
    # 合計
    total_amount_ex_tax = Column(Integer, default=0, nullable=False)  # 合計金額（税抜）
    total_discount_amount = Column(Integer, default=0, nullable=False)  # 割引額合計
    total_after_discount = Column(Integer, default=0, nullable=False)  # 割引後合計金額
    tax_amount = Column(Integer, default=0, nullable=False)  # 消費税額
    total_amount_inc_tax = Column(Integer, default=0, nullable=False)  # 合計金額（税込）
    
    # その他
    # note: 備考
    # invoice_date: 請求日
    # receipt_date: 領収日
    # payment_due_date: 支払期日
    # deleted_flag: 削除フラグ
    note = Column(String(500), nullable=True)  # 備考
    invoice_date = Column(Date, nullable=False)  # 請求日
    receipt_date = Column(Date, nullable=True)  # 領収日
    payment_due_date = Column(Date, nullable=True)  # 支払期日
    deleted_flag = Column(Boolean, default=False, nullable=False)  # 削除フラグ
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    contractor = relationship("Contractor")
    discount_rate = relationship("DiscountRate")
    tax_rate = relationship("TaxRate")
    details = relationship("ContractorInvoiceDetail", back_populates="contractor_invoice", cascade="all, delete-orphan")

class ContractorInvoiceDetail(Base):
    __tablename__ = "contractor_invoice_details"
    # Columns:
    # id: 主キー（委託先請求書明細ID, UUID）
    # contractor_invoice_id: 委託先請求書ID（外部キー）
    # product_id: 商品ID（外部キー）
    # total_quantity: 数量
    # unit_price: 単価
    # amount: 金額（税抜）
    # deleted_flag: 削除フラグ
    # created_at: 作成日時
    # updated_at: 更新日時
    contractor_invoice_detail_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    contractor_invoice_id = Column(UUID(as_uuid=True), ForeignKey("contractor_invoices.contractor_invoice_id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=False)
    total_quantity = Column(Integer, default=0, nullable=False)  # 数量
    unit_price = Column(Integer, nullable=False)  # 単価
    amount = Column(Integer, nullable=False)  # 金額（税抜）
    deleted_flag = Column(Boolean, default=False, nullable=False)  # 削除フラグ
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    contractor_invoice = relationship("ContractorInvoice", back_populates="details")
    product = relationship("Product")