import os
import sys
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../..'))
from core.config import settings
from fastapi.responses import JSONResponse

ALLOW_PATH = ['/login', '/register', '/api/login', '/api/register', '/', '/api/chat']

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_middleware(app):
    @app.middleware("http")
    async def check_valid_token(request: Request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path in ALLOW_PATH:
            return await call_next(request)

        try:
            token = await oauth2_scheme(request)
        except HTTPException as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid Authorization header"},
                headers=e.headers if hasattr(e, 'headers') else {"WWW-Authenticate": "Bearer"}
            )

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            request.state.user = payload
        except JWTError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token"},
                headers={"WWW-Authenticate": "Bearer"}
            )

        return await call_next(request)
    return app