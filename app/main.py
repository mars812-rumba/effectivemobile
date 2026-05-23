"""
main.py — точка входа в приложение.
1. Создаём приложение FastAPI
2. При старте — создаём тестовых пользователей (если их ещё нет)
3. Подключаем роуты (users, admin, cars)
4. Запускаем сервер
"""
from fastapi import FastAPI
from app.database import read_data, write_data, find_one
from app.security import hash_password
from datetime import datetime

# Создаём приложение
app = FastAPI(
    title="Система аутентификации и авторизации",
    description="Тестовое задание — собственная система доступа к ресурсам",
    version="1.0.0"
)


# ========== Создание тестовых данных при старте ==========

def seed_test_users():
    """
    Создаёт тестовых пользователей, если база пуста.
    
    Три пользователя:
    1. admin@test.ru — администратор (роль admin)
    2. user@test.ru — обычный пользователь (роль user)
    3. moderator@test.ru — модератор (роль moderator)
    
    Пароль у всех: qwerty123
    """
    users = read_data("users.json")
    
    # Если пользователи уже есть — ничего не делаем
    if len(users) > 0:
        return
    
    test_users = [
        {
            "id": "user-1",
            "first_name": "Админ",
            "last_name": "Админович",
            "patronymic": "Админов",
            "email": "admin@test.ru",
            "password_hash": hash_password("qwerty123"),
            "role_id": "role-admin",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "user-2",
            "first_name": "Иван",
            "last_name": "Иванов",
            "patronymic": "Иванович",
            "email": "user@test.ru",
            "password_hash": hash_password("qwerty123"),
            "role_id": "role-user",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "user-3",
            "first_name": "Мария",
            "last_name": "Петрова",
            "patronymic": "Сергеевна",
            "email": "moderator@test.ru",
            "password_hash": hash_password("qwerty123"),
            "role_id": "role-moderator",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    
    write_data("users.json", test_users)
    print("✅ Тестовые пользователи созданы!")
    print("   admin@test.ru / qwerty123 (администратор)")
    print("   user@test.ru / qwerty123 (пользователь)")
    print("   moderator@test.ru / qwerty123 (модератор)")


@app.on_event("startup")
def on_startup():
    """Вызывается при запуске приложения."""
    seed_test_users()


# ========== Подключаем роуты ==========

from app.routes import users, admin, cars

app.include_router(users.router)
app.include_router(admin.router)
app.include_router(cars.router)


# ========== Корневой эндпоинт ==========

@app.get("/")
def root():
    """Приветственный эндпоинт — проверка, что сервер работает."""
    return {
        "message": "Система аутентификации и авторизации работает!",
        "docs": "/docs — Swagger UI для тестирования API"
    }

# ========== Запуск через python ==========

if __name__ == "__main__":

    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
