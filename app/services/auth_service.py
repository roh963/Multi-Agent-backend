import uuid
import logging
from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import settings
from app.dependencies.auth import create_access_token
from app.models.user import User
from app.schemas.user import AuthResponse, UserCreate, UserResponse

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# ─── Private Helper ────────────────────────────────────────────────────────────

def _build_auth_response(user: User) -> AuthResponse:
    """
    Token banao + AuthResponse object assemble karo.
    DRY: signup, login, google_callback — teeno mein same kaam tha.
    Ek jagah likhne se ek jagah fix bhi hoga agar kabhi change karna pade.
    """
    token = create_access_token({"sub": str(user.id)})  # ✅ str() add karo
    return AuthResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


# ─── Service Class ─────────────────────────────────────────────────────────────

class AuthService:

    # ── SIGNUP ──────────────────────────────────────────────────────────────────

    def signup(self, db: Session, data: UserCreate) -> AuthResponse:
        """
        Naya user register karo.
        Return: AuthResponse object (dict nahi — router seedha return kar sakta hai)
        """
        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Yeh email already registered hai",
            )

        try:
            user = User(
                id=str(uuid.uuid4()),
                email=data.email,
                name=data.name,
                hashed_password=pwd_context.hash(data.password),
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            logger.info("New user registered: id=%s email=%s", user.id, user.email)
            return _build_auth_response(user)

        except IntegrityError:
            db.rollback()
            logger.warning("Duplicate email race condition: %s", data.email)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Yeh email already registered hai",
            )
        except SQLAlchemyError as exc:
            db.rollback()
            logger.error("Signup DB error: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Account banana mein dikkat aayi, baad mein try karo",
            )

    # ── LOGIN ───────────────────────────────────────────────────────────────────

    def login(self, db: Session, email: str, password: str) -> AuthResponse:
        """
        Email + password verify karo, token return karo.

        Security: "user nahi mila" aur "galat password" — dono ka
        SAME error message — attacker ko email existence pata na chale.
        (User Enumeration Attack rokta hai yeh pattern)
        """
        user = db.query(User).filter(User.email == email).first()

        if not user or not user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ya password galat hai",
            )

        if not pwd_context.verify(password, user.hashed_password):
            logger.warning("Failed login attempt: email=%s", email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ya password galat hai",
            )

        logger.info("User logged in: id=%s", user.id)
        return _build_auth_response(user)

    # ── GOOGLE OAUTH — URL ──────────────────────────────────────────────────────

    def get_google_login_url(self) -> str:
        """
        Google OAuth login URL banao.
        Frontend is URL pe redirect kare → Google login page khulega →
        Google tumhare redirect_uri pe 'code' bhejega.
        """
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    # ── GOOGLE OAUTH — CALLBACK ─────────────────────────────────────────────────

    async def google_callback(self, db: Session, code: str) -> AuthResponse:
        """
        Google ka 'code' → access token → user info → DB upsert → AuthResponse.
        3 private helpers mein split kiya hai — har ek ka ek kaam.
        """
        tokens = await self._exchange_code_for_tokens(code)
        google_user = await self._fetch_google_user_info(tokens["access_token"])

        try:
            user = self._upsert_google_user(db, google_user)
            logger.info("Google OAuth success: google_id=%s", google_user.get("sub"))
            return _build_auth_response(user)
        except SQLAlchemyError as exc:
            db.rollback()
            logger.error("Google callback DB error: %s", exc, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Google login mein dikkat aayi",
            )

    # ── Private: Google Token Exchange ─────────────────────────────────────────

    async def _exchange_code_for_tokens(self, code: str) -> dict:
        """
        Google se authorization code ko access token se exchange karo.
        timeout=10 — agar Google ne 10 sec mein jawab nahi diya toh 504 do.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": code,
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                        "grant_type": "authorization_code",
                    },
                )
                resp.raise_for_status()
                tokens = resp.json()

        except httpx.TimeoutException:
            logger.error("Google token exchange timeout")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Google server ne response nahi diya",
            )
        except httpx.HTTPStatusError as exc:
            logger.error("Google token exchange failed: %s", exc.response.text)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Google se token lena fail hua",
            )

        if "access_token" not in tokens:
            logger.error("Google token response invalid: %s", tokens)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Google ka response invalid hai",
            )

        return tokens

    # ── Private: Google User Info ───────────────────────────────────────────────

    async def _fetch_google_user_info(self, access_token: str) -> dict:
        """Google userinfo endpoint se profile data fetch karo."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    "https://www.googleapis.com/oauth2/v3/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                resp.raise_for_status()
                return resp.json()

        except httpx.TimeoutException:
            logger.error("Google userinfo timeout")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Google user info fetch timeout",
            )
        except httpx.HTTPStatusError as exc:
            logger.error("Google userinfo failed: %s", exc.response.text)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Google user info lena fail hua",
            )

    # ── Private: DB Upsert ──────────────────────────────────────────────────────

    def _upsert_google_user(self, db: Session, google_user: dict) -> User:
        """
        Upsert = Update + Insert.

        Priority order:
        1. google_id se dhundo  → returning Google user
        2. email se dhundo      → pehle manually register kiya tha
        3. Dono nahi mila       → bilkul naya user banao

        Yeh ensure karta hai ki same email ke 2 accounts kabhi na bane.
        """
        google_id = google_user["sub"]

        user = db.query(User).filter(User.google_id == google_id).first()

        if not user:
            user = db.query(User).filter(User.email == google_user["email"]).first()

        if not user:
            user = User(
                id=str(uuid.uuid4()),
                email=google_user["email"],
                name=google_user.get("name"),
                picture=google_user.get("picture"),
                google_id=google_id,
            )
            db.add(user)
            logger.info("Google se naya user create: %s", google_user["email"])
        else:
            user.google_id = google_id
            user.picture = google_user.get("picture")
            logger.info("Existing user Google se login: id=%s", user.id)

        db.commit()
        db.refresh(user)
        return user


# Singleton — ek hi instance, har jagah yahi use hoga
auth_service = AuthService()