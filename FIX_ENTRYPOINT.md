# Исправление ошибки "exec ./entrypoint.sh: no such file or directory"

## Проблема
При запуске Docker контейнера возникала ошибка:
```
exec ./entrypoint.sh: no such file or directory
```

## Причины
1. **Относительный путь** - использование `./entrypoint.sh` вместо абсолютного пути
2. **Окончания строк Windows (CRLF)** - файл создан на Windows, а Linux требует LF
3. **Неправильные команды создания пользователя** - использовались команды для Alpine Linux вместо Ubuntu

## Исправления

### 1. Dockerfile
- Изменен `ENTRYPOINT` с `["./entrypoint.sh"]` на `["/app/entrypoint.sh"]` (абсолютный путь)
- Добавлено исправление окончаний строк: `sed -i 's/\r$//' /app/entrypoint.sh`
- Исправлены команды создания пользователя для Ubuntu:
  - `addgroup` → `groupadd`
  - `adduser` → `useradd`

### 2. entrypoint.sh
- Улучшена обработка ошибок для опционального SQL файла
- Добавлена проверка существования файла seed SQL

## Как пересобрать

```bash
cd Raspisanie
docker-compose down
docker-compose build --no-cache backend
docker-compose up -d
```

## Проверка

После пересборки проверьте логи:
```bash
docker-compose logs backend
```

Вы должны увидеть:
```
🚀 Starting application setup...
⏳ Waiting for database...
✅ Database is ready!
🔧 Running database migrations...
```

## Дополнительные рекомендации

Если проблема сохраняется:

1. **Проверьте права доступа на файл** (на Windows это не критично, но в контейнере должно быть `chmod +x`)

2. **Убедитесь, что файл не в .dockerignore** (уже проверено - файл не игнорируется)

3. **Проверьте окончания строк вручную** (если нужно):
   ```bash
   # В Git Bash или WSL
   dos2unix Raspisanie/backend/entrypoint.sh
   ```

4. **Альтернативный способ** - если проблема все еще есть, можно использовать `bash` напрямую:
   ```dockerfile
   ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
   ```

