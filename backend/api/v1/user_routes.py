from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.services.data_sync_service import sync_spotify_library
from backend.models.database_models import SystemUser, PlatformAccount
from backend.configurations.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])

class OnboardRequest(BaseModel):
    platform_name: str
    platform_user_id: str
    refresh_token: str
    
@router.post("/onboard")
def onboard_user(request: OnboardRequest, db: Session = Depends(get_db)):
    """
    Onboards a new user, creates their account in our system,
    and triggers a background sync of their library.
    """
    try:
        # Check if the platform account already exists
        account = db.query(PlatformAccount).filter(
            PlatformAccount.platform_user_id == request.platform_user_id,
            PlatformAccount.platform_name == request.platform_name
        ).first()

        if not account:
            # Create a new system user and platform account
            new_user = SystemUser()
            db.add(new_user)
            db.flush() # Flush to get the new_user.id

            account = PlatformAccount(
                system_user_id=new_user.id,
                platform_name=request.platform_name,
                platform_user_id=request.platform_user_id,
                refresh_token=request.refresh_token
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            
            # Trigger the background sync task for the new account
            sync_spotify_library.delay(account.id)
            message = "User onboarded successfully. Library synchronization has started in the background."
        else:
            message = "User already exists. Triggering a library refresh."
            # Trigger a sync here for returning users
            sync_spotify_library.delay(account.id)

        return {"status": "success", "message": message, "platform_account_id": account.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to onboard user: {e}")
        