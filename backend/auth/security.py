from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
SECRET_KEY='change-me-local-secret'; ALGORITHM='HS256'; pwd_context=CryptContext(schemes=['bcrypt'], deprecated='auto')
def hash_password(password:str)->str: return pwd_context.hash(password)
def verify_password(password:str, hashed:str)->bool: return pwd_context.verify(password, hashed)
def create_access_token(subject:str, minutes:int=480)->str:
    return jwt.encode({'sub':subject,'exp':datetime.now(timezone.utc)+timedelta(minutes=minutes)}, SECRET_KEY, algorithm=ALGORITHM)
