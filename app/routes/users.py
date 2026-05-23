"""
routes/users.py — роуты для работы с пользователями.

Что здесь есть:
1. POST /users/register — регистрация нового пользователя
2. POST /users/login — вход в систему (получить JWT-токен)
3. POST /users/logout — выход из системы (токен в чёрный список)
4. GET /users/me — посмотреть свой профиль
5. PUT /users/me — обновить свой профиль
6. DELETE /users/me — мягкое удаление аккаунта (is_active=False)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime
import uuid

from app.models import UserRegister, UserLogin, UserUpdate, UserResponse, TokenResponse, MessageResponse
from app.database import read_data, write_data, find_one, find_by_id
from app.security import hash_password, verify_password, create_access_token
from app.auth import get_current_user

router = APIRouter(prefix="/users", tags=["Пользователи"])

# Нужен для получения сырого токена в logout
bearer_scheme = HTTPBearer()


@router.post("/register", response_model=UserResponse)
def register(user_data: UserRegister):
    """
    Регистрация нового пользователя.
    
    Шаги:
    1. Проверяем, что пароли совпадают
    2. Проверяем, что email ещё не занят
    3. Хешируем пароль
    4. Сохраняем пользователя в "базу"
    5. Возвращаем данные пользователя (без пароля!)
    """
    # 1. Проверка паролей
    if user_data.password != user_data.password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пароли не совпадают"
        )
    
    # 2. Проверка, что email свободен
    existing = find_one("users.json", email=user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким email уже существует"
        )
    
    # 3. Создаём пользователя
    new_user = {
        "id": f"user-{uuid.uuid4().hex[:8]}",  # уникальный ID
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "patronymic": user_data.patronymic,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),  # пароль в хеше!
        "role_id": "role-user",  # по умолчанию — обычный пользователь
        "is_active": True,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # 4. Сохраняем в "базу"
    users = read_data("users.json")
    users.append(new_user)
    write_data("users.json", users)
    
    # 5. Возвращаем без пароля
    return UserResponse(
        id=new_user["id"],
        first_name=new_user["first_name"],
        last_name=new_user["last_name"],
        patronymic=new_user["patronymic"],
        email=new_user["email"],
        role_id=new_user["role_id"],
        is_active=new_user["is_active"],
        created_at=new_user["created_at"]
    )


@router.post("/login", response_model=TokenResponse)
def login(login_data: UserLogin):
    """
    Вход в систему — получить JWT-токен.
    
    Шаги:
    1. Находим пользователя по email
    2. Проверяем, что аккаунт активен
    3. Проверяем пароль
    4. Создаём JWT-токен
    5. Возвращаем токен
    """
    # 1. Ищем пользователя
    user = find_one("users.json", email=login_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    # 2. Проверяем, что аккаунт активен
    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Аккаунт удалён"
        )
    
    # 3. Проверяем пароль
    if not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )
    
    # 4. Создаём токен
    token = create_access_token(user["id"])
    
    # 5. Возвращаем
    return TokenResponse(access_token=token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: dict = Depends(get_current_user)
):
    """
    Выход из системы.
    
    Добавляем текущий JWT-токен в чёрный список (sessions.json).
    После этого токен перестанет работать, даже если срок его действия не истёк.
    
    Зачем нужен чёрный список?
    JWT-токен — самодостаточный, сервер не хранит состояние сессии.
    Поэтому, чтобы "разлогинить" пользователя, нужно куда-то записать,
    что этот конкретный токен больше не принимается.
    """
    token = credentials.credentials
    
    # Добавляем токен в чёрный список
    sessions = read_data("sessions.json")
    sessions.append({
        "token": token,
        "user_id": current_user["id"],
        "logout_at": datetime.utcnow().isoformat()
    })
    write_data("sessions.json", sessions)
    
    return MessageResponse(message="Вы вышли из системы")


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: dict = Depends(get_current_user)):
    """
    Посмотреть свой профиль.
    
    Требует авторизации (JWT-токен в заголовке Authorization: Bearer <token>).
    """
    return UserResponse(
        id=current_user["id"],
        first_name=current_user["first_name"],
        last_name=current_user.get("last_name"),
        patronymic=current_user.get("patronymic"),
        email=current_user["email"],
        role_id=current_user["role_id"],
        is_active=current_user["is_active"],
        created_at=current_user["created_at"]
    )


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Обновить свой профиль.
    
    Можно изменить: имя, фамилию, отчество, email.
    Пароль и роль менять здесь нельзя (роль — через админа).
    """
    users = read_data("users.json")
    
    # Если пользователь хочет сменить email — проверяем, не занят ли он
    if update_data.email and update_data.email != current_user["email"]:
        existing = find_one("users.json", email=update_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Этот email уже занят"
            )
    
    # Обновляем только переданные поля
    updated_user = None
    for user in users:
        if user["id"] == current_user["id"]:
            if update_data.first_name is not None:
                user["first_name"] = update_data.first_name
            if update_data.last_name is not None:
                user["last_name"] = update_data.last_name
            if update_data.patronymic is not None:
                user["patronymic"] = update_data.patronymic
            if update_data.email is not None:
                user["email"] = update_data.email
            updated_user = user
            break
    
    write_data("users.json", users)
    
    return UserResponse(
        id=updated_user["id"],
        first_name=updated_user["first_name"],
        last_name=updated_user.get("last_name"),
        patronymic=updated_user.get("patronymic"),
        email=updated_user["email"],
        role_id=updated_user["role_id"],
        is_active=updated_user["is_active"],
        created_at=updated_user["created_at"]
    )


@router.delete("/me", response_model=MessageResponse)
def delete_my_account(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: dict = Depends(get_current_user)
):
    """
    Мягкое удаление аккаунта.
    
    Что происходит:
    1. Ставим is_active=False (не удаляем из базы!)
    2. Добавляем токен в чёрный список (автоматический logout)
    3. Пользователь больше не может залогиниться
    
    Почему "мягкое"? Потому что данные остаются в базе.
    Это нужно, чтобы можно было восстановить аккаунт или
    сохранить историю действий пользователя.
    """
    users = read_data("users.json")
    
    # Ставим is_active=False
    for user in users:
        if user["id"] == current_user["id"]:
            user["is_active"] = False
            break
    
    write_data("users.json", users)
    
    # Добавляем токен в чёрный список (logout)
    token = credentials.credentials
    sessions = read_data("sessions.json")
    sessions.append({
        "token": token,
        "user_id": current_user["id"],
        "logout_at": datetime.utcnow().isoformat()
    })
    write_data("sessions.json", sessions)
    
    return MessageResponse(message="Аккаунт удалён (мягкое удаление)")
