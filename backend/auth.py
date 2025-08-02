from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from . import schemas, database
import os
import json
import secrets
import requests
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

# Configurações de segurança
SECRET_KEY = os.getenv("SECRET_KEY", "sua-chave-secreta-muito-segura-aqui-123456789")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db: Session, username: str):
    return db.query(database.Usuario).filter(database.Usuario.username == username).first()

def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sessão expirada ou inválida. Faça login novamente.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        session_token: str = payload.get("session_token")
        if username is None or session_token is None:
            raise credentials_exception
        token_data = schemas.TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    
    # Verifica se a sessão específica do token ainda está ativa
    active_session = db.query(database.UserSession).filter(
        database.UserSession.usuario_id == user.id,
        database.UserSession.session_token == session_token,
        database.UserSession.is_active == True,
        database.UserSession.expires_at > datetime.utcnow()
    ).first()
    
    if not active_session:
        # Limpa sessões expiradas
        cleanup_expired_sessions(db)
        raise credentials_exception
    
    # Atualiza atividade da sessão (renova expiração automaticamente)
    update_session_activity(db, active_session.session_token)
    
    return user

def create_user(db: Session, user: schemas.UsuarioCreate):
    hashed_password = get_password_hash(user.password)
    db_user = database.Usuario(
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_device_info(request: Request) -> dict:
    """Extrai informações do dispositivo a partir do request"""
    user_agent = request.headers.get("user-agent", "")
    
    device_info = {
        "user_agent": user_agent,
        "platform": "Unknown",
        "browser": "Unknown",
        "is_mobile": False
    }
    
    # Detecta plataforma
    if "Windows" in user_agent:
        device_info["platform"] = "Windows"
    elif "Mac" in user_agent:
        device_info["platform"] = "macOS"
    elif "Linux" in user_agent:
        device_info["platform"] = "Linux"
    elif "Android" in user_agent:
        device_info["platform"] = "Android"
        device_info["is_mobile"] = True
    elif "iPhone" in user_agent or "iPad" in user_agent:
        device_info["platform"] = "iOS"
        device_info["is_mobile"] = True
    
    # Detecta navegador
    if "Chrome" in user_agent:
        device_info["browser"] = "Chrome"
    elif "Firefox" in user_agent:
        device_info["browser"] = "Firefox"
    elif "Safari" in user_agent:
        device_info["browser"] = "Safari"
    elif "Edge" in user_agent:
        device_info["browser"] = "Edge"
    
    return device_info

def get_location_from_ip(ip_address: str) -> str:
    """Obtém localização aproximada a partir do IP"""
    try:
        # Usando um serviço gratuito de geolocalização
        response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success":
                city = data.get("city", "")
                region = data.get("regionName", "")
                country = data.get("country", "")
                return f"{city}, {region}, {country}"
    except:
        pass
    return "Localização não disponível"

def create_user_session(db: Session, usuario_id: int, request: Request) -> database.UserSession:
    """Cria uma nova sessão de usuário com informações detalhadas"""
    # IMPORTANTE: Invalida todas as sessões existentes do usuário (sessão única)
    invalidate_all_user_sessions(db, usuario_id)
    
    # Gera token único para a sessão
    session_token = secrets.token_urlsafe(32)
    
    # Obtém IP do cliente
    ip_address = request.client.host if request.client else "127.0.0.1"
    
    # Obtém informações do dispositivo
    device_info = get_device_info(request)
    
    # Obtém localização (opcional)
    location = get_location_from_ip(ip_address)
    
    # Define expiração da sessão (2 horas de inatividade)
    expires_at = datetime.utcnow() + timedelta(hours=2)
    
    # Cria a sessão no banco
    db_session = database.UserSession(
        usuario_id=usuario_id,
        session_token=session_token,
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent", ""),
        device_info=json.dumps(device_info),
        location=location,
        expires_at=expires_at
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session

def update_session_activity(db: Session, session_token: str):
    """Atualiza a última atividade da sessão e renova expiração"""
    session = db.query(database.UserSession).filter(
        database.UserSession.session_token == session_token,
        database.UserSession.is_active == True
    ).first()
    
    if session:
        now = datetime.utcnow()
        session.last_activity = now
        # Renova expiração para mais 2 horas a partir da atividade atual
        session.expires_at = now + timedelta(hours=2)
        db.commit()

def invalidate_user_session(db: Session, session_token: str):
    """Invalida uma sessão específica"""
    session = db.query(database.UserSession).filter(
        database.UserSession.session_token == session_token
    ).first()
    
    if session:
        session.is_active = False
        db.commit()

def invalidate_all_user_sessions(db: Session, usuario_id: int, except_token: str = None):
    """Invalida todas as sessões de um usuário, exceto uma específica"""
    query = db.query(database.UserSession).filter(
        database.UserSession.usuario_id == usuario_id,
        database.UserSession.is_active == True
    )
    
    if except_token:
        query = query.filter(database.UserSession.session_token != except_token)
    
    sessions = query.all()
    for session in sessions:
        session.is_active = False
    
    db.commit()

def cleanup_expired_sessions(db: Session):
    """Remove sessões expiradas"""
    expired_sessions = db.query(database.UserSession).filter(
        database.UserSession.expires_at < datetime.utcnow()
    ).all()
    
    for session in expired_sessions:
        session.is_active = False
    
    db.commit()

def get_user_sessions(db: Session, usuario_id: int) -> list:
    """Obtém todas as sessões ativas de um usuário"""
    sessions = db.query(database.UserSession).filter(
        database.UserSession.usuario_id == usuario_id,
        database.UserSession.is_active == True,
        database.UserSession.expires_at > datetime.utcnow()
    ).order_by(database.UserSession.last_activity.desc()).all()
    
    return sessions