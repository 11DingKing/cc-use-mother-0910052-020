"""业务模块说明。"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.services.auth_service import (
    authenticate_user, create_token, verify_token, remove_token
)

router = APIRouter(prefix="/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    token: Optional[str] = None
    username: Optional[str] = None
    message: str


def get_current_user(authorization: str = Header(None)):
    """业务模块说明。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization[7:]
    user_data = verify_token(token)
    if not user_data:
        raise HTTPException(status_code=401, detail="登录已过期")
    return user_data


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """业务模块说明。"""
    user = authenticate_user(db, req.username, req.password)
    if not user:
        return LoginResponse(success=False, message="用户名或密码错误")
    
    # 更新最后登录时间
    user.last_login = datetime.now()
    db.commit()
    
    token = create_token(user.id, user.username)
    return LoginResponse(
        success=True,
        token=token,
        username=user.username,
        message="登录成功"
    )


@router.post("/logout")
def logout(authorization: str = Header(None)):
    """业务模块说明。"""
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
        remove_token(token)
    return {"success": True, "message": "已登出"}


@router.get("/check")
def check_auth(user: dict = Depends(get_current_user)):
    """业务模块说明。"""
    return {
        "success": True,
        "username": user["username"]
    }
