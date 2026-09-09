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
        w_clean = wallet_address.strip().lower()
        query = query.filter(
            (Transaction.from_address.ilike(w_clean))
            | (Transaction.to_address.ilike(w_clean))
        )
        res = query.order_by(Transaction.timestamp.desc()).offset(skip).limit(limit).all()
        if not res:
            # On-demand transaction fetch and persistence for searched wallet
            from datetime import datetime
            from app.services.blockchain_client import fetch_wallet_transactions
            raw_txs = fetch_wallet_transactions(w_clean, limit=limit)
            for tx_item in raw_txs:
                t_hash = tx_item.get("tx_hash")
                if not t_hash:
                    continue
                existing_tx = db.query(Transaction).filter(Transaction.tx_hash == t_hash).first()
                if not existing_tx:
                    ts_val = tx_item.get("timestamp")
                    if isinstance(ts_val, (int, float)):
                        ts_dt = datetime.utcfromtimestamp(ts_val)
                    elif isinstance(ts_val, str):
                        try:
                            ts_dt = datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                        except Exception:
                            ts_dt = datetime.utcnow()
                    else:
                        ts_dt = datetime.utcnow()

                    db.add(
                        Transaction(
                            tx_hash=t_hash,
                            from_address=str(tx_item.get("from_address") or tx_item.get("from") or w_clean).lower().strip(),
                            to_address=str(tx_item.get("to_address") or tx_item.get("to") or "").lower().strip(),
                            amount=float(tx_item.get("amount", 0.0) or 0.0),
                            token_symbol=str(tx_item.get("token_symbol") or tx_item.get("token") or "ETH"),
                            chain=str(tx_item.get("chain") or "ethereum"),
                            block_number=tx_item.get("block_number"),
                            timestamp=ts_dt,
                        )
                    )
            db.commit()
            res = query.order_by(Transaction.timestamp.desc()).offset(skip).limit(limit).all()
        return res
    return query.order_by(Transaction.timestamp.desc()).offset(skip).limit(limit).all()
