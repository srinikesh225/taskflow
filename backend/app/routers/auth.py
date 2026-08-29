"""Authentication routes: register, login, and current-user lookup."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..ratelimit import login_rate_limiter
from ..schemas import Token, UserCreate, UserOut
from ..security import create_access_token, hash_password, verify_password

logger = logging.getLogger("taskflow.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])

# A fixed hash used to burn ~equal CPU when the account doesn't exist, so login
# timing doesn't reveal whether an email is registered (user enumeration).
_DUMMY_HASH = hash_password("dummy-password-for-constant-time")


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    email = payload.email.lower().strip()
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(email=email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("user registered", extra={"user_id": user.id})
    return user


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    client_ip = request.client.host if request.client else "unknown"
    if not login_rate_limiter.is_allowed(client_ip):
        logger.warning("login rate limit exceeded", extra={"ip": client_ip})
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )

    # OAuth2 form uses "username"; we treat it as the email.
    email = form_data.username.lower().strip()
    user = db.scalar(select(User).where(User.email == email))

    # Verify against the real hash if the user exists, otherwise against a dummy
    # hash — so response timing doesn't reveal whether the email is registered.
    hashed = user.hashed_password if user is not None else _DUMMY_HASH
    password_ok = verify_password(form_data.password, hashed)

    if user is None or not password_ok or not user.is_active:
        login_rate_limiter.record(client_ip)
        logger.warning("failed login attempt", extra={"email": email, "ip": client_ip})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(subject=str(user.id))
    logger.info("user logged in", extra={"user_id": user.id})
    return Token(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
