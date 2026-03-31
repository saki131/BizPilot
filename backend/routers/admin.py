from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import SystemSetting, User
from dependencies import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/admin", tags=["admin"])

DEFAULT_GEMINI_MODEL = "gemini-3.1-flash-lite-preview"
DEFAULT_FALLBACK_MODEL = "gemini-2.5-flash"


def get_gemini_models(db: Session) -> dict:
    """DBからGeminiモデル設定を取得する（他ルーターから呼び出し可能）"""
    model_setting = db.query(SystemSetting).filter(SystemSetting.key == "gemini_model").first()
    fallback_setting = db.query(SystemSetting).filter(SystemSetting.key == "gemini_fallback_model").first()
    return {
        "model": model_setting.value if model_setting else DEFAULT_GEMINI_MODEL,
        "fallback_model": fallback_setting.value if fallback_setting else DEFAULT_FALLBACK_MODEL,
    }


class GeminiModelUpdate(BaseModel):
    model: str
    fallback_model: str


@router.get("/settings/gemini-model")
def get_gemini_model_setting(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Geminiモデル設定を取得する（ログインユーザーなら誰でも参照可）"""
    return get_gemini_models(db)


@router.put("/settings/gemini-model")
def update_gemini_model_setting(
    data: GeminiModelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Geminiモデル設定を更新する（adminのみ変更可）"""
    if current_user.username != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者のみが設定を変更できます",
        )

    model_setting = db.query(SystemSetting).filter(SystemSetting.key == "gemini_model").first()
    if model_setting:
        model_setting.value = data.model
    else:
        db.add(SystemSetting(key="gemini_model", value=data.model))

    fallback_setting = db.query(SystemSetting).filter(SystemSetting.key == "gemini_fallback_model").first()
    if fallback_setting:
        fallback_setting.value = data.fallback_model
    else:
        db.add(SystemSetting(key="gemini_fallback_model", value=data.fallback_model))

    db.commit()
    return get_gemini_models(db)
