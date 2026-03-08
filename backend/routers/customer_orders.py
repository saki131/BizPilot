from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import CustomerOrder, Customer, DepositRecord
from dependencies import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime
import uuid
import csv
import io

router = APIRouter(tags=["customer-orders"])

# ========== Pydantic Schemas ==========

class CustomerOrderCreate(BaseModel):
    customer_id: int
    order_date: str  # YYYY-MM-DD
    order_amount: int
    payment_due_date: str  # YYYY-MM-DD
    memo: Optional[str] = None

class CustomerOrderUpdate(BaseModel):
    customer_id: Optional[int] = None
    order_date: Optional[str] = None
    order_amount: Optional[int] = None
    payment_due_date: Optional[str] = None
    memo: Optional[str] = None

class CustomerOrderResponse(BaseModel):
    customer_order_id: str
    customer_id: int
    customer_name: str
    order_date: str
    order_amount: int
    payment_due_date: str
    payment_status: str
    deposit_record_id: Optional[str] = None
    memo: Optional[str] = None

    class Config:
        from_attributes = True

class DepositRecordResponse(BaseModel):
    deposit_record_id: str
    deposit_date: str
    depositor_name: Optional[str] = None
    amount: int
    detail1: Optional[str] = None
    detail2: Optional[str] = None
    matched_order_id: Optional[str] = None
    matched_customer_name: Optional[str] = None
    matched_order_amount: Optional[int] = None
    upload_batch_id: Optional[str] = None

    class Config:
        from_attributes = True

class DepositUploadResult(BaseModel):
    total_records: int
    deposit_only: int
    auto_matched: int
    unmatched: int
    matched_details: List[dict]
    unmatched_deposits: List[DepositRecordResponse]

# ========== ヘルパー関数 ==========

def _update_overdue_status(db: Session):
    """未入金かつ入金期限超過の注文を overdue に更新"""
    today = date.today()
    db.query(CustomerOrder).filter(
        CustomerOrder.payment_status == "unpaid",
        CustomerOrder.payment_due_date < today,
        CustomerOrder.deleted_flag == False
    ).update({"payment_status": "overdue"})
    db.commit()

def _order_to_response(order: CustomerOrder) -> CustomerOrderResponse:
    """CustomerOrder モデルをレスポンスに変換"""
    return CustomerOrderResponse(
        customer_order_id=str(order.customer_order_id),
        customer_id=order.customer_id,
        customer_name=order.customer.name if order.customer else "",
        order_date=order.order_date.isoformat() if order.order_date else "",
        order_amount=order.order_amount,
        payment_due_date=order.payment_due_date.isoformat() if order.payment_due_date else "",
        payment_status=order.payment_status,
        deposit_record_id=str(order.deposit_record_id) if order.deposit_record_id else None,
        memo=order.memo,
    )

def _deposit_to_response(dep: DepositRecord) -> DepositRecordResponse:
    """DepositRecord モデルをレスポンスに変換"""
    matched_name = None
    matched_amount = None
    if dep.matched_order and dep.matched_order.customer:
        matched_name = dep.matched_order.customer.name
        matched_amount = dep.matched_order.order_amount
    return DepositRecordResponse(
        deposit_record_id=str(dep.deposit_record_id),
        deposit_date=dep.deposit_date.isoformat() if dep.deposit_date else "",
        depositor_name=dep.depositor_name,
        amount=dep.amount,
        detail1=dep.detail1,
        detail2=dep.detail2,
        matched_order_id=str(dep.matched_order_id) if dep.matched_order_id else None,
        matched_customer_name=matched_name,
        matched_order_amount=matched_amount,
        upload_batch_id=dep.upload_batch_id,
    )

# ========== 注文 CRUD ==========

