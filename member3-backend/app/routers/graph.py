from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.risk import GraphAnalysisOut
from app.services.graph_client import get_wallet_graph

router = APIRouter(prefix="/graph", tags=["Graph Analysis"])


@router.get("/{wallet_address}", response_model=GraphAnalysisOut)
def get_graph(
    wallet_address: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the transaction graph (nodes/edges) and any suspicious flow
    patterns for a wallet, sourced from Member 1's NetworkX module.
    Feeds Member 5's interactive graph visualization directly.
    """
    data = get_wallet_graph(wallet_address)
    return GraphAnalysisOut(**data)
