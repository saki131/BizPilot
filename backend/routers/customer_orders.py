from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import CustomerOrder, Customer, DepositRecord
from dependencies import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime, timedelta
import uuid
import csv
import io
import base64
import os
import unicodedata

router = APIRouter(tags=["customer-orders"])

# ========== Pydantic Schemas ==========

class CustomerOrderCreate(BaseModel):
    customer_id: int
    order_amount: int
    memo: Optional[str] = None

class CustomerOrderBulkItem(BaseModel):
    customer_name: str
    order_amount: int
    order_date: Optional[str] = None
    memo: Optional[str] = None

class CustomerOrderBulkCreate(BaseModel):
    orders: List[CustomerOrderBulkItem]

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
    transaction_id: Optional[str] = None
    depositor_name: Optional[str] = None
    amount: int
    detail1: Optional[str] = None
    detail2: Optional[str] = None
    balance: Optional[int] = None
    upload_batch_id: Optional[str] = None
    matched_order_id: Optional[str] = None

    class Config:
        from_attributes = True

class ManualPaymentUpdate(BaseModel):
    payment_status: str  # "paid" or "unpaid"
    deposit_record_id: Optional[str] = None

class MatchedDetail(BaseModel):
    deposit_id: str
    depositor_name: Optional[str]
    amount: int
    order_id: str
    customer_name: str
    order_amount: int

class PendingMatch(BaseModel):
    deposit_id: str
    depositor_name: Optional[str]
    amount: int
    order_id: str
    customer_name: str
    customer_name_kana: Optional[str]
    order_amount: int

class DepositUploadResult(BaseModel):
    total_records: int
    deposit_only: int
    auto_matched: int
    pending_confirmation: int
    skipped_duplicates: int = 0
    matched_details: List[MatchedDetail]
    pending_matches: List[PendingMatch]

class ConfirmMatchRequest(BaseModel):
    deposit_id: str
    order_id: str

class ImageRecognitionResult(BaseModel):
    orders: List[dict]

# ========== ヘルパー関数 ==========

def _normalize_for_comparison(text: str) -> str:
    """文字列を正規化して比較用に変換（全角→半角、カタカナ→ひらがな等）"""
    if not text:
        return ""
    # NFKC正規化（全角英数→半角、半角カナ→全角カナ等）
    normalized = unicodedata.normalize("NFKC", text)
    # スペースを除去
    normalized = normalized.replace(" ", "").replace("　", "")
    return normalized

def _katakana_to_hiragana(text: str) -> str:
    """カタカナをひらがなに変換"""
    return "".join(
        chr(ord(ch) - 0x60) if "\u30A1" <= ch <= "\u30F6" else ch
        for ch in text
    )

