# Создание пользователя прямо сейчас

База данных не пустая, но пользователь не может войти. Нужно создать/исправить пользователя.

## Быстрое решение

Выполните в PowerShell:

```powershell
# Скопировать обновленный скрипт в контейнер
docker cp backend/check_and_fix_user.py schedule_saas_backend:/app/check_and_fix_user.py

# Запустить скрипт (он создаст пользователя, если его нет, или исправит пароль)
docker compose exec backend python3 check_and_fix_user.py
```

Скрипт автоматически:
- Проверит наличие пользователя `admin@university.edu`
- Если нет - создаст его и организацию
- Если есть - проверит и исправит пароль

## После выполнения

Попробуйте войти:
- Email: `admin@university.edu`
- Password: `admin123`

