# Утилиты проекта

Эта папка содержит вспомогательные утилиты для работы с проектом.

## Категории утилит

### Проверка и диагностика
- `check_agent_status.py` - проверка статуса агентов
- `check_linkedin_accounts.py` - проверка конфигурации LinkedIn аккаунтов
- `check_and_update_accounts.py` - проверка и обновление аккаунтов из Unipile API
- `check_logs.py` - проверка логов
- `diagnose_issues.py` - диагностика проблем
- `test_connection.py` - тест подключений
- `test_sheets_connection.py` - тест подключения к Google Sheets
- `test_startup.py` - тест запуска
- `test_gemini_api.py` - тест Gemini API
- `test_cooldown_system.py` - тест системы cooldown
- `test_accounts_api.py` - тест API аккаунтов

### Управление аккаунтами
- `show_account_config.py` - показ конфигурации аккаунтов
- `verify_two_accounts.py` - проверка двух аккаунтов
- `update_second_account.py` - обновление второго аккаунта
- `fix_single_account_complete.py` - исправление одного аккаунта
- `reset_accounts_complete.py` - полный сброс аккаунтов
- `reset_linkedin_accounts.py` - сброс LinkedIn аккаунтов

### Мониторинг и анализ
- `monitor_leads.py` - мониторинг лидов
- `monitor_linkedin_limits.py` - мониторинг лимитов LinkedIn
- `analyze_notes_errors.py` - анализ ошибок в Notes колонке

### Работа с логами
- `get_logs.py` - получение логов
- `view_logs.py` - просмотр логов

## Использование

Все утилиты запускаются из корневой директории проекта:

```bash
python tools/check_linkedin_accounts.py
```

Или из папки tools:

```bash
cd tools
python check_linkedin_accounts.py
```


