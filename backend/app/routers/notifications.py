from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.schemas.notification import TestEmailRequest
from app.services import email_service
from app.core.config import settings

router = APIRouter(
    tags=["Notifications"]
)

@router.post("/test-email")
def send_test_email(request: TestEmailRequest, db: Session = Depends(get_db)):
    """
    Sends a test email to the specified recipient to verify SMTP settings.
    Requires database session (authentication/RBAC mock via deps).
    """
    if not settings.ENABLE_EMAIL_NOTIFICATIONS:
        raise HTTPException(status_code=400, detail="Email notifications are disabled.")

    success = email_service.send_test_email(request.recipient)
    
    if success:
        return {"status": "SENT", "recipient": request.recipient}
    else:
        # We don't return the exact SMTP error to avoid exposing credentials.
        raise HTTPException(status_code=500, detail="FAILED to send email. Check server logs.")
