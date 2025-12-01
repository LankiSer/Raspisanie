# Скрипт для полного исправления

Write-Host "📦 Copying fixed files to container..." -ForegroundColor Cyan

# Копируем исправленный seed.py
docker cp backend/scripts/seed.py schedule_saas_backend:/app/scripts/seed.py
Write-Host "✅ seed.py copied" -ForegroundColor Green

# Копируем обновленный check_and_fix_user.py
docker cp backend/check_and_fix_user.py schedule_saas_backend:/app/check_and_fix_user.py
Write-Host "✅ check_and_fix_user.py copied" -ForegroundColor Green

Write-Host "`n🔧 Creating/fixing user..." -ForegroundColor Yellow
docker compose exec backend python3 check_and_fix_user.py

Write-Host "`n✅ Done! Try to login now:" -ForegroundColor Green
Write-Host "   Email: admin@university.edu" -ForegroundColor White
Write-Host "   Password: admin123" -ForegroundColor White

