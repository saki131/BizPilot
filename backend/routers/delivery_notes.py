from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
from models import DeliveryNote, DeliveryNoteDetail
from dependencies import get_current_user
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import shutil
import os
import base64
import json
import traceback
import re
from pathlib import Path
from config import settings
from genai_wrapper import configure as genai_configure, generate_content_with_image, set_api_keys
import os

router = APIRouter(prefix="/delivery-notes", tags=["delivery notes"])

# Configure GenAI client with multiple API keys
_api_keys = settings.GEMINI_API_KEYS
if _api_keys:
    print(f"[DEBUG] Loaded {len(_api_keys)} Gemini API key(s)")
    for i, key in enumerate(_api_keys):
        print(f"[DEBUG] API Key {i+1}: ...{key[-8:] if len(key) >= 8 else '***'}")
    set_api_keys(_api_keys)
    # Configure with first key initially
    genai_configure(_api_keys[0])
else:
    print(f"[WARNING] No Gemini API keys found in environment")
    
MODEL_NAME = 'gemini-2.5-flash'  # 費用対効果と高スループット向けに最適化

def recognize_delivery_note_image(image_path: str, db: Session) -> dict:
    """Gemini APIを使って納品書画像を認識する"""
    print(f"Starting recognition for image: {image_path}")
    
    try:
        # マスタデータを取得
        from models import SalesPerson, Product, TaxRate
        
        sales_persons = db.query(SalesPerson).filter(SalesPerson.deleted_flag == False).all()
        products = db.query(Product).filter(Product.deleted_flag == False).all()
        tax_rates = db.query(TaxRate).filter(TaxRate.deleted_flag == False).all()
        
        print(f"Loaded {len(sales_persons)} sales persons, {len(products)} products, {len(tax_rates)} tax rates")
        
        # マスタデータをプロンプト用に整形
        sales_person_list = [f"{sp.id}: {sp.name}" for sp in sales_persons]
        product_list = [f"{p.id}: {p.name} (¥{p.price})" for p in products]
        tax_rate_list = [f"{tr.id}: {tr.display_name} ({tr.rate}%)" for tr in tax_rates]
        
        # 画像をBase64エンコード
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        print(f"Image encoded, size: {len(image_data)} chars")
        
        # Gemini APIプロンプト
        prompt = f"""
納品書の画像を解析して、以下のJSON形式で情報を抽出してください。

【重要】IDは必ず数字のみで返してください。名前ではなくIDの数字を使用すること。

【マスタデータ】
販売員一覧（ID: 名前の形式）:
{chr(10).join(sales_person_list)}

商品一覧（ID: 商品名 (価格)の形式）:
{chr(10).join(product_list)}

税率一覧（ID: 表示名 (税率%)の形式）:
{chr(10).join(tax_rate_list)}

抽出が必要な情報:
1. 販売員名からマスタの販売員IDを特定
2. 納品日（YYYY/MM/DD形式,例：R7年1月5日の場合2025/01/05に変換）
3. 税率からマスタの税率IDを特定
4. 商品明細（商品名、数量、単価）と対応する商品IDを特定
5. 納品書に記載された「税抜合計金額」を読み取り、各明細の税抜金額の合計と一致するかを確認

【重要】商品名の読み取りルール:
- 商品名欄で「"」（ダブルクォート）や省略記号が使われている場合は、直前の商品名と同じ商品を意味します
- 例：「アクアカラー②」の次に「"③」とある場合は「アクアカラー③」を意味します
- 省略されている商品名は必ず完全な商品名に展開してからマスタと照合してください
- 数字や記号（①②③④⑤⑥⑦⑧⑨⑩等）が付いている場合も含めて完全な商品名として認識してください
- 「シャンプー」とある場合は「ハイシャンプー」を意味します
- 「リンス」とある場合は「リンス＆ヘアパック」を意味します
- 画像から読み取った商品名に最も近いマスタの商品を選択し、そのIDを使用

【重要】数値の読み取りルール:
- 数量は整数で読み取ってください
- 単価は円単位で読み取ってください
- 各明細行の「金額」は税抜き金額を読み取ってください
- 納品書に記載されている「税抜合計金額」も読み取り、読み取れた各明細行の税抜金額の合計と比較してください

【重要】読み取り成功の条件:
以下の全ての項目が正確に特定できた場合のみ成功とし、1つでも不明・未特定の場合は読み取り失敗として処理してください：
- 販売員IDがマスタデータから特定できること
- 納品日が明確に読み取れること
- 税率IDがマスタデータから特定できること
- 全ての商品明細について、商品IDがマスタデータから特定でき、数量・単価・金額が読み取れること
- 読み取れた各明細の税抜金額（amount）の合計が、納品書に記載された税抜合計金額と一致していること


補足:
- 一部の明細行がどうしても読み取れない場合、それらの行は items に含めなくても構いません。
- ただし、その場合でも「読み取れた明細のみの税抜金額合計」と「納品書に記載された税抜合計金額」が一致している場合は success を true（読み取り成功）としてください。
- 逆に、各明細の税抜金額の合計と税抜合計金額が一致しない場合は、明細のどこかに誤りがあるとみなし、必ず success を false（読み取り失敗）としてください。

重要: 必ず以下のJSON形式でのみ回答してください。コメント、説明、コードブロック記号（\`\`\`json等）は一切含めないでください。


【出力JSON形式】
必ず以下の形式のJSONのみを出力してください。説明文は不要です。
成功の場合（全ての必須項目が特定できた場合のみ）:
{{
  "success": true,
  "salesPersonId": 1,
  "deliveryDate": "2026-01-15",
  "taxRateId": 1,
  "details": [
    {{
      "productId": 1,
      "quantity": 2,
      "unitPrice": 1000
    }}
  ]
}}

【注意事項】
- salesPersonId, taxRateId, productIdは必ず数字（整数）で返すこと
- 文字列ではなく数値型で返すこと
- 失敗時は {{"success": false, "failureReason": "理由"}} を返す
"""
        
        print(f"Prompt length: {len(prompt)} chars")
        
        # Gemini / GenAI API呼び出し（wrapper経由）
        try:
            response = generate_content_with_image(MODEL_NAME, prompt, image_data)
            print("GenAI API call completed")

            # レスポンスを抽出
            result_text = getattr(response, 'text', None)
            if result_text is None:
                # fallback: full repr
                result_text = str(response)

            result_text = str(result_text).strip()
            print(f"Raw response (preview): {result_text[:400]}...")

            # 保存（診断用）
            try:
                diag_dir = Path("uploads") / "genai_diagnostics"
                diag_dir.mkdir(parents=True, exist_ok=True)
                import time
                ts = int(time.time())
                diag_path = diag_dir / f"resp_{ts}.txt"
                with open(diag_path, "w", encoding="utf-8") as f:
                    f.write("=== repr(response) ===\n")
                    f.write(repr(response) + "\n\n")
                    f.write("=== text ===\n")
                    f.write(result_text + "\n")
                print(f"Saved GenAI raw response to {diag_path}")
            except Exception as e:
                print(f"Failed to save diagnostic response: {e}")

            # remove triple-backtick fences if present
            if result_text.startswith('```') and '```' in result_text[3:]:
                # remove leading fence
                idx = result_text.find('\n')
                if idx != -1:
                    result_text = result_text[idx+1:]
                # remove trailing fence if present
                if result_text.endswith('```'):
                    result_text = result_text[:-3]

            # try direct JSON parse first
            try:
                result = json.loads(result_text)
                print(f"Parsed result (direct JSON): {type(result)}")
                
                # 認識成功時に税率情報と税込み金額を追加
                if result.get("success") and result.get("taxRateId"):
                    # 税率情報を取得
                    tax_rate = db.query(TaxRate).filter(TaxRate.id == result["taxRateId"]).first()
                    if tax_rate:
                        # 税抜き合計を計算
                        subtotal = sum(detail["quantity"] * detail["unitPrice"] for detail in result.get("details", []))
                        
                        # 税率を適用（DBの税率が10.0のような場合は/100する）
                        rate_value = tax_rate.rate
                        if rate_value >= 1:
                            rate_value = rate_value / 100
                        
                        # 消費税額を計算
                        tax_amount = int(subtotal * rate_value)
                        
                        # 税込み合計を計算
                        total_including_tax = subtotal + tax_amount
                        
                        # 結果に追加情報を付与
                        result["taxRate"] = {
                            "id": tax_rate.id,
                            "rate": tax_rate.rate,
                            "display_name": tax_rate.display_name
                        }
                        result["subtotal"] = subtotal
                        result["taxAmount"] = tax_amount
                        result["totalIncludingTax"] = total_including_tax
                
                return result
            except Exception:
                # try to extract JSON object using regex (first { ... } block)
                try:
                    m = re.search(r"\{[\s\S]*\}", result_text)
                    if m:
                        json_text = m.group(0)
                        result = json.loads(json_text)
                        print("Parsed result (extracted JSON block)")
                        
                        # 認識成功時に税率情報と税込み金額を追加
                        if result.get("success") and result.get("taxRateId"):
                            # 税率情報を取得
                            tax_rate = db.query(TaxRate).filter(TaxRate.id == result["taxRateId"]).first()
                            if tax_rate:
                                # 税抜き合計を計算
                                subtotal = sum(detail["quantity"] * detail["unitPrice"] for detail in result.get("details", []))
                                
                                # 税率を適用（DBの税率が10.0のような場合は/100する）
                                rate_value = tax_rate.rate
                                if rate_value >= 1:
                                    rate_value = rate_value / 100
                                
                                # 消費税額を計算
                                tax_amount = int(subtotal * rate_value)
                                
                                # 税込み合計を計算
                                total_including_tax = subtotal + tax_amount
                                
                                # 結果に追加情報を付与
                                result["taxRate"] = {
                                    "id": tax_rate.id,
                                    "rate": tax_rate.rate,
                                    "display_name": tax_rate.display_name
                                }
                                result["subtotal"] = subtotal
                                result["taxAmount"] = tax_amount
                                result["totalIncludingTax"] = total_including_tax
                        
                        return result
                except Exception as e_json:
                    print(f"JSON extraction failed: {e_json}")

            # 最後の手段: そのまま文字列をエラー情報として返す
            return {
                "success": False,
                "failureReason": "認識結果のパースに失敗しました",
                "raw_response": result_text[:2000]
            }

        except Exception as e:
            tb = traceback.format_exc()
            print(f"Error in recognize_delivery_note_image (API call): {e}\n{tb}")
            # 保存して戻す
            try:
                diag_dir = Path("uploads") / "genai_diagnostics"
                diag_dir.mkdir(parents=True, exist_ok=True)
                import time
                ts = int(time.time())
                err_path = diag_dir / f"error_{ts}.txt"
                with open(err_path, "w", encoding="utf-8") as f:
                    f.write("Exception:\n")
                    f.write(tb)
            except Exception as ee:
                print(f"Failed to write exception diag: {ee}")

            return {
                "success": False,
                "failureReason": f"認識エラー: {str(e)}"
            }
        
    except Exception as e:
        print(f"Error in recognize_delivery_note_image: {str(e)}")
        return {
            "success": False,
            "failureReason": f"認識エラー: {str(e)}"
        }

