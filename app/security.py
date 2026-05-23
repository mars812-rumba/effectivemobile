"""
security.py — безопасность: хеширование паролей и JWT-токены.

ДВА ГЛАВНЫХ ВОПРОСА:
1. Как хранить пароли? — В хеше. Никогда не храним пароль как есть!
2. Как пользователь доказывает, кто он? — Через JWT-токен.

--- ПРО ПАРОЛИ ---
Мы НЕ используем bcrypt/scrypt/passlib. Вместо этого берём встроенный
модуль hashlib (есть в Python из коробки) и делаем SHA-256 с солью.

Соль (salt) — случайная строка, которая добавляется к паролю перед хешированием.
Зачем? Чтобы одинаковые пароли у разных людей давали разные хеши.

Хранится в формате: "соль:хеш"
При проверке: берём соль из сохранённого хеша, хешируем пароль с этой солью,
сравниваем с сохранённым хешем.

--- ПРО JWT ---
JWT (JSON Web Token) — это строка вида: header.payload.signature
- header: алгоритм подписи
- payload: данные (user_id, срок действия)
- signature: подпись, чтобы никто не подделал токен

Мы используем PyJWT с алгоритмом HS256 (HMAC + SHA-256).
HS256 использует только встроенный hashlib — НИКАКИХ крипто-библиотек!
"""

import hashlib
import secrets
import jwt
from datetime import datetime, timedelta

# Секретный ключ для подписи JWT-токенов.
# В продакшене его нужно хранить в переменной окружения, не в коде!
SECRET_KEY = "my-super-secret-key-for-jwt-change-in-production"

# Алгоритм подписи токена
ALGORITHM = "HS256"

# Сколько живёт токен (24 часа)
TOKEN_EXPIRE_HOURS = 24


# ========== ХЕШИРОВАНИЕ ПАРОЛЕЙ ==========

def hash_password(password: str) -> str:
    """
    Хеширует пароль с помощью SHA-256 + случайная соль.
    
    Возвращает строку вида: "соль:хеш"
    
    Пример:
        hash_password("qwerty123") → "a1b2c3...:d4e5f6..."
    """
    # Генерируем случайную соль (32 hex-символа = 16 байт)
    salt = secrets.token_hex(16)
    # Хешируем соль+пароль
    hash_value = hashlib.sha256((salt + password).encode()).hexdigest()
    # Склеиваем соль и хеш через двоеточие
    return f"{salt}:{hash_value}"


def verify_password(password: str, hashed: str) -> bool:
    """
    Проверяет, совпадает ли пароль с хешем.
    
    Как это работает:
    1. Разделяем сохранённую строку "соль:хеш" на соль и хеш
    2. Хешируем введённый пароль с той же солью
    3. Сравниваем полученный хеш с сохранённым
    4. Если совпадают — пароль правильный!
    """
    salt, stored_hash = hashed.split(":")
    computed_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    return computed_hash == stored_hash


# ========== JWT-ТОКЕНЫ ==========

def create_access_token(user_id: str) -> str:
    """
    Создаёт JWT-токен для пользователя.
    
    Payload (данные внутри токена):
    - sub: user_id (кто этот пользователь)
    - exp: время, когда токен истечёт
    - iat: время, когда токен создан
    
    Токен подписывается секретным ключом, чтобы его нельзя было подделать.
    """
    now = datetime.utcnow()
    payload = {
        "sub": user_id,                          # subject = кто владелец токена
        "iat": now,                               # issued at = когда создан
        "exp": now + timedelta(hours=TOKEN_EXPIRE_HOURS)  # expiration = когда истечёт
    }
    # Кодируем payload в JWT-строку
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> dict | None:
    """
    Расшифровывает JWT-токен и возвращает payload.
    
    Если токен просрочен или невалиден — возвращает None.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Токен просрочен
        return None
    except jwt.InvalidTokenError:
        # Токен кривой
        return None
