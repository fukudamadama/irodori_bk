# routers/pos.py
from __future__ import annotations
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, conint
from sqlalchemy.orm import Session
from sqlalchemy import select

from database import SessionLocal
from models import User, TanabotaTransaction, TanabotaActionLog
from services.tanabota import execute_pos_payment

router = APIRouter(prefix="/pos", tags=["POS"])

# DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===== Schemas =====
class ExecuteRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    amount: conint(ge=0, le=999_999_999_999)  # JPY integer
    # ← 追加：カテゴリは任意。トリガ 4/12/6 の判定で使う
    category: str | None = Field(
        None, description="支出カテゴリ（例: コンビニ/推し活/食費-ランチ など）"
    )

class ExecutionItem(BaseModel):
    rule_id: int
    action_id: int
    action_type: str
    tanabota_amount: int

class ExecuteResponse(BaseModel):
    transaction_id: int
    amount_paid: int
    tanabota_total: int
    executions: List[ExecutionItem]

# ===== Endpoint =====
@router.post("/execute", response_model=ExecuteResponse)
def execute(req: ExecuteRequest, db: Session = Depends(get_db)) -> ExecuteResponse:
    # ユーザー存在チェック（必要なら）
    user = db.get(User, req.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    tx, logs = execute_pos_payment(
        db,
        user_id=req.user_id,
        amount_paid=int(req.amount),
        category=req.category,   # ← 追加
    )
    # ここでコミットは呼び出し側に任せても良いが、APIならコミットする方が扱いやすい
    db.commit()

    return ExecuteResponse(
        transaction_id=tx.id,
        amount_paid=tx.amount_paid,
        tanabota_total=tx.tanabota_total,
        executions=[
            ExecutionItem(
                rule_id=log.rule_id,
                action_id=log.action_id,
                action_type=log.action_type,
                tanabota_amount=log.tanabota_amount,
            )
            for log in logs
        ],
    )

