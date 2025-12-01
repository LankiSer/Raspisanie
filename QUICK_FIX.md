# Быстрое исправление проблемы с входом

## Проблема
Контейнер использует старую версию файлов. Нужно пересобрать контейнер или скопировать файлы.

## Решение 1: Пересобрать контейнер (рекомендуется)

```bash
cd Raspisanie
docker compose down
docker compose build --no-cache backend
docker compose up -d
```

Затем проверьте логи:
```bash
docker compose logs -f backend
```

Дождитесь сообщения:
```
✅ Seed data created successfully!
```

## Решение 2: Скопировать файлы напрямую в контейнер

```bash
# Скопировать исправленный seed.py
docker compose cp backend/scripts/seed.py schedule_saas_backend:/app/scripts/seed.py

# Скопировать check_and_fix_user.py
docker compose cp backend/check_and_fix_user.py schedule_saas_backend:/app/check_and_fix_user.py

# Перезапустить контейнер
docker compose restart backend
```

## Решение 3: Создать пользователя напрямую через Python

Если ничего не помогает, выполните это в контейнере:

```bash
docker compose exec backend python3 -c "
import asyncio
import sys
sys.path.insert(0, '/app')
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.core.auth import get_password_hash
from app.models.user import User, UserRole
from app.models.organization import Organization
from sqlalchemy import select

async def fix():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        result = await session.execute(select(Organization).limit(1))
        org = result.scalar_one_or_none()
        if not org:
            org = Organization(name='МГТУ', locale='ru', tz='Europe/Moscow')
            session.add(org)
            await session.flush()
        
        result = await session.execute(select(User).where(User.email == 'admin@university.edu'))
        user = result.scalar_one_or_none()
        
        if user:
            print('User exists, updating password...')
            user.password_hash = get_password_hash('admin123')
            user.is_active = True
        else:
            print('Creating new user...')
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

asyncio.run(fix())
"
```

## После исправления

Попробуйте войти снова:
- Email: `admin@university.edu`
- Password: `admin123`

