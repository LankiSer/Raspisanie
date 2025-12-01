# Расписание - SaaS платформа

## Быстрый старт

```bash
cd Raspisanie
docker compose up -d
```

Тестовые данные создаются **автоматически** при первом запуске, если база данных пустая.

## После первого запуска

Если база данных не пустая и данные не создались автоматически, выполните:

```bash
# Из корня проекта (c:\Проектики\rasp\Raspisanie)
# Скопировать исправленный seed.py в контейнер
docker cp backend/scripts/seed.py schedule_saas_backend:/app/scripts/seed.py

# Запустить seed скрипт для создания всех тестовых данных
docker compose exec backend python3 scripts/seed.py
```

Или создать/исправить пользователя:

```bash
# Из корня проекта (c:\Проектики\rasp\Raspisanie)
# Скопировать скрипт проверки пользователя
docker cp backend/check_and_fix_user.py schedule_saas_backend:/app/check_and_fix_user.py

# Запустить скрипт (создаст пользователя, если его нет)
docker compose exec backend python3 check_and_fix_user.py
```

## Тестовые учетные записи

После автоматического создания тестовых данных доступны следующие учетные записи:

### Администратор
- Email: `admin@university.edu`
- Password: `admin123`
- Роль: ADMIN

### Методист
- Email: `methodist@university.edu`
- Password: `methodist123`
- Роль: METHODIST

### Преподаватель
- Email: `teacher1@university.edu`
- Password: `teacher123`
- Роль: TEACHER

## Автоматическое создание тестовых данных

При запуске `docker compose up -d` скрипт `entrypoint.sh` автоматически:

1. ⏳ Ждет готовности базы данных
2. 🔧 Применяет миграции Alembic
3. 🔍 Проверяет, пустая ли база данных
4. 🌱 Если база пустая - запускает Python скрипт `scripts/seed.py` для создания тестовых данных

## Ручное создание тестовых данных

Если нужно пересоздать тестовые данные вручную (из корня проекта `c:\Проектики\rasp\Raspisanie`):

```bash
# Вариант 1: Использовать основной seed скрипт (рекомендуется)
# Сначала скопировать файл в контейнер (если изменили)
docker cp backend/scripts/seed.py schedule_saas_backend:/app/scripts/seed.py
# Затем запустить
docker compose exec backend python3 scripts/seed.py

# Вариант 2: Использовать скрипт создания тестового аккаунта
docker cp backend/create_test_account.py schedule_saas_backend:/app/create_test_account.py
docker compose exec backend python3 create_test_account.py
```

## Что создается автоматически

- ✅ 1 организация (Московский технический университет)
- ✅ 3 пользователя (админ, методист, преподаватель)
- ✅ 1 учебный год и семестр
- ✅ 3 группы студентов
- ✅ 3 преподавателя
- ✅ 5 курсов
- ✅ 5 временных слотов
- ✅ 6 аудиторий
- ✅ Записи о доступности преподавателей
- ✅ Записи о зачислениях групп на курсы
- ✅ Примеры занятий

## Проверка статуса

```bash
# Из корня проекта (c:\Проектики\rasp\Raspisanie)
# Просмотр логов backend
docker compose logs backend

# Проверка здоровья сервисов
docker compose ps
```

## Очистка и пересоздание

```bash
# Из корня проекта (c:\Проектики\rasp\Raspisanie)
# Остановить и удалить контейнеры и volumes
docker compose down -v

# Пересоздать все с нуля
docker compose up -d
```

## Важно: Пути к файлам

Все команды выполняются из корня проекта: `c:\Проектики\rasp\Raspisanie`

Пути к файлам в командах `docker cp`:
- `backend/scripts/seed.py` - относительно корня проекта Raspisanie
- `backend/check_and_fix_user.py` - относительно корня проекта Raspisanie
- `backend/create_test_account.py` - относительно корня проекта Raspisanie
