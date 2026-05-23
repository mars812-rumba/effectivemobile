"""
routes/admin.py — роуты для администратора.

Админ может:
1. Посмотреть все роли
2. Создать новую роль
3. Обновить роль (имя, описание, разрешения)
4. Удалить роль
5. Посмотреть все разрешения
6. Изменить разрешения у роли
7. Посмотреть всех пользователей
8. Изменить роль пользователя

Все эти роуты защищены — доступны только админу.
Проверка происходит через check_permission(current_user, "roles", "manage").
"""

from fastapi import APIRouter, Depends, HTTPException, status
import uuid

from app.models import (
    RoleCreate, RoleUpdate, RoleResponse,
    PermissionResponse, RolePermissionsUpdate,
    MessageResponse, UserResponse
)
from app.database import read_data, write_data, find_by_id, find_one
from app.auth import get_current_user
from app.utils import check_permission, is_admin

router = APIRouter(prefix="/admin", tags=["Администрирование"])


# ========== РОЛИ ==========

@router.get("/roles", response_model=list[RoleResponse])
def get_roles(current_user: dict = Depends(get_current_user)):
    """Получить список всех ролей. Доступно только админу."""
    check_permission(current_user, "roles", "manage")
    roles = read_data("roles.json")
    return [RoleResponse(**role) for role in roles]


@router.post("/roles", response_model=RoleResponse)
def create_role(role_data: RoleCreate, current_user: dict = Depends(get_current_user)):
    """Создать новую роль. Доступно только админу."""
    check_permission(current_user, "roles", "manage")
    
    # Проверяем, что роль с таким именем не существует
    existing = find_one("roles.json", name=role_data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Роль '{role_data.name}' уже существует"
        )
    
    # Проверяем, что все permission_ids существуют
    all_permissions = read_data("permissions.json")
    valid_perm_ids = {p["id"] for p in all_permissions}
    for perm_id in role_data.permission_ids:
        if perm_id not in valid_perm_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Разрешение '{perm_id}' не существует"
            )
    
    new_role = {
        "id": f"role-{uuid.uuid4().hex[:8]}",
        "name": role_data.name,
        "description": role_data.description,
        "permission_ids": role_data.permission_ids
    }
    
    roles = read_data("roles.json")
    roles.append(new_role)
    write_data("roles.json", roles)
    
    return RoleResponse(**new_role)


@router.put("/roles/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: str,
    role_data: RoleUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Обновить роль. Доступно только админу."""
    check_permission(current_user, "roles", "manage")
    
    roles = read_data("roles.json")
    updated_role = None
    
    for role in roles:
        if role["id"] == role_id:
            if role_data.name is not None:
                role["name"] = role_data.name
            if role_data.description is not None:
                role["description"] = role_data.description
            if role_data.permission_ids is not None:
                # Проверяем, что все permission_ids существуют
                all_permissions = read_data("permissions.json")
                valid_perm_ids = {p["id"] for p in all_permissions}
                for perm_id in role_data.permission_ids:
                    if perm_id not in valid_perm_ids:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Разрешение '{perm_id}' не существует"
                        )
                role["permission_ids"] = role_data.permission_ids
            updated_role = role
            break
    
    if not updated_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Роль не найдена"
        )
    
    write_data("roles.json", roles)
    return RoleResponse(**updated_role)


@router.delete("/roles/{role_id}", response_model=MessageResponse)
def delete_role(role_id: str, current_user: dict = Depends(get_current_user)):
    """Удалить роль. Доступно только админу."""
    check_permission(current_user, "roles", "manage")
    
    roles = read_data("roles.json")
    
    # Нельзя удалить роль admin
    role = find_by_id("roles.json", role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Роль не найдена"
        )
    
    if role["name"] == "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя удалить роль администратора"
        )
    
    # Проверяем, что нет пользователей с этой ролью
    users = read_data("users.json")
    users_with_role = [u for u in users if u.get("role_id") == role_id]
    if users_with_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Нельзя удалить роль: есть {len(users_with_role)} пользователей с этой ролью"
        )
    
    roles = [r for r in roles if r["id"] != role_id]
    write_data("roles.json", roles)
    
    return MessageResponse(message=f"Роль '{role['name']}' удалена")


# ========== РАЗРЕШЕНИЯ ==========

@router.get("/permissions", response_model=list[PermissionResponse])
def get_permissions(current_user: dict = Depends(get_current_user)):
    """Получить список всех разрешений. Доступно только админу."""
    check_permission(current_user, "permissions", "read")
    permissions = read_data("permissions.json")
    return [PermissionResponse(**p) for p in permissions]


@router.put("/roles/{role_id}/permissions", response_model=RoleResponse)
def update_role_permissions(
    role_id: str,
    perm_data: RolePermissionsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Изменить список разрешений у роли. Доступно только админу."""
    check_permission(current_user, "roles", "manage")
    
    # Проверяем, что все permission_ids существуют
    all_permissions = read_data("permissions.json")
    valid_perm_ids = {p["id"] for p in all_permissions}
    for perm_id in perm_data.permission_ids:
        if perm_id not in valid_perm_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Разрешение '{perm_id}' не существует"
            )
    
    roles = read_data("roles.json")
    updated_role = None
    
    for role in roles:
        if role["id"] == role_id:
            role["permission_ids"] = perm_data.permission_ids
            updated_role = role
            break
    
    if not updated_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Роль не найдена"
        )
    
    write_data("roles.json", roles)
    return RoleResponse(**updated_role)


# ========== ПОЛЬЗОВАТЕЛИ (для админа) ==========

@router.get("/users", response_model=list[UserResponse])
def get_all_users(current_user: dict = Depends(get_current_user)):
    """Получить список всех пользователей. Доступно только админу."""
    check_permission(current_user, "users", "read")
    users = read_data("users.json")
    return [
        UserResponse(
            id=u["id"],
            first_name=u["first_name"],
            last_name=u.get("last_name"),
            patronymic=u.get("patronymic"),
            email=u["email"],
            role_id=u["role_id"],
            is_active=u["is_active"],
            created_at=u["created_at"]
        )
        for u in users
    ]


@router.put("/users/{user_id}/role", response_model=MessageResponse)
def change_user_role(
    user_id: str,
    role_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Изменить роль пользователя. Доступно только админу."""
    check_permission(current_user, "users", "write")
    
    # Проверяем, что пользователь существует
    user = find_by_id("users.json", user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    
    # Проверяем, что роль существует
    role = find_by_id("roles.json", role_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Роль не найдена"
        )
    
    # Меняем роль
    users = read_data("users.json")
    for u in users:
        if u["id"] == user_id:
            u["role_id"] = role_id
            break
    write_data("users.json", users)
    
    return MessageResponse(
        message=f"Пользователю {user['email']} назначена роль {role['name']}"
    )
