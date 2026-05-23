"""
routes/cars.py — Mock-View для бизнес-объектов "Автомобили".

Это минимальные вымышленные объекты бизнес-приложения,
к которым применяется наша система авторизации.

Машины (cars) — это просто пример ресурса, доступ к которому
контролируется через нашу систему разрешений.

Правила доступа:
- perm-cars-read → может смотреть список машин
- perm-cars-write → может создавать/редактировать машины
- perm-cars-delete → может удалять машины

Если пользователь не залогинен → 401
Если залогинен, но нет разрешения → 403
Если есть разрешение → возвращает данные
"""

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import read_data
from app.auth import get_current_user
from app.utils import check_permission

router = APIRouter(prefix="/cars", tags=["Автомобили (Mock)"])


@router.get("/")
def get_cars(current_user: dict = Depends(get_current_user)):
    """
    Получить список всех автомобилей.
    
    Нужно разрешение: perm-cars-read (resource="cars", action="read")
    """
    check_permission(current_user, "cars", "read")
    
    cars = read_data("cars.json")
    return {"cars": cars, "total": len(cars)}


@router.get("/{car_id}")
def get_car(car_id: str, current_user: dict = Depends(get_current_user)):
    """
    Получить информацию об одном автомобиле.
    
    Нужно разрешение: perm-cars-read
    """
    check_permission(current_user, "cars", "read")
    
    cars = read_data("cars.json")
    for car in cars:
        if car["id"] == car_id:
            return car
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Автомобиль не найден"
    )


@router.post("/")
def create_car(car_data: dict, current_user: dict = Depends(get_current_user)):
    """
    Создать автомобиль (mock — не сохраняет в базу).
    
    Нужно разрешение: perm-cars-write
    """
    check_permission(current_user, "cars", "write")
    
    return {
        "message": "Автомобиль создан (mock — не сохраняется)",
        "car": car_data
    }


@router.put("/{car_id}")
def update_car(car_id: str, car_data: dict, current_user: dict = Depends(get_current_user)):
    """
    Обновить автомобиль (mock — не сохраняет в базу).
    
    Нужно разрешение: perm-cars-write
    """
    check_permission(current_user, "cars", "write")
    
    cars = read_data("cars.json")
    for car in cars:
        if car["id"] == car_id:
            return {
                "message": "Автомобиль обновлён (mock — не сохраняется)",
                "old": car,
                "new": car_data
            }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Автомобиль не найден"
    )


@router.delete("/{car_id}")
def delete_car(car_id: str, current_user: dict = Depends(get_current_user)):
    """
    Удалить автомобиль (mock — не удаляет из базы).
    
    Нужно разрешение: perm-cars-delete
    """
    check_permission(current_user, "cars", "delete")
    
    cars = read_data("cars.json")
    for car in cars:
        if car["id"] == car_id:
            return {
                "message": f"Автомобиль {car['brand']} {car['model']} удалён (mock — не сохраняется)"
            }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Автомобиль не найден"
    )
