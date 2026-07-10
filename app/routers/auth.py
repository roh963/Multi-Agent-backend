from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import AuthResponse, UserCreate, UserLogin
from app.services.auth_service import auth_service

from app.config import settings  

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=AuthResponse, status_code=201)
def signup(data: UserCreate, db: Session = Depends(get_db)):
    """
    Naya user register karo.
    auth_service seedha AuthResponse return karta hai — manually wrap karne ki zaroorat nahi.
    status_code=201 — "Created" — REST standard for resource creation.
    """
    return auth_service.signup(db, data)


@router.post("/login", response_model=AuthResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """
    Email + password se login karo, JWT token wapas milega.
    """
    return auth_service.login(db, data.email, data.password)


@router.get("/google/login", include_in_schema=True)
def google_login():
    """
    Google OAuth flow shuru karo.
    Frontend is endpoint ko call kare → Google login page pe redirect ho jaayega.
    """
    url = auth_service.get_google_login_url()
    return RedirectResponse(url=url, status_code=302)


@router.get("/google/callback")          # ← response_model hata diya
async def google_callback(code: str, db: Session = Depends(get_db)):
    """
    Google code → token exchange → frontend pe redirect with token in URL
    """
    result = await auth_service.google_callback(db, code)
    
    frontend_url = getattr(settings, "FRONTEND_URL")
    
    # Token URL mein daal ke frontend pe bhejo
    return RedirectResponse(
        url=f"{frontend_url}/auth/callback?token={result.access_token}",
        status_code=302
    )
