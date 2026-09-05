from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.models.vasp import VASPAttribution
from app.models.wallet import Wallet
from app.schemas.vasp import VASPAttributionOut
from app.services.vasp_client import attribute_vasp

router = APIRouter(prefix="/vasp", tags=["VASP Attribution"])


@router.post("/attribute/{wallet_address}", response_model=VASPAttributionOut, status_code=201)
def run_attribution(
    wallet_address: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = db.query(Wallet).filter(Wallet.address == wallet_address).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found. Create it first.")

    result = attribute_vasp(wallet_address)
    attribution = VASPAttribution(
        wallet_id=wallet.id,
        vasp_name_guess=result.get("vasp_name_guess"),
        confidence_score=result.get("confidence_score", 0.0),
        evidence=result.get("evidence", []),
    )
    db.add(attribution)
    db.commit()
    db.refresh(attribution)
    return attribution


@router.get("/{wallet_address}", response_model=list[VASPAttributionOut])
def get_attributions(
    wallet_address: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = db.query(Wallet).filter(Wallet.address == wallet_address).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    return (
        db.query(VASPAttribution)
        .filter(VASPAttribution.wallet_id == wallet.id)
        .order_by(VASPAttribution.created_at.desc())
        .all()
    )
