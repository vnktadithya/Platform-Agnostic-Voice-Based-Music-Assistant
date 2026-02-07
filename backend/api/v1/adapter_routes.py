from fastapi import APIRouter, Query, HTTPException, Depends, Response, Cookie, Request
from fastapi.responses import RedirectResponse
import logging
import os
from typing import Optional
from backend.adapters.spotify_adapter import SpotifyAdapter
from backend.adapters.soundcloud_adapter import SoundCloudAdapter
from backend.models.database_models import PlatformAccount, SystemUser
from backend.services.data_sync_service import sync_spotify_library, sync_soundcloud_library
from backend.configurations.database import get_db
from backend.utils.feature_flags import is_soundcloud_enabled
from sqlalchemy.orm import Session
from backend.utils.encryption import encrypt_token


router = APIRouter(tags=["Adapter"])

@router.get("/adapter/{platform}/status")
def get_platform_status(
    platform: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Checks if the platform is connected and (for Spotify) if a device is available.
    """
    platform = platform.lower().strip()
    account_id = request.query_params.get("platform_account_id")
    if not account_id:
        account_id = request.session.get(f"{platform}_account_id")
        
    if not account_id:
        return {"is_connected": False, "reason": "No account ID"}

    account = db.query(PlatformAccount).filter_by(id=account_id).first()
    if not account:
        return {"is_connected": False, "reason": "Account not found"}

    if platform == "spotify":
        from backend.services.data_sync_service import get_valid_spotify_access_token
        try:
             token = get_valid_spotify_access_token(db, account)
             if not token:
                 return {"is_connected": False, "reason": "Token refresh failed"}
             
             adapter = SpotifyAdapter(token)
             device = adapter.get_active_device()
             
             # Return True if ANY device is found. 
             return {
                 "is_connected": True, 
                 "has_active_device": bool(device),
                 "device": device,
                 "account_id": account.id,
                 "user_id": account.system_user_id
             }
        except Exception as e:
            return {"is_connected": False, "reason": str(e)}

    elif platform == "soundcloud":
        # SoundCloud doesn't have "devices"
        
        # FIX: Check if we actually have a valid token (it might have been wiped on error)
        if not account.refresh_token:
             return {"is_connected": False, "reason": "Authorization expired"}

        return {
            "is_connected": True, 
            "has_active_device": True,
            "account_id": account.id,
            "user_id": account.system_user_id
        }

    return {"is_connected": False, "reason": "Unsupported platform"}

#------------------------------------------------- SPOTIFY -------------------------------------------------------

@router.get("/adapter/spotify/login")
def spotify_login():
    """Returns the Spotify OAuth URL for user sign-in."""
    try:
        auth_url = SpotifyAdapter.get_auth_url()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not generate auth URL: {e}")

@router.get("/adapter/spotify/callback")
def spotify_callback(request: Request, code: str = Query(...), db: Session = Depends(get_db)):
    try:
        data = SpotifyAdapter.handle_auth_callback(code)

        user_data = data["user"]
        tokens = data["tokens"]

        platform_user_id = user_data["id"]
        email = user_data.get("email")
        display_name = user_data.get("name")

        # Check for existing PlatformAccount first
        account = (
            db.query(PlatformAccount)
            .filter_by(
                platform_name="spotify",
                platform_user_id=platform_user_id
            )
            .first()
        )

        system_user = None

        if account:
            # Use existing user
            system_user = account.owner
            
            # Update metadata
            account.refresh_token = encrypt_token(tokens["refresh_token"]) or account.refresh_token
            account.meta_data = {
                "access_token": encrypt_token(tokens["access_token"]),
                "expires_at": tokens["expires_at"],
                "scope": tokens.get("scope"),
                "token_type": tokens.get("token_type"),
                "display_name": display_name,
                "email": email
            }
        else:
            # No account found, this is a new connection.
            # Try to match by email if we have one.
            if email:
                system_user = db.query(SystemUser).filter_by(email=email).first()

            if not system_user:
                system_user = SystemUser(email=email)
                db.add(system_user)
                db.flush()

            # Create new PlatformAccount linked to this user
            account = PlatformAccount(
                system_user_id=system_user.id,
                platform_name="spotify",
                platform_user_id=platform_user_id,
                refresh_token=encrypt_token(tokens["refresh_token"]),
                meta_data={
                    "access_token": encrypt_token(tokens["access_token"]),
                    "expires_at": tokens["expires_at"],
                    "scope": tokens.get("scope"),
                    "token_type": tokens.get("token_type"),
                    "display_name": display_name,
                    "email": email
                }
            )
            db.add(account)

        db.commit()
        db.refresh(account)

        # SECURE SESSION STORAGE
        request.session["spotify_account_id"] = account.id
        request.session["user_id"] = system_user.id
        logging.info(f"Session updated: spotify_account_id={account.id}, user_id={system_user.id}")

        # Trigger background sync to store user's liked songs and playlists
        sync_spotify_library.delay(account.id)
        
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(
            url=f"{frontend_url}/chat?platform=spotify&account_id={account.id}&user_id={system_user.id}"
        )
    except Exception as e:
        logging.error(f"Spotify Callback Failed: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": f"Spotify Callback Error: {str(e)}"})

    
#------------------------------------------------- SOUNDCLOUD ----------------------------------------------------

@router.get("/adapter/soundcloud/login")
def soundcloud_login():
    if not is_soundcloud_enabled():
        raise HTTPException(
            status_code=503,
            detail="SoundCloud integration implemented but awaiting API credentials"
        )
    
    auth_url, verifier = SoundCloudAdapter.get_auth_url()
    
    # Create the redirect response
    response = RedirectResponse(auth_url)
    
    # Store PKCE verifier in a short-lived HTTP-only cookie
    response.set_cookie(
        key="soundcloud_verifier",
        value=verifier,
        httponly=True,
        max_age=600,  # 10 minutes
        samesite="lax",
        secure=False,  # Allow on localhost dev
        path="/"
    )
    
    return response

@router.get("/adapter/soundcloud/callback")
def soundcloud_callback(
    request: Request,
    code: str = Query(...),
    soundcloud_verifier: str = Cookie(None),
    db: Session = Depends(get_db)
):
    try:
        logging.info(f"SoundCloud Callback Cookies: {request.cookies}")
        if not soundcloud_verifier:
            logging.error("Missing soundcloud_verifier cookie!")
            raise HTTPException(status_code=400, detail="Missing PKCE verifier cookie. Please try logging in again.")

        try:
            data = SoundCloudAdapter.handle_auth_callback(code, soundcloud_verifier)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"SoundCloud authentication failed: {str(e)}")


        # Match existing user by email, or create new SystemUser if none exists.
        
        account = db.query(PlatformAccount).filter_by(
            platform_name="soundcloud", 
            platform_user_id=data["platform_user_id"]
        ).first()

        sc_email = data["meta_data"].get("email")
        # If we have an email from SC, try to find an existing system user
        system_user = None
        if sc_email:
            system_user = db.query(SystemUser).filter_by(email=sc_email).first()

        if account:
             # Update existing account
             account.refresh_token = encrypt_token(data.get("refresh_token"))
             account.meta_data = {
                "access_token": encrypt_token(data["access_token"]),
                **data["meta_data"]
             }
             # If the account's system user is missing email but we have one now, update it
             if account.owner and not account.owner.email and sc_email:
                 account.owner.email = sc_email
                 
             system_user = account.owner
        else:
            # If we didn't find a user by email, create one
            if not system_user:
                system_user = SystemUser(email=sc_email)
                db.add(system_user)
                db.flush()
            
            account = PlatformAccount(
                system_user_id=system_user.id,
                platform_name="soundcloud",
                platform_user_id=data["platform_user_id"],
                refresh_token=encrypt_token(data.get("refresh_token")),
                meta_data={
                    "access_token": encrypt_token(data["access_token"]),
                    **data["meta_data"]
                }
            )
            db.add(account)

        db.commit()
        db.refresh(account)

        # SECURE SESSION STORAGE
        request.session["soundcloud_account_id"] = account.id
        request.session["user_id"] = system_user.id
        logging.info(f"Session updated: soundcloud_account_id={account.id}, user_id={system_user.id}")

        # 2. Trigger Background Sync to store user's liked songs and playlists
        sync_soundcloud_library.delay(account.id)

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(
            url=f"{frontend_url}/chat?platform=soundcloud&account_id={account.id}&user_id={system_user.id}"
        )
    except Exception as e:
        logging.error(f"SoundCloud Callback Failed: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"detail": f"SoundCloud Callback Error: {str(e)}"})
