from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from database import get_db
from models import UserModel

load_dotenv()

SECRET_KEY=os.getenv("SECRET_KEY")
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

security=HTTPBearer()

# --- PYDANTIC SCHEMAS (DTOs) ---
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str

# --- TOKEN GENERATION ---
def create_access_token(data: dict)->str:
    to_encode=data.copy()
    expire=datetime.utcnow()+timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    encoded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

# --- AUTHENTICATION DEPENDENCY ---
def get_current_user(
        credentials: HTTPAuthorizationCredentials=Depends(security),
        db: Session=Depends(get_db),
)->UserModel:
    token=credentials.credentials
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=ALGORITHM)
        username: str=payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: missing subject identifier.",
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired. Please log in again.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
        )

    # Query the user in our SQLite database
    user=db.query(UserModel).filter(UserModel.username==username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists in database.",
        )
    return user

# --- AUTHORIZATION (ROLE-BASED ACCESS CONTROL) FACTORY ---
def require_role(allowed_roles: list[str]):
    def role_checker(current_user: UserModel=Depends(get_current_user))->UserModel:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires one of roles {allowed_roles}, but your role is '{current_user.role}'.",
            )
        return current_user
    return role_checker