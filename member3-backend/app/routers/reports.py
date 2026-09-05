import os
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.report import Report
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.report import ReportOut, ReportRequest

router = APIRouter(prefix="/reports", tags=["Reports"])

REPORTS_DIR = "generated_reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


def _generate_report_file(report_id: uuid.UUID, wallet_address: str, db_url: str):
    """
    Background job that would call Member 6's report-generation module
    (e.g. a function that builds a PDF with reportlab/weasyprint using the
    wallet's graph, risk score and VASP attribution). Left as a placeholder
    so Member 6 can drop in their real generator here.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        report = session.query(Report).filter(Report.id == report_id).first()
        if not report:
            return

        # --- TODO (Member 6): replace this stub with real PDF generation ---
        file_path = os.path.join(REPORTS_DIR, f"{wallet_address}_{report_id}.txt")
        with open(file_path, "w") as f:
            f.write(f"Investigation Report for {wallet_address}\n")
            f.write("This is a placeholder. Plug in the real PDF generator here.\n")
        # ---------------------------------------------------------------------

        report.file_path = file_path
        report.status = "READY"
        report.completed_at = datetime.utcnow()
        session.commit()
    finally:
        session.close()


@router.post("/generate", response_model=ReportOut, status_code=202)
def generate_report(
    payload: ReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    wallet = db.query(Wallet).filter(Wallet.address == payload.wallet_address).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")

    report = Report(wallet_id=wallet.id, status="GENERATING", generated_by=current_user.id)
    db.add(report)
    db.commit()
    db.refresh(report)

    from app.config import settings

    background_tasks.add_task(
        _generate_report_file, report.id, wallet.address, settings.DATABASE_URL
    )
    return report


@router.get("/{report_id}", response_model=ReportOut)
def get_report_status(
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/download")
def download_report(
    report_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report or report.status != "READY" or not report.file_path:
        raise HTTPException(status_code=404, detail="Report not ready or not found")
    return FileResponse(report.file_path, filename=os.path.basename(report.file_path))
