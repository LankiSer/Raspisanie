#!/bin/bash
# Скрипт для копирования исправленных файлов в контейнер

echo "📦 Copying fixed files to container..."

# Копируем исправленный seed.py
docker cp backend/scripts/seed.py schedule_saas_backend:/app/scripts/seed.py

# Копируем check_and_fix_user.py
docker cp backend/check_and_fix_user.py schedule_saas_backend:/app/check_and_fix_user.py

echo "✅ Files copied!"
echo "🔄 Restarting backend container..."
docker compose restart backend

echo "✅ Done! Now run: docker compose exec backend python3 scripts/seed.py"

