# Инструкция по развертыванию

## После пуша изменений

Все исправления применены. Для работы нужно:

### 1. Пересобрать контейнер (обязательно)

```bash
docker compose down
docker compose build --no-cache backend
docker compose up -d
```

### 2. Проверить логи

```bash
docker compose logs -f backend
```

Дождитесь сообщения:
```
✅ Seed data created successfully!
```

### 3. Проверить вход

После успешного создания данных попробуйте войти:
- Email: `admin@university.edu`
- Password: `admin123`

## Что было исправлено

✅ **scripts/seed.py** - убран импорт HoursUnit, исправлен доступ к relationship
✅ **entrypoint.sh** - автоматически запускает seed.py при пустой БД
✅ **docker-compose.yml** - добавлен volume для scripts (для разработки)
✅ **Все файлы с тестовыми данными** - исправлены импорты

## Автоматическое создание данных

При первом запуске контейнера (`docker compose up -d`):

1. ⏳ Ожидание базы данных
2. 🔧 Применение миграций Alembic
3. 🔍 Проверка, пустая ли база данных
4. 🌱 Если пустая - автоматический запуск `scripts/seed.py`
5. ✅ Создание тестовых данных (организация, пользователи, группы, курсы и т.д.)

## Если что-то не работает

### Проверка пользователя:
```bash
docker compose exec backend python3 check_and_fix_user.py
```

### Ручной запуск seed:
```bash
docker compose exec backend python3 scripts/seed.py
```

### Пересоздание с нуля:
```bash
docker compose down -v
docker compose build --no-cache backend
docker compose up -d
```

## Важно

- При изменении `scripts/seed.py` нужно **пересобрать контейнер** или использовать volume (уже добавлен)
- При изменении `entrypoint.sh` нужно **пересобрать контейнер**
- При изменении других файлов backend - достаточно **перезапустить** контейнер

