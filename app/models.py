"""
models.py — Pydantic-модели для валидации входящих и исходящих данных.
Pydantic — библиотека, которая автоматически проверяет
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ========== Модели для пользователей ==========

class UserRegister(BaseModel):
    """Данные для регистрации нового пользователя."""
    first_name: str
    last_name: Optional[str] = None
    patronymic: Optional[str] = None  # отчество
    email: str
    password: str
    password_confirm: str  # повтор пароля для проверки


class UserLogin(BaseModel):
    """Данные для входа в систему."""
    email: str
    password: str


class UserUpdate(BaseModel):
    """Данные для обновления профиля (всё опционально — можно обновить только имя)."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    patronymic: Optional[str] = None
    email: Optional[str] = None


class UserResponse(BaseModel):
    """Как выглядит пользователь в ответе API (без пароля!)."""
    id: str
    first_name: str
    last_name: Optional[str] = None
    patronymic: Optional[str] = None
    email: str
    role_id: str
    is_active: bool
    created_at: str


# ========== Модели для ролей ==========

class RoleCreate(BaseModel):
    """Создание новой роли."""
    name: str
    description: Optional[str] = None
    permission_ids: list[str] = []


class RoleUpdate(BaseModel):
    """Обновление роли."""
    name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[list[str]] = None


class RoleResponse(BaseModel):
    """Как выглядит роль в ответе API."""
    id: str
    name: str
    description: Optional[str] = None
    permission_ids: list[str] = []


# ========== Модели для разрешений ==========

class PermissionResponse(BaseModel):
    """Как выглядит разрешение в ответе API."""
    id: str
    resource: str
    action: str
    description: Optional[str] = None


class RolePermissionsUpdate(BaseModel):
    """Обновление списка разрешений у роли."""
    permission_ids: list[str]


# ========== Модели для ответов ==========

class TokenResponse(BaseModel):
    """Ответ при успешном логине — JWT-токен."""
    access_token: str
    token_type: str = "bearer"


class MessageResponse(BaseModel):
    """Простой ответ с сообщением."""
    message: str
