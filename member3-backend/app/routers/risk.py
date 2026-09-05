from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.risk import RiskScore, SuspiciousPattern
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.risk import RiskCalculateRequest, RiskScoreOut, SuspiciousPatternOut
from app.services.graph_client import get_wallet_graph
from app.services.risk_client import calculate_risk

router = APIRouter(prefix="/risk", tags=["Risk Engine"])


@router.post("/calculate", response_model=RiskScoreOut, status_code=201)
def compute_risk(
    payload: RiskCalculateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Orchestrates the pipeline: pulls graph context from Member 1's module,
    passes it to Member 4's risk model, then persists + caches the result
    on the wallet row for fast dashboard sorting.
    """
    wallet = db.query(Wallet).filter(Wallet.address == payload.wallet_address).first()
    if not wallet:
        wallet = Wallet(address=payload.wallet_address)
        db.add(wallet)
        db.commit()
        db.refresh(wallet)

    graph_data = get_wallet_graph(payload.wallet_address)
    result = calculate_risk(payload.wallet_address, graph_data)

    risk_score = RiskScore(
        wallet_id=wallet.id,
        score=result["score"],
        risk_level=result["risk_level"],
        reasons=result["reasons"],
        model_version=result.get("model_version", "unknown"),
    )
    db.add(risk_score)

    # Persist any suspicious patterns the graph module surfaced
    for pattern in graph_data.get("patterns", []):
        db.add(
            SuspiciousPattern(
                wallet_id=wallet.id,
                pattern_type=pattern.get("pattern_type", "UNKNOWN"),
                description=pattern.get("description"),
                related_addresses=pattern.get("related_addresses", []),
                severity=pattern.get("severity", "MEDIUM"),
            )
        )

    # Cache latest values on the wallet for fast list/search/sort
    wallet.latest_risk_score = result["score"]
    wallet.latest_risk_level = result["risk_level"]
    wallet.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(risk_score)
    return risk_score


@router.get("/{wallet_address}", response_model=list[RiskScoreOut])
def get_risk_history(
    wallet_address: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = db.query(Wallet).filter(Wallet.address == wallet_address).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    return (
        db.query(RiskScore)
        .filter(RiskScore.wallet_id == wallet.id)
        .order_by(RiskScore.created_at.desc())
        .all()
    )


@router.get("/{wallet_address}/patterns", response_model=list[SuspiciousPatternOut])
def get_patterns(
    wallet_address: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = db.query(Wallet).filter(Wallet.address == wallet_address).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    return (
        db.query(SuspiciousPattern)
        .filter(SuspiciousPattern.wallet_id == wallet.id)
        .order_by(SuspiciousPattern.detected_at.desc())
        .all()
    )