def _check_name_match(depositor_name: str, customer_name: str, customer_kana: str) -> str:
    """名前照合: 'exact', 'partial', 'none' を返す"""
    if not depositor_name:
        return "none"
    
    dep_norm = _normalize_for_comparison(depositor_name)
    dep_hira = _katakana_to_hiragana(dep_norm)
    
    # 完全一致チェック（正規化後）
    if customer_name:
        cust_norm = _normalize_for_comparison(customer_name)
        if cust_norm and (cust_norm in dep_norm or dep_norm in cust_norm):
            return "exact"
    
    if customer_kana:
        kana_norm = _normalize_for_comparison(customer_kana)
        if kana_norm and (kana_norm in dep_norm or dep_norm in kana_norm):
            return "exact"
    
    # 部分一致チェック（ひらがな変換後の比較）
    if customer_name:
        cust_hira = _katakana_to_hiragana(_normalize_for_comparison(customer_name))
        if cust_hira and (cust_hira in dep_hira or dep_hira in cust_hira):
            return "partial"
    
    if customer_kana:
        kana_hira = _katakana_to_hiragana(_normalize_for_comparison(customer_kana))
        if kana_hira and (kana_hira in dep_hira or dep_hira in kana_hira):
            return "partial"
    
    return "none"

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
    return DepositRecordResponse(
        deposit_record_id=str(dep.deposit_record_id),
        deposit_date=dep.deposit_date.isoformat() if dep.deposit_date else "",
        transaction_id=dep.transaction_id,
        depositor_name=dep.depositor_name,
        amount=dep.amount,
        detail1=dep.detail1,
        detail2=dep.detail2,
        balance=dep.balance,
        upload_batch_id=dep.upload_batch_id,
        matched_order_id=str(dep.matched_order_id) if dep.matched_order_id else None,
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
    """注文作成（登録日=当日、入金期限=登録日+10日を自動設定）"""
    customer = db.query(Customer).filter(
        Customer.customer_id == order.customer_id,
        Customer.deleted_flag == False
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="顧客が見つかりません")

    today = date.today()
    db_order = CustomerOrder(
        customer_id=order.customer_id,
        order_date=today,
        order_amount=order.order_amount,
        payment_due_date=today + timedelta(days=10),
        memo=order.memo,
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    db.refresh(db_order, ["customer"])
    return _order_to_response(db_order)

@router.post("/bulk", response_model=List[CustomerOrderResponse])
async def create_customer_orders_bulk(
    data: CustomerOrderBulkCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """注文一括作成（画像認識結果から）"""
    today = date.today()
    created_orders = []
    
    for item in data.orders:
        if not item.customer_name or not item.customer_name.strip():
            continue
        # スペース（全角・半角）を除去して正規化
        normalized_name = item.customer_name.replace('\u3000', '').replace(' ', '').strip()
        if not normalized_name:
            continue
        # 顧客名でマスタを検索（スペース正規化後に完全一致）
        # DBの既存顧客名も正規化して比較するため、全件取得してPython側でフィルタ
        all_customers = db.query(Customer).filter(
            Customer.deleted_flag == False
        ).all()
        customer = next(
            (c for c in all_customers if c.name.replace('\u3000', '').replace(' ', '').strip() == normalized_name),
            None
        )
        # 一致する顧客がなければ新規作成
        if not customer:
            customer = Customer(
                name=normalized_name,
                deleted_flag=False,
            )
            db.add(customer)
            db.flush()  # customer_idを取得
        
        if item.order_date:
            try:
                order_date = date.fromisoformat(item.order_date)
            except ValueError:
                order_date = today
        else:
            order_date = today
        
        db_order = CustomerOrder(
            customer_id=customer.customer_id,
            order_date=order_date,
            order_amount=item.order_amount,
            payment_due_date=order_date + timedelta(days=10),
            memo=item.memo,
        )
        db.add(db_order)
        created_orders.append(db_order)
    
    db.commit()
    for o in created_orders:
        db.refresh(o)
        db.refresh(o, ["customer"])
    
    return [_order_to_response(o) for o in created_orders]

@router.post("/recognize-image")
async def recognize_order_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """注文台帳画像認識（Gemini APIで画像から注文情報を読み取り）"""
    from genai_wrapper import generate_content_with_image
    
    content = await file.read()
    image_b64 = base64.b64encode(content).decode("utf-8")
    
    # 顧客マスタを取得してプロンプトに含める
    customers = db.query(Customer).filter(Customer.deleted_flag == False).all()
    customer_list = [f"{c.customer_id}: {c.name}" for c in customers]
    
    from datetime import date as date_cls
    current_year = date_cls.today().year
    
    prompt = f"""この画像は注文台帳です。画像から注文情報を読み取ってJSON形式で返してください。

登録されている顧客マスタ:
{chr(10).join(customer_list)}

以下のJSON形式で返してください。顧客名はマスタのcustomer_idで指定してください。
マスタに一致する顧客がない場合はcustomer_idを0にしてください。

```json
{{
  "orders": [
    {{
      "customer_id": 1,
      "customer_name": "顧客名",
      "order_date": "YYYY-MM-DD",
      "order_amount": 10000,
      "memo": "メモ（あれば）"
    }}
  ]
}}
```

注意:
- 金額はカンマなしの整数で返してください
- 顧客名はマスタと照合して最も一致するcustomer_idを設定してください
- order_dateは画像の日付欄から読み取ってください。年が記載されていない場合は{current_year}年として解釈してください。形式はYYYY-MM-DDです
- 日付が読み取れない場合はnullにしてください
- 読み取れない部分はnullにしてください
- JSONのみ返してください（説明文は不要）"""

    try:
        model_name = "gemini-2.5-flash"
        response = generate_content_with_image(model_name, prompt, image_b64)
        
        import json
        response_text = response.text if hasattr(response, "text") else str(response)
        # JSON部分を抽出
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()
        
        result = json.loads(json_str)
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"画像認識に失敗しました: {str(e)}")

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

# ========== 入金履歴 ==========

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
    skipped_duplicates = 0
    for row_idx, row in enumerate(reader):
        # ヘッダー行（先頭3行）をスキップ
        if row_idx < 3:
            continue
        if len(row) < 4:
            continue

        # ゆうちょ残高等通知明細フォーマット:
        # 取引日, 入出金取引番号, お預り金額(円), お支払金額(円), 詳細1, 詳細2, 残高(残付)額
        try:
            deposit_date_str = row[0].strip()
            transaction_id = row[1].strip() if len(row) > 1 else ""
            deposit_amount_str = row[2].strip() if len(row) > 2 else ""
            detail1 = row[4].strip() if len(row) > 4 else ""
            detail2 = row[5].strip() if len(row) > 5 else ""
            balance_str = row[6].strip() if len(row) > 6 else ""

            # 入金額が空または0の場合はスキップ（出金行）
            if not deposit_amount_str or deposit_amount_str == "0":
                continue

            # 日付パース（YYYYMMDD形式）
            deposit_date = None
            for fmt in ("%Y%m%d", "%Y/%m/%d", "%Y-%m-%d"):
                try:
                    deposit_date = datetime.strptime(deposit_date_str, fmt).date()
                    break
                except ValueError:
                    continue
            if not deposit_date:
                continue

            amount = int(deposit_amount_str.replace(",", ""))
            balance = int(balance_str.replace(",", "")) if balance_str else None

            # 重複チェック：transaction_id がある場合はそれで、ない場合は日付+金額+振込人名で確認
            if transaction_id:
                exists = db.query(DepositRecord).filter(
                    DepositRecord.transaction_id == transaction_id
                ).first()
            else:
                exists = db.query(DepositRecord).filter(
                    DepositRecord.deposit_date == deposit_date,
                    DepositRecord.amount == amount,
                    DepositRecord.depositor_name == detail2,
                ).first()
            if exists:
                skipped_duplicates += 1
                continue

            dep = DepositRecord(
                deposit_date=deposit_date,
                transaction_id=transaction_id,
                depositor_name=detail2,  # 詳細2が振込人名
                amount=amount,
                detail1=detail1,
                detail2=detail2,
                balance=balance,
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
        CustomerOrder.payment_status == "unpaid",
        CustomerOrder.deleted_flag == False
    ).all()

    matched_details = []
    pending_matches = []
    auto_matched = 0

    for dep in deposit_records:
        db.refresh(dep)
        for order in list(unpaid_orders):
            # 金額一致チェック
            if dep.amount != order.order_amount:
                continue

            # 入金日が登録日～入金期限の範囲内かチェック
            if not (order.order_date <= dep.deposit_date <= order.payment_due_date):
                continue

            # 名前照合
            depositor = dep.depositor_name or ""
            customer_name = order.customer.name if order.customer else ""
            customer_kana = order.customer.name_kana if order.customer else ""

            match_type = _check_name_match(depositor, customer_name, customer_kana)

            if match_type == "exact":
                # 完全一致 → 自動でステータス更新
                dep.matched_order_id = order.customer_order_id
                order.payment_status = "paid"
                order.deposit_record_id = dep.deposit_record_id
                auto_matched += 1
                matched_details.append(MatchedDetail(
                    deposit_id=str(dep.deposit_record_id),
                    depositor_name=dep.depositor_name,
                    amount=dep.amount,
                    order_id=str(order.customer_order_id),
                    customer_name=customer_name,
                    order_amount=order.order_amount,
                ))
                unpaid_orders.remove(order)
                break
            elif match_type == "partial":
                # 部分一致 → 確認待ち
                pending_matches.append(PendingMatch(
                    deposit_id=str(dep.deposit_record_id),
                    depositor_name=dep.depositor_name,
                    amount=dep.amount,
                    order_id=str(order.customer_order_id),
                    customer_name=customer_name,
                    customer_name_kana=customer_kana,
                    order_amount=order.order_amount,
                ))
                break

    db.commit()

    return DepositUploadResult(
        total_records=len(deposit_records),
        deposit_only=len(deposit_records),
        auto_matched=auto_matched,
        pending_confirmation=len(pending_matches),
        skipped_duplicates=skipped_duplicates,
        matched_details=matched_details,
        pending_matches=pending_matches,
    )

@router.post("/deposits/confirm-match")
async def confirm_match(
    req: ConfirmMatchRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """部分一致確認後のステータス更新"""
    dep = db.query(DepositRecord).filter(
        DepositRecord.deposit_record_id == req.deposit_id
    ).first()
    if not dep:
        raise HTTPException(status_code=404, detail="入金記録が見つかりません")

    order = db.query(CustomerOrder).filter(
        CustomerOrder.customer_order_id == req.order_id,
        CustomerOrder.deleted_flag == False
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="注文が見つかりません")

    dep.matched_order_id = order.customer_order_id
    order.payment_status = "paid"
    order.deposit_record_id = dep.deposit_record_id
    db.commit()
    return {"message": "入金確認が完了しました"}

@router.get("/deposits/", response_model=List[DepositRecordResponse])
async def get_deposit_records(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """入金記録一覧（CSV取り込み分のみ表示、照合結果なし）"""
    deposits = db.query(DepositRecord).order_by(
        DepositRecord.deposit_date.desc()
    ).all()
    return [_deposit_to_response(d) for d in deposits]

@router.post("/deposits/check-payments", response_model=DepositUploadResult)
async def check_payments(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """既存の未照合入金記録と未払い注文を再照合してステータス更新"""
    # 未照合の入金記録を取得
    unmatched_deposits = db.query(DepositRecord).filter(
        DepositRecord.matched_order_id == None
    ).all()

    # 未払い注文を取得
    unpaid_orders = db.query(CustomerOrder).options(
        joinedload(CustomerOrder.customer)
    ).filter(
        CustomerOrder.payment_status == "unpaid",
        CustomerOrder.deleted_flag == False
    ).all()

    matched_details = []
    pending_matches = []
    auto_matched = 0

    for dep in unmatched_deposits:
        for order in list(unpaid_orders):
            if dep.amount != order.order_amount:
                continue
            if not (order.order_date <= dep.deposit_date <= order.payment_due_date):
                continue
            depositor = dep.depositor_name or ""
            customer_name = order.customer.name if order.customer else ""
            customer_kana = order.customer.name_kana if order.customer else ""
            match_type = _check_name_match(depositor, customer_name, customer_kana)
            if match_type == "exact":
                dep.matched_order_id = order.customer_order_id
                order.payment_status = "paid"
                order.deposit_record_id = dep.deposit_record_id
                auto_matched += 1
                matched_details.append(MatchedDetail(
                    deposit_id=str(dep.deposit_record_id),
                    depositor_name=dep.depositor_name,
                    amount=dep.amount,
                    order_id=str(order.customer_order_id),
                    customer_name=customer_name,
                    order_amount=order.order_amount,
                ))
                unpaid_orders.remove(order)
                break
            elif match_type == "partial":
                pending_matches.append(PendingMatch(
                    deposit_id=str(dep.deposit_record_id),
                    depositor_name=dep.depositor_name,
                    amount=dep.amount,
                    order_id=str(order.customer_order_id),
                    customer_name=customer_name,
                    customer_name_kana=customer_kana,
                    order_amount=order.order_amount,
                ))
                break

    db.commit()

    return DepositUploadResult(
        total_records=len(unmatched_deposits),
        deposit_only=len(unmatched_deposits),
        auto_matched=auto_matched,
        pending_confirmation=len(pending_matches),
        matched_details=matched_details,
        pending_matches=pending_matches,
    )

@router.patch("/{order_id}/payment-status", response_model=CustomerOrderResponse)
async def update_payment_status(
    order_id: str,
    update: ManualPaymentUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """手動で入金ステータス・紐付け入金記録を更新"""
    db_order = db.query(CustomerOrder).options(
        joinedload(CustomerOrder.customer)
    ).filter(
        CustomerOrder.customer_order_id == order_id,
        CustomerOrder.deleted_flag == False
    ).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="注文が見つかりません")

    if update.payment_status not in ("paid", "unpaid"):
        raise HTTPException(status_code=400, detail="payment_status は 'paid' または 'unpaid' のみ指定できます")

    # 以前に紐付いていた入金記録の matched_order_id を解除
    if db_order.deposit_record_id:
        old_dep = db.query(DepositRecord).filter(
            DepositRecord.deposit_record_id == db_order.deposit_record_id
        ).first()
        if old_dep:
            old_dep.matched_order_id = None

    if update.payment_status == "paid":
        db_order.payment_status = "paid"
        if update.deposit_record_id:
            try:
                dep_uuid = uuid.UUID(update.deposit_record_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="deposit_record_id が不正なUUIDです")
            new_dep = db.query(DepositRecord).filter(
                DepositRecord.deposit_record_id == dep_uuid
            ).first()
            if not new_dep:
                raise HTTPException(status_code=404, detail="入金記録が見つかりません")
            new_dep.matched_order_id = db_order.customer_order_id
            db_order.deposit_record_id = new_dep.deposit_record_id
        else:
            db_order.deposit_record_id = None
    else:  # unpaid
        db_order.payment_status = "unpaid"
        db_order.deposit_record_id = None

    db.commit()
    db.refresh(db_order)
    return _order_to_response(db_order)
