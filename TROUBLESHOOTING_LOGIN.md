# Устранение проблемы с входом (401 Unauthorized)

## Проблема
При попытке войти с учетными данными:
- Email: `admin@university.edu`
- Password: `admin123`

Получаете ошибку **401 Unauthorized**.

## Возможные причины

1. **Пользователь не создан** - seed скрипт не запустился
2. **Пароль неправильно хеширован** - проблема при создании пользователя
3. **Пользователь неактивен** - `is_active = False`

## Решение

### Шаг 1: Проверьте, создан ли пользователь

Выполните в контейнере:

```bash
docker compose exec backend python3 check_and_fix_user.py
```

Этот скрипт:
- Проверит, существует ли пользователь
- Проверит правильность пароля
- Исправит пароль, если нужно

### Шаг 2: Если пользователь не найден - запустите seed скрипт вручную

```bash
docker compose exec backend python3 scripts/seed.py
```

### Шаг 3: Проверьте логи контейнера

```bash
docker compose logs backend | grep -i seed
docker compose logs backend | grep -i "creating users"
```

### Шаг 4: Альтернатива - создайте пользователя вручную

Если seed скрипт не работает, создайте пользователя через Python:

```bash
docker compose exec backend python3 -c "
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.core.auth import get_password_hash
from app.models.user import User, UserRole
from app.models.organization import Organization
from sqlalchemy import select

async def create_user():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        # Get or create organization
        result = await session.execute(select(Organization).limit(1))
        org = result.scalar_one_or_none()
        
        if not org:
            org = Organization(name='Московский технический университет', locale='ru', tz='Europe/Moscow')
            session.add(org)
            await session.flush()
        
        # Check if user exists
        result = await session.execute(select(User).where(User.email == 'admin@university.edu'))
        user = result.scalar_one_or_none()
        
        if user:
            print(f'User exists, updating password...')
            user.password_hash = get_password_hash('admin123')
        else:
            print(f'Creating new user...')
            user = User(
                org_id=org.org_id,
                email='admin@university.edu',
                password_hash=get_password_hash('admin123'),
                role=UserRole.ADMIN,
                is_active=True
            )
            session.add(user)
        
        await session.commit()
        print('✅ User created/updated successfully!')
    
    await engine.dispose()

asyncio.run(create_user())
"
```

## Проверка через SQL

Можно также проверить напрямую через PostgreSQL:

```bash
docker compose exec database psql -U schedule_user -d schedule_saas -c "SELECT user_id, email, is_active FROM users WHERE email = 'admin@university.edu';"
```

## Проверка хеша пароля

Если пользователь существует, но пароль не работает, проверьте хеш:

```bash
docker compose exec backend python3 -c "
from app.core.auth import get_password_hash, verify_password

# Создать новый хеш
new_hash = get_password_hash('admin123')
print(f'New hash: {new_hash}')

# Проверить
is_valid = verify_password('admin123', new_hash)
print(f'Verification: {is_valid}')
"
```

## Быстрое решение

Если ничего не помогает, выполните:

```bash
# 1. Остановите контейнеры
docker compose down

# 2. Удалите volumes (ОСТОРОЖНО: удалит все данные!)
docker compose down -v

# 3. Запустите заново
docker compose up -d

# 4. Проверьте логи
docker compose logs -f backend
```

Дождитесь сообщения:
```
✅ Seed data created successfully!
```

## Проверка после исправления

После исправления попробуйте войти снова:
- Email: `admin@university.edu`
- Password: `admin123`

Если все еще не работает, проверьте:
1. Правильность email (без опечаток)
2. Правильность пароля (без лишних пробелов)
3. Что пользователь активен (`is_active = True`)

