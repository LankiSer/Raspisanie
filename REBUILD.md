# Полный ребилд проекта

## Вариант 1: Полный ребилд с очисткой (рекомендуется)

```bash
# 1. Остановить и удалить все контейнеры, сети и volumes (ОСТОРОЖНО: удалит данные БД!)
docker compose down -v

# 2. Удалить все образы проекта (опционально, если нужно полностью очистить)
docker compose down --rmi all

# 3. Пересобрать все образы без кеша
docker compose build --no-cache

# 4. Запустить все сервисы
docker compose up -d
```

## Вариант 2: Ребилд без удаления данных БД (безопасный)

```bash
# 1. Остановить контейнеры (БЕЗ удаления volumes)
docker compose down

# 2. Пересобрать все образы без кеша
docker compose build --no-cache

# 3. Запустить все сервисы
docker compose up -d
```

## Вариант 3: Ребилд только конкретного сервиса

```bash
# Ребилд только backend
docker compose build --no-cache backend
docker compose up -d backend

# Ребилд только frontend
docker compose build --no-cache frontend
docker compose up -d frontend
```

## Вариант 4: Быстрый ребилд (с кешем)

```bash
# Просто пересобрать и перезапустить
docker compose up -d --build
```

## Полезные команды для очистки

```bash
# Удалить все неиспользуемые образы
docker image prune -a

# Удалить все неиспользуемые volumes (ОСТОРОЖНО!)
docker volume prune

# Удалить все неиспользуемые контейнеры
docker container prune

# Полная очистка системы Docker (ОСТОРОЖНО: удалит ВСЁ!)
docker system prune -a --volumes
```

## Проверка после ребилда

```bash
# Проверить статус всех контейнеров
docker compose ps

# Проверить логи
docker compose logs -f

# Проверить логи конкретного сервиса
docker compose logs -f backend
docker compose logs -f frontend
```

## Важные замечания

⚠️ **ВНИМАНИЕ**: 
- `docker compose down -v` удалит ВСЕ volumes, включая данные БД!
- Используйте `docker compose down` (без `-v`) если хотите сохранить данные БД
- Для полного ребилда с сохранением данных используйте Вариант 2

