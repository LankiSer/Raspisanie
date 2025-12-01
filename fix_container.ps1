# PowerShell скрипт для копирования исправленных файлов в контейнер

Write-Host "📦 Copying fixed files to container..." -ForegroundColor Cyan

# Копируем исправленный seed.py
docker cp backend/scripts/seed.py schedule_saas_backend:/app/scripts/seed.py

# Копируем check_and_fix_user.py
docker cp backend/check_and_fix_user.py schedule_saas_backend:/app/check_and_fix_user.py

Write-Host "✅ Files copied!" -ForegroundColor Green
Write-Host "🔄 Restarting backend container..." -ForegroundColor Yellow
docker compose restart backend

Write-Host "✅ Done! Now run: docker compose exec backend python3 scripts/seed.py" -ForegroundColor Green

