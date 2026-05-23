"""
auth.py — аутентификация: определяем, КТО делает запрос.

АУТЕНТИФИКАЦИЯ vs АВТОРИЗАЦИЯ:
- Аутентификация: "Ты кто?" — проверяем, что пользователь тот, за кого себя выдаёт
- Авторизация: "Тебе можно?" — проверяем, есть ли у него права на действие

Этот файл отвечает за АУТЕНТИФИКАЦИЮ:
1. Достаём JWT-токен из заголовка Authorization: Bearer <token>
2. Расшифровываем токен, получаем user_id
3. Проверяем, что токен не в чёрном списке (после logout)
4. Проверяем, что пользователь существует и активен
5. Возвращаем объект пользователя

Используется как зависимость (Depends) в роутах FastAPI.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import read_data, find_by_id
from app.security import decode_access_token

# HTTPBearer — это класс, который автоматически достаёт токен
# из заголовка "Authorization: Bearer <token>"
security_scheme = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)) -> dict:
    """
    Зависимость FastAPI: получает текущего пользователя из JWT-токена.
    
    Как работает:
    1. FastAPI автоматически вызывает HTTPBearer, который достаёт токен из заголовка
    2. Расшифровываем токен → получаем user_id
    3. Проверяем, что токен не в чёрном списке (logout)
    4. Находим пользователя в "базе"
    5. Проверяем, что он активен (не удалён)
    
    Если что-то не так — выбрасываем ошибку 401 (Unauthorized).
    """
    token = credentials.credentials
    
    # 1. Расшифровываем токен
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Токен недействителен или просрочен"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Некорректный токен"
        )
    
    # 2. Проверяем, что токен не в чёрном списке (пользователь не делал logout)
    blacklisted = read_data("sessions.json")
    for item in blacklisted:
        if item.get("token") == token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Токен отозван (выполнен logout)"
            )
    
    # 3. Находим пользователя
    user = find_by_id("users.json", user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден"
        )
    
    # 4. Проверяем, что пользователь активен
    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Аккаунт удалён"
        )
    
    return user
