# Конные туры — практика по отношениям в БД

Стартап для продажи конных туров на Django + Django REST Framework.

## Связи

| Связь | Модели |
|---|---|
| 1 к 1 | `Customer` ↔ `CustomerProfile` |
| 1 ко многим | `Customer` → `Booking`, `Customer` → `Comment`, `Tour` → `Booking`, `Tour` → `Comment` |
| Многие ко многим | `Tour` ↔ `Category` («конный», «пеший», «мото») |

## Правила, которые проверяют тесты

1. Один человек может купить только 1 тур на определённый день и время (`UniqueConstraint` + проверка в сериализаторе).
2. Один человек может оставить несколько комментариев, но только к турам, в которых был (бронирование с датой ≤ сегодня).
3. У тура есть категории (M2M), фильтр `/api/tours/?category=конный`.
4. Все отправки данных (POST/PATCH) в API покрыты тестами: корректные данные → 201, некорректные → 400.

## Запуск (VS Code → Terminal → New Terminal)

Windows:

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py test -v 2
```

macOS / Linux: то же самое, но активация — `source .venv/bin/activate`.

## Документация (django.contrib.admindocs)

```
python manage.py createsuperuser
python manage.py runserver
```

Открыть http://127.0.0.1:8000/admin/doc/ → «Модели» → `tours` — там описание всех моделей и связей
(берётся из docstring'ов в `tours/models.py` и `tours/views.py`).

API: http://127.0.0.1:8000/api/
