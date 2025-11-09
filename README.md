admin@mgtu.ru

admin123

логин и праоль от тестовго пользователя


Сначала
docker compose up -d
После для тестовых данных для тестовгго пользователя
docker compose exec backend bash -lc 'psql "postgresql://schedule_user:schedule_password@database:5432/schedule_saas" -v ON_ERROR_STOP=1 -f /app/sql/admin_seed.sql'
