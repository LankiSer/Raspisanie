# Автоматическое создание тестовых данных

## Обзор

Система автоматически создает тестовые данные при первом запуске контейнера, если база данных пустая.

## Как это работает

### 1. Entrypoint скрипт (`entrypoint.sh`)

При запуске контейнера `entrypoint.sh` выполняет следующие шаги:

1. ⏳ **Ожидание базы данных** - проверяет доступность PostgreSQL
2. 🔧 **Миграции** - применяет Alembic миграции
3. 🔍 **Проверка пустой БД** - проверяет наличие организаций в БД
4. 🌱 **Создание данных** - если БД пустая, запускает Python скрипт seed

### 2. Скрипт создания данных (`scripts/seed.py`)

Основной скрипт для создания тестовых данных. Создает:

- Организацию
- Пользователей (админ, методист, преподаватель)
- Учебный год и семестр
- Группы студентов
- Преподавателей
- Курсы
- Временные слоты
- Аудитории
- Доступность преподавателей
- Зачисления на курсы
- Примеры занятий

## Использование

### Автоматическое создание (рекомендуется)

Просто запустите:

```bash
docker compose up -d
```

Если база данных пустая, данные создадутся автоматически.

### Ручное создание

Если нужно пересоздать данные:

```bash
# Вариант 1: Основной seed скрипт
docker compose exec backend python3 scripts/seed.py

# Вариант 2: Скрипт создания тестового аккаунта
docker compose exec backend python3 create_test_account.py
```

### Очистка и пересоздание

```bash
# Остановить и удалить все (включая volumes)
docker compose down -v

# Пересоздать с нуля
docker compose up -d
```

## Тестовые учетные записи

После создания тестовых данных доступны:

| Роль | Email | Password |
|------|-------|----------|
| Администратор | `admin@university.edu` | `admin123` |
| Методист | `methodist@university.edu` | `methodist123` |
| Преподаватель | `teacher1@university.edu` | `teacher123` |

## Логирование

Проверить процесс создания данных:

```bash
# Просмотр логов backend
docker compose logs backend

# Следить за логами в реальном времени
docker compose logs -f backend
```

Вы должны увидеть:

```
🚀 Starting application setup...
⏳ Waiting for database...
✅ Database is ready!
🔧 Running database migrations...
🔍 Checking if database needs seeding...
🌱 Database is empty, creating seed data...
📝 Running Python seed script (scripts/seed.py)...
🌱 Starting seed data creation...
📚 Creating organization...
👥 Creating users...
...
✅ Seed data created successfully!
🎯 Starting FastAPI application...
```

## Устранение проблем

### Скрипт не запускается

1. Проверьте, что файл существует:
   ```bash
   docker compose exec backend ls -la scripts/seed.py
   ```

2. Проверьте права доступа:
   ```bash
   docker compose exec backend chmod +x scripts/seed.py
   ```

3. Запустите вручную для отладки:
   ```bash
   docker compose exec backend python3 scripts/seed.py
   ```

### Ошибки импорта

Убедитесь, что все зависимости установлены:

```bash
docker compose exec backend poetry install
```

### База данных не пустая

Если нужно пересоздать данные в существующей БД:

1. Удалите данные вручную через SQL или
2. Пересоздайте volumes: `docker compose down -v`

## Альтернативные скрипты

В проекте есть несколько скриптов для создания тестовых данных:

- `scripts/seed.py` - основной скрипт (используется автоматически)
- `create_test_account.py` - создание тестового аккаунта
- `create_test_data.py` - создание тестовых данных
- `add_test_data.py` - добавление тестовых данных
- `add_data_for_mgtu.py` - данные для МГТУ

Все они могут быть запущены вручную при необходимости.

