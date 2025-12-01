# Исправления в файле seed.py с тестовыми данными

## Найденные проблемы

### 1. ❌ Импорт несуществующего HoursUnit
**Проблема:** В строке 18 импортировался `HoursUnit`, который не определен в моделях.

**Исправление:** Удален импорт `HoursUnit` из списка импортов.

### 2. ❌ Использование несуществующего enum
**Проблема:** В строке 284 использовалось `HoursUnit.per_week`, но `HoursUnit` не определен.

**Исправление:** Заменено на строку `"per_week"`, так как в модели `Enrollment` поле `unit` имеет тип `String(20)`, а не Enum.

### 3. ❌ Неправильный доступ к relationship
**Проблема:** В строке 277 использовалось `assignment.course.type`, но relationship может быть не загружен в момент создания enrollments.

**Исправление:** Создан словарь `course_map` для быстрого доступа к курсам по `course_id`, что более надежно и эффективно.

## Исправленный код

### До исправления:
```python
from app.models import (
    ...
    Group, Teacher, Course, CourseAssignment, Enrollment, HoursUnit,  # ❌ HoursUnit не существует
    ...
)

# В цикле создания enrollments:
hours = 3 if assignment.course.type == "lecture" else 2  # ❌ relationship может быть не загружен
unit=HoursUnit.per_week  # ❌ HoursUnit не определен
```

### После исправления:
```python
from app.models import (
    ...
    Group, Teacher, Course, CourseAssignment, Enrollment,  # ✅ Убран HoursUnit
    ...
)

# В цикле создания enrollments:
course_map = {course.course_id: course for course in courses}  # ✅ Создан словарь для быстрого доступа

for group in groups:
    for assignment in assignments:
        course = course_map[assignment.course_id]  # ✅ Надежный доступ к курсу
        hours = 3 if course.type == "lecture" else 2
        unit="per_week"  # ✅ Строковое значение
```

## Проверка других файлов

### Файлы, которые также используют HoursUnit (требуют проверки):

1. **create_test_account.py** (строка 10, 150)
   - Импортирует `HoursUnit`
   - Использует `HoursUnit.PER_TERM.value`
   - ⚠️ Требует исправления

2. **add_test_data.py** (строка 11, 14)
   - Импортирует `HoursUnit`
   - ⚠️ Требует проверки использования

3. **add_data_for_mgtu.py** (строка 8)
   - Импортирует `HoursUnit`
   - ⚠️ Требует проверки использования

### Файлы, которые импортируют несуществующий Lesson:

1. **create_test_account.py** (строка 13)
   - Импортирует `from app.models.lessons import Lesson`
   - ⚠️ Файл `lessons.py` не существует в `app/models/`
   - Возможно, это старая модель, которая была удалена

2. **add_test_data.py** (строка 14)
   - Импортирует `Lesson`
   - ⚠️ Требует проверки

3. **add_data_for_mgtu.py** (строка 11)
   - Импортирует `Lesson`
   - ⚠️ Требует проверки

## Рекомендации

1. ✅ **seed.py исправлен** - готов к использованию
2. ⚠️ Проверить и исправить другие скрипты создания тестовых данных
3. ⚠️ Удалить неиспользуемые импорты `Lesson` из скриптов
4. ⚠️ Заменить все использования `HoursUnit` на строковые значения

## Валидные значения для unit

Согласно модели `Enrollment`, поле `unit` имеет тип `String(20)` с дефолтным значением `"per_week"`.

Возможные значения (нужно проверить в миграциях или документации):
- `"per_week"` - часов в неделю
- `"per_term"` - часов в семестр
- Возможно другие значения

## Статус исправлений

- ✅ `scripts/seed.py` - **ИСПРАВЛЕН**
- ⚠️ `create_test_account.py` - требует проверки
- ⚠️ `add_test_data.py` - требует проверки
- ⚠️ `add_data_for_mgtu.py` - требует проверки

