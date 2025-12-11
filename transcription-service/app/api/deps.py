from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.db.base import get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.token import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token", auto_error=False) # Endpoint relative URL
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    api_key: str = Depends(api_key_header),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user either from JWT Token (Web) or API Key (IDE/Bots).
    """
    # 1. Try API Key first if present
    if api_key:
        user = db.query(User).filter(User.api_key == api_key).first()
        if user:
            return user
        # If API key is provided but invalid, maybe we should fail? 
        # But if both are provided, let's fall back to Token? 
        # For simplicity, if API key is invalid, we fail immediately to warn user.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

    # 2. Try JWT
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
        
    user = db.query(User).filter(User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user
