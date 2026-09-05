from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionBulkCreate, TransactionOut

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post("/bulk", status_code=201)
def bulk_ingest(
    payload: TransactionBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ingestion endpoint for Member 2's cleaned blockchain data pipeline.
    Skips duplicates by tx_hash so the pipeline can be re-run safely.
    """
    inserted = 0
    for tx in payload.transactions:
        existing = db.query(Transaction).filter(Transaction.tx_hash == tx.tx_hash).first()
        if existing:
            continue
        db.add(Transaction(**tx.model_dump()))
        inserted += 1

    db.commit()
    return {"inserted": inserted, "skipped": len(payload.transactions) - inserted}


@router.get("", response_model=list[TransactionOut])
def list_transactions(
    wallet_address: str | None = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Transaction)
    if wallet_address:
        query = query.filter(
            (Transaction.from_address == wallet_address)
            | (Transaction.to_address == wallet_address)
        )
    return query.order_by(Transaction.timestamp.desc()).offset(skip).limit(limit).all()
