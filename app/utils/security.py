from fastapi.security import OAuth2PasswordBearer
from app.config import get_settings
from passlib.context import CryptContext

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=getattr(settings, "APP_PREFIX", "") + "/auth/login"
)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
