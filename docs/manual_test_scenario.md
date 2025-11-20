# Ручной сценарий тестирования (Manual Test Scenario)

Этот документ описывает, как вручную проверить работу системы "InG AI Sales Department" без написания кода.

## 1. Подготовка (Setup)

Перед началом убедитесь, что у вас настроено окружение (см. `docs/13-setup-guide.md`):

1.  **Google Sheet**: Создана таблица с листом `Leads` и правильными колонками.
2.  **API Keys**: В файле `.env` прописаны ключи (Gemini, Google Sheets, LinkedIn Service).
3.  **Зависимости**: `pip install -r requirements.txt`.

## 2. Сценарий тестирования (End-to-End)

Мы проверим полный цикл: от добавления лида до отправки сообщения.

### Шаг 1: Добавление тестового лида
Вручную добавьте строку в Google Sheet (лист `Leads`):

| Column | Value |
|--------|-------|
| **Lead ID** | `test_001` |
| **Name** | `Test User` |
| **Position** | `CTO` |
| **Company** | `Test Corp` |
| **LinkedIn URL** | `https://www.linkedin.com/in/test-profile-123/` (используйте реальный или валидный URL) |
| **Contact Status** | `Not Contacted` |
| **Created At** | `2025-01-01 10:00:00` |
| **Last Updated** | `2025-01-01 10:00:00` |

*Остальные поля оставьте пустыми.*

### Шаг 2: Запуск Lead Finder (Классификация)
Запустите агентов:
```bash
python main.py
```
*Подождите 1-2 минуты (Lead Finder работает по расписанию или при старте).*

**Проверка в Google Sheet:**
- Поле **Classification** должно заполниться (например, `Speaker` или `Sponsor`).
- Поле **Quality Score** должно заполниться (число от 1 до 10).
- Поле **Last Updated** должно обновиться.

### Шаг 3: Запуск Sales Manager (Аллокация)
Если Lead Finder отработал успешно, Sales Manager должен подхватить лида.
*Это происходит автоматически в рамках запущенного `main.py` (обычно в 9:00, но при первом запуске может сработать проверка).*

**Проверка в Google Sheet:**
- Поле **Contact Status** изменилось на `Allocated`.
- Поле **Allocated To** заполнено (например, `Outreach`).
- Поле **Allocated At** заполнено текущим временем.

### Шаг 4: Запуск Outreach Agent (Генерация сообщения)
Outreach агент постоянно мониторит очередь.

**Проверка в Google Sheet:**
- Поле **Contact Status** изменилось на `Message Sent` (или `Queued` если есть задержка).
- Поле **Message Sent** заполнилось текстом сообщения.
- Текст сообщения должен быть персонализирован (содержать имя, компанию, позицию).

### Шаг 5: Проверка отправки (Если подключен реальный LinkedIn)
Если вы используете Gojiberry/Dripify:
- Проверьте дашборд сервиса.
- Сообщение должно появиться в "Sent" или "Queued".

## 3. Тестирование обработки ответов (Mock)

Чтобы проверить, как агент обрабатывает ответы, симулируйте ответ в Google Sheet.

1.  Вручную измените поля для `test_001`:
    - **Response**: "Hi, thanks for reaching out! I'm interested in speaking."
    - **Response Received At**: `2025-01-01 12:00:00`
    - **Contact Status**: `Message Sent` (верните, если изменился)

2.  Подождите цикл проверки Outreach агента (каждые 2 часа, или перезапустите `main.py`).

**Проверка:**
- Поле **Response Sentiment** стало `positive`.
- Поле **Response Intent** стало `interested`.
- Поле **Contact Status** может измениться на `Responded`.

## 4. Полезные команды для отладки

- **Смотреть логи**:
  ```bash
  tail -f data/logs/agents.log
  ```
- **Очистить состояние (для перезапуска теста)**:
  Удалите файлы в `data/state/` и очистите строки в Google Sheet (кроме заголовка).
