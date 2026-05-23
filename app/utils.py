"""
utils.py — утилиты для АВТОРИЗАЦИИ: проверяем, МОЖЕТ ЛИ пользователь делать действие.

АВТОРИЗАЦИЯ — это проверка прав доступа.
У нас она работает так:

Пользователь → Роль → Разрешения → Ресурс + Действие

1. У каждого пользователя есть role_id (одна роль)
2. У каждой роли есть список permission_ids (много разрешений)
3. У каждого разрешения есть resource (что) и action (что делать)

Пример:
- Пользователь "Иван" имеет роль "user"
- Роль "user" имеет разрешение ["perm-cars-read"]
- Разрешение "perm-cars-read" = resource: "cars", action: "read"
- Значит Иван МОЖЕТ читать машины, но НЕ МОЖЕТ их удалять

Функция check_permission() — главная. Она проверяет:
есть ли у пользователя разрешение на ресурс+действие.
"""

from fastapi import HTTPException, status
from app.database import read_data, find_by_id


def get_user_permissions(user: dict) -> list[dict]:
    """
    Получает список разрешений пользователя через его роль.
    
    Цепочка: пользователь → role_id → роль → permission_ids → разрешения
    
    Возвращает список словарей-разрешений.
    """
    # Находим роль пользователя
    role = find_by_id("roles.json", user.get("role_id"))
    if not role:
        return []
    
    # Получаем все разрешения из базы
    all_permissions = read_data("permissions.json")
    
    # Фильтруем — оставляем только те, что есть в роли
    user_permissions = []
    for perm_id in role.get("permission_ids", []):
        for perm in all_permissions:
            if perm["id"] == perm_id:
                user_permissions.append(perm)
    
    return user_permissions


def check_permission(user: dict, resource: str, action: str) -> None:
    """
    Проверяет, есть ли у пользователя разрешение на ресурс+действие.
    
    Если НЕТ — выбрасывает 403 Forbidden.
    Если ДА — ничего не делает (код продолжает работать).
    
    Параметры:
    - user: словарь пользователя (из get_current_user)
    - resource: что пытаемся сделать (например "cars", "users", "roles")
    - action: какое действие (например "read", "write", "delete", "manage")
    
    Использование в роутах:
        check_permission(current_user, "cars", "read")
        # если дошло сюда — доступ есть, продолжаем
    """
    permissions = get_user_permissions(user)
    
    for perm in permissions:
        if perm["resource"] == resource and perm["action"] == action:
            return  # Разрешение найдено — всё ок!
    
    # Разрешение НЕ найдено — доступ запрещён
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Доступ запрещён: нет разрешения на {action} для {resource}"
    )


def is_admin(user: dict) -> bool:
    """
    Быстрая проверка: является ли пользователь админом?
    Полезно для роутов, которые доступны только админам.
    """
    role = find_by_id("roles.json", user.get("role_id"))
    return role is not None and role.get("name") == "admin"