# Pydantic schemas
class DeliveryNoteDetailBase(BaseModel):
    product_id: int
    quantity: int
    unit_price: int
    remarks: Optional[str] = None

class DeliveryNoteDetailCreate(DeliveryNoteDetailBase):
    pass

class DeliveryNoteDetailResponse(DeliveryNoteDetailBase):
    id: int
    delivery_note_id: int

    class Config:
        from_attributes = True

class DeliveryNoteBase(BaseModel):
    sales_person_id: int
    tax_rate_id: int
    delivery_date: date
    billing_date: date
    delivery_note_number: str
    remarks: Optional[str] = None
    image_filename: Optional[str] = None

class DeliveryNoteCreate(DeliveryNoteBase):
    details: List[DeliveryNoteDetailCreate]

class DeliveryNoteResponse(DeliveryNoteBase):
    id: int
    details: List[DeliveryNoteDetailResponse]

    class Config:
        from_attributes = True

# Delivery Note endpoints
@router.get("/", response_model=List[DeliveryNoteResponse])
async def get_delivery_notes(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    delivery_notes = db.query(DeliveryNote).all()
    return delivery_notes

@router.post("/", response_model=DeliveryNoteResponse)
async def create_delivery_note(delivery_note: DeliveryNoteCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Create delivery note
    db_delivery_note = DeliveryNote(
        sales_person_id=delivery_note.sales_person_id,
        tax_rate_id=delivery_note.tax_rate_id,
        delivery_date=delivery_note.delivery_date,
        billing_date=delivery_note.billing_date,
        delivery_note_number=delivery_note.delivery_note_number,
        remarks=delivery_note.remarks,
        image_filename=delivery_note.image_filename
    )
    db.add(db_delivery_note)
    db.commit()
    db.refresh(db_delivery_note)

    # Create delivery note details
    for detail in delivery_note.details:
        amount = detail.quantity * detail.unit_price
        db_detail = DeliveryNoteDetail(
            delivery_note_id=db_delivery_note.id,
            product_id=detail.product_id,
            quantity=detail.quantity,
            unit_price=detail.unit_price,
            amount=amount,
            remarks=detail.remarks
        )
        db.add(db_detail)
    db.commit()

    # Refresh to get details
    db.refresh(db_delivery_note)
    return db_delivery_note

@router.get("/{delivery_note_id}", response_model=DeliveryNoteResponse)
async def get_delivery_note(delivery_note_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    delivery_note = db.query(DeliveryNote).filter(DeliveryNote.id == delivery_note_id).first()
    if delivery_note is None:
        raise HTTPException(status_code=404, detail="Delivery note not found")
    return delivery_note

@router.put("/{delivery_note_id}", response_model=DeliveryNoteResponse)
async def update_delivery_note(delivery_note_id: int, delivery_note: DeliveryNoteCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_delivery_note = db.query(DeliveryNote).filter(DeliveryNote.id == delivery_note_id).first()
    if db_delivery_note is None:
        raise HTTPException(status_code=404, detail="Delivery note not found")

    # Update delivery note
    for key, value in delivery_note.dict(exclude={'details'}).items():
        setattr(db_delivery_note, key, value)

    # Delete existing details
    db.query(DeliveryNoteDetail).filter(DeliveryNoteDetail.delivery_note_id == delivery_note_id).delete()

    # Create new details
    for detail in delivery_note.details:
        amount = detail.quantity * detail.unit_price
        db_detail = DeliveryNoteDetail(
            delivery_note_id=delivery_note_id,
            product_id=detail.product_id,
            quantity=detail.quantity,
            unit_price=detail.unit_price,
            amount=amount,
            remarks=detail.remarks
        )
        db.add(db_detail)

    db.commit()
    db.refresh(db_delivery_note)
    return db_delivery_note

@router.delete("/{delivery_note_id}")
async def delete_delivery_note(delivery_note_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    db_delivery_note = db.query(DeliveryNote).filter(DeliveryNote.id == delivery_note_id).first()
    if db_delivery_note is None:
        raise HTTPException(status_code=404, detail="Delivery note not found")
    
    # Delete all details first with synchronize_session
    db.query(DeliveryNoteDetail).filter(
        DeliveryNoteDetail.delivery_note_id == delivery_note_id
    ).delete(synchronize_session=False)
    
    # Delete the delivery note
    db.delete(db_delivery_note)
    db.commit()
    return {"message": "Delivery note deleted"}

# Image upload and recognition
@router.post("/recognize-image")
async def recognize_image(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """画像をアップロードしてGemini APIで認識"""
    print(f"Received file: {file.filename}, size: {file.size}")
    
    # Save uploaded file
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"File saved to: {file_path}")
        
        # GenAIで画像認識
        recognition_result = recognize_delivery_note_image(file_path, db)

        # 認識結果のみを返す（DB登録はフロントエンドから明示的に行う）
        return {
            "file_path": file_path,
            "recognition_result": recognition_result
        }
        
    except Exception as e:
        print(f"Error in recognize_image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"画像処理エラー: {str(e)}")

# Legacy endpoint (deprecated)
@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...), current_user = Depends(get_current_user)):
    # Save uploaded file
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {"file_path": file_path, "message": "Image uploaded successfully. Use /recognize-image for OCR."}