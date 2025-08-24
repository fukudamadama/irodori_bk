# routers/pos.py  —— 認可ヘッダなし（デモ用）
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
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

# ======= Schemas (整数円) =======
class ExecuteRequest(BaseModel):
    user_id: int = Field(..., ge=1)
    amount: conint(ge=0, le=999_999_999_999)

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

class TxSummary(BaseModel):
    id: int
    user_id: int
    amount_paid: int
    tanabota_total: int
    created_at: str

class TxDetail(TxSummary):
    executions: List[ExecutionItem] = []

# ======= Core API =======
@router.post("/execute", response_model=ExecuteResponse, summary="POS決済の処理（日本円・整数）")
def execute(request: ExecuteRequest, db: Session = Depends(get_db)):
    user = db.get(User, request.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")

    try:
        tx, logs = execute_pos_payment(
            db,
            user_id=request.user_id,
            amount_paid=int(request.amount),
        )
        db.commit()
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"internal error: {e}")

    return ExecuteResponse(
        transaction_id=tx.id,
        amount_paid=int(tx.amount_paid),
        tanabota_total=int(tx.tanabota_total),
        executions=[
            ExecutionItem(
                rule_id=l.rule_id,
                action_id=l.action_id,
                action_type=l.action_type,
                tanabota_amount=int(l.tanabota_amount),
            ) for l in logs
        ],
    )

# ======= Read APIs =======
@router.get("/transactions/{transaction_id}", response_model=TxDetail, summary="取引詳細を取得")
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    tx = db.get(TanabotaTransaction, transaction_id)
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="transaction not found")
    logs = db.query(TanabotaActionLog).filter_by(transaction_id=tx.id).all()
    return TxDetail(
        id=tx.id,
        user_id=tx.user_id,
        amount_paid=int(tx.amount_paid),
        tanabota_total=int(tx.tanabota_total),
        created_at=tx.created_at.isoformat() if getattr(tx, "created_at", None) else "",
        executions=[
            ExecutionItem(
                rule_id=l.rule_id,
                action_id=l.action_id,
                action_type=l.action_type,
                tanabota_amount=int(l.tanabota_amount),
            ) for l in logs
        ],
    )

@router.get("/transactions", response_model=List[TxSummary], summary="ユーザーの取引一覧")
def list_transactions(
    user_id: int = Query(..., ge=1),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = (
        select(TanabotaTransaction)
        .where(TanabotaTransaction.user_id == user_id)
        .order_by(TanabotaTransaction.id.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = db.execute(q).scalars().all()
    return [
        TxSummary(
            id=tx.id,
            user_id=tx.user_id,
            amount_paid=int(tx.amount_paid),
            tanabota_total=int(tx.tanabota_total),
            created_at=tx.created_at.isoformat() if getattr(tx, "created_at", None) else "",
        ) for tx in rows
    ]

@router.get("/health", summary="POS API ヘルスチェック")
def health():
    return {"ok": True}