@router.get("/", response_model=List[CustomerOrderResponse])
async def get_customer_orders(
    status: Optional[str] = None,
    customer_id: Optional[int] = None,
    due_from: Optional[str] = None,
    due_to: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """注文一覧取得（フィルタ対応）"""
    _update_overdue_status(db)

    query = db.query(CustomerOrder).options(
        joinedload(CustomerOrder.customer)
    ).filter(CustomerOrder.deleted_flag == False)

    if status:
        query = query.filter(CustomerOrder.payment_status == status)
    if customer_id:
        query = query.filter(CustomerOrder.customer_id == customer_id)
    if due_from:
        query = query.filter(CustomerOrder.payment_due_date >= date.fromisoformat(due_from))
    if due_to:
        query = query.filter(CustomerOrder.payment_due_date <= date.fromisoformat(due_to))

    orders = query.order_by(CustomerOrder.order_date.desc()).all()
    return [_order_to_response(o) for o in orders]

@router.post("/", response_model=CustomerOrderResponse)
async def create_customer_order(
    order: CustomerOrderCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """注文作成"""
    # 顧客存在チェック
    customer = db.query(Customer).filter(
        Customer.customer_id == order.customer_id,
        Customer.deleted_flag == False
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="顧客が見つかりません")

    db_order = CustomerOrder(
        customer_id=order.customer_id,
        order_date=date.fromisoformat(order.order_date),
        order_amount=order.order_amount,
        payment_due_date=date.fromisoformat(order.payment_due_date),
        memo=order.memo,
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    # customerリレーション読み込み
    db.refresh(db_order, ["customer"])
    return _order_to_response(db_order)

@router.put("/{order_id}", response_model=CustomerOrderResponse)
async def update_customer_order(
    order_id: str,
    order: CustomerOrderUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """注文更新"""
    db_order = db.query(CustomerOrder).options(
        joinedload(CustomerOrder.customer)
    ).filter(
        CustomerOrder.customer_order_id == order_id,
        CustomerOrder.deleted_flag == False
    ).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="注文が見つかりません")

    update_data = order.dict(exclude_unset=True)
    for key, value in update_data.items():
        if key in ("order_date", "payment_due_date") and value:
            value = date.fromisoformat(value)
        setattr(db_order, key, value)

    db.commit()
    db.refresh(db_order)
    return _order_to_response(db_order)

@router.delete("/{order_id}")
async def delete_customer_order(
    order_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """注文削除（論理削除）"""
    db_order = db.query(CustomerOrder).filter(
        CustomerOrder.customer_order_id == order_id,
        CustomerOrder.deleted_flag == False
    ).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="注文が見つかりません")
    db_order.deleted_flag = True
    db.commit()
    return {"message": "注文を削除しました"}

# ========== 入金チェック ==========

@router.post("/deposits/upload", response_model=DepositUploadResult)
async def upload_deposits_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """ゆうちょCSVアップロード & 自動照合"""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="CSVファイルのみ対応しています")

    content = await file.read()
    # Shift-JIS or UTF-8 でデコード
    try:
        text = content.decode("shift_jis")
    except UnicodeDecodeError:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            text = content.decode("utf-8")

    reader = csv.reader(io.StringIO(text))
    batch_id = str(uuid.uuid4())[:8] + "_" + datetime.now().strftime("%Y%m%d%H%M%S")

    deposit_records = []
    for row_idx, row in enumerate(reader):
        if row_idx == 0:
            # ヘッダー行をスキップ（ただし列数チェック）
            continue
        if len(row) < 4:
            continue

        # ゆうちょCSV想定フォーマット: 取引日, 摘要(詳細1), お支払金額, お預り金額, 差引残高, メモ(詳細2)
        try:
            deposit_date_str = row[0].strip()
            detail1 = row[1].strip() if len(row) > 1 else ""
            withdrawal = row[2].strip() if len(row) > 2 else ""
            deposit_amount_str = row[3].strip() if len(row) > 3 else ""
            detail2 = row[5].strip() if len(row) > 5 else ""

            # 入金額が空または0の場合はスキップ（出金行）
            if not deposit_amount_str or deposit_amount_str == "0":
                continue

            # 日付パース（複数形式対応）
            deposit_date = None
            for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y年%m月%d日"):
                try:
                    deposit_date = datetime.strptime(deposit_date_str, fmt).date()
                    break
                except ValueError:
                    continue
            if not deposit_date:
                continue

            amount = int(deposit_amount_str.replace(",", ""))

            dep = DepositRecord(
                deposit_date=deposit_date,
                depositor_name=detail1,
                amount=amount,
                detail1=detail1,
                detail2=detail2,
                upload_batch_id=batch_id,
            )
            deposit_records.append(dep)

        except (ValueError, IndexError):
            continue

    # DB に保存
    for dep in deposit_records:
        db.add(dep)
    db.commit()

    # 自動照合
    unpaid_orders = db.query(CustomerOrder).options(
        joinedload(CustomerOrder.customer)
    ).filter(
        CustomerOrder.payment_status.in_(["unpaid", "overdue"]),
        CustomerOrder.deleted_flag == False
    ).all()

    matched_details = []
    auto_matched = 0

    for dep in deposit_records:
        db.refresh(dep)
        for order in unpaid_orders:
            # 金額一致チェック
            if dep.amount != order.order_amount:
                continue

            # 名前照合（部分一致: 振込人名に顧客名 or 顧客名カナが含まれる）
            depositor = dep.depositor_name or ""
            customer_name = order.customer.name if order.customer else ""
            customer_kana = order.customer.name_kana if order.customer else ""

            name_match = False
            if customer_name and customer_name in depositor:
                name_match = True
            elif customer_kana and customer_kana in depositor:
                name_match = True
            elif customer_name and depositor in customer_name:
                name_match = True

            if name_match:
                # 照合成功
                dep.matched_order_id = order.customer_order_id
                order.payment_status = "paid"
                order.deposit_record_id = dep.deposit_record_id
                auto_matched += 1
                matched_details.append({
                    "deposit_id": str(dep.deposit_record_id),
                    "depositor_name": dep.depositor_name,
                    "amount": dep.amount,
                    "order_id": str(order.customer_order_id),
                    "customer_name": customer_name,
                    "order_amount": order.order_amount,
                })
                # この注文は照合済みなのでリストから除外
                unpaid_orders.remove(order)
                break

    db.commit()

    # 未照合の入金をレスポンス用に取得
    unmatched = [dep for dep in deposit_records if dep.matched_order_id is None]

    return DepositUploadResult(
        total_records=len(deposit_records),
        deposit_only=len(deposit_records),
        auto_matched=auto_matched,
        unmatched=len(unmatched),
        matched_details=matched_details,
        unmatched_deposits=[_deposit_to_response(d) for d in unmatched],
    )

@router.get("/deposits/", response_model=List[DepositRecordResponse])
async def get_deposit_records(
    unmatched_only: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """入金記録一覧"""
    query = db.query(DepositRecord).options(
        joinedload(DepositRecord.matched_order).joinedload(CustomerOrder.customer)
    )
    if unmatched_only:
        query = query.filter(DepositRecord.matched_order_id == None)
    deposits = query.order_by(DepositRecord.deposit_date.desc()).all()
    return [_deposit_to_response(d) for d in deposits]

@router.post("/deposits/{deposit_id}/match/{order_id}")
async def manual_match(
    deposit_id: str,
    order_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """手動紐付け"""
    dep = db.query(DepositRecord).filter(
        DepositRecord.deposit_record_id == deposit_id
    ).first()
    if not dep:
        raise HTTPException(status_code=404, detail="入金記録が見つかりません")
    if dep.matched_order_id:
        raise HTTPException(status_code=400, detail="この入金記録は既に紐付け済みです")

    order = db.query(CustomerOrder).filter(
        CustomerOrder.customer_order_id == order_id,
        CustomerOrder.deleted_flag == False
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="注文が見つかりません")

    dep.matched_order_id = order.customer_order_id
    order.payment_status = "paid"
    order.deposit_record_id = dep.deposit_record_id
    db.commit()
    return {"message": "紐付けが完了しました"}

@router.delete("/deposits/{deposit_id}/match")
async def unmatch_deposit(
    deposit_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """紐付け解除"""
    dep = db.query(DepositRecord).filter(
        DepositRecord.deposit_record_id == deposit_id
    ).first()
    if not dep:
        raise HTTPException(status_code=404, detail="入金記録が見つかりません")
    if not dep.matched_order_id:
        raise HTTPException(status_code=400, detail="この入金記録は紐付けされていません")

    # 注文のステータスを元に戻す
    order = db.query(CustomerOrder).filter(
        CustomerOrder.customer_order_id == dep.matched_order_id
    ).first()
    if order:
        today = date.today()
        if order.payment_due_date < today:
            order.payment_status = "overdue"
        else:
            order.payment_status = "unpaid"
        order.deposit_record_id = None

    dep.matched_order_id = None
    db.commit()
    return {"message": "紐付けを解除しました"}
