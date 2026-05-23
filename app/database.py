"""
database.py — работа с JSON-файлами как с «базой данных».

Вместо PostgreSQL мы храним всё в JSON-файлах в папке data/.
Это НЕ для продакшена, но для понимания принципов — идеально.

Каждая функция делает простую вещь:
- read_data() — читает JSON-файл и возвращает список словарей
- write_data() — записывает список словарей обратно в JSON-файл
"""

import json
import os

# Путь к папке data/ (относительно корня проекта)
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def read_data(filename: str) -> list:
    """
    Читает JSON-файл из папки data/ и возвращает список.
    
    Пример: read_data("users.json") вернёт список пользователей.
    Если файл пустой — вернёт пустой список [].
    """
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if data else []


def write_data(filename: str, data: list) -> None:
    """
    Записывает список в JSON-файл в папку data/.
    
    Перезаписывает файл целиком. indent=2 чтобы файл
    был читаемым человеком (с отступами).
    """
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def find_by_id(filename: str, item_id: str) -> dict | None:
    """
    Ищет элемент по полю 'id' в JSON-файле.
    Возвращает словарь если найден, иначе None.
    """
    items = read_data(filename)
    for item in items:
        if item.get("id") == item_id:
            return item
    return None


def find_one(filename: str, **filters) -> dict | None:
    """
    Ищет первый элемент, у которого все ключи из filters совпадают.
    
    Пример: find_one("users.json", email="test@mail.ru")
    найдёт первого пользователя с таким email.
    """
    items = read_data(filename)
    for item in items:
        if all(item.get(key) == value for key, value in filters.items()):
            return item
    return None
