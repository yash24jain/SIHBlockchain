import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.wallet import WalletCreate, WalletOut, WalletSearchResult

router = APIRouter(prefix="/wallets", tags=["Wallets"])


@router.post("", response_model=WalletOut, status_code=201)
def create_wallet(
    payload: WalletCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.query(Wallet).filter(Wallet.address == payload.address).first()
    if existing:
        return existing

    wallet = Wallet(address=payload.address, chain=payload.chain, label=payload.label)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet


@router.get("", response_model=WalletSearchResult)
def list_wallets(
    q: str | None = Query(None, description="Search by address or label"),
    risk_level: str | None = Query(None, description="Filter by LOW/MEDIUM/HIGH/CRITICAL"),
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Wallet)
    if q:
        query = query.filter(
            (Wallet.address.ilike(f"%{q}%")) | (Wallet.label.ilike(f"%{q}%"))
        )
    if risk_level:
        query = query.filter(Wallet.latest_risk_level == risk_level.upper())

    total = query.count()
    wallets = query.offset(skip).limit(limit).all()
    return WalletSearchResult(wallets=wallets, total=total)


@router.get("/{wallet_address}", response_model=WalletOut)
def get_wallet(
    wallet_address: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = db.query(Wallet).filter(Wallet.address == wallet_address).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet


@router.delete("/{wallet_id}", status_code=204)
def delete_wallet(
    wallet_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = db.query(Wallet).filter(Wallet.id == wallet_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    db.delete(wallet)
    db.commit()
