# Проверка кода на Python

## Быстрая проверка (аналог `yarn build`)

### Вариант 1: Makefile (рекомендуется)
```bash
make check
```

### Вариант 2: Скрипт
```bash
./scripts/check_code.sh
```

### Вариант 3: Вручную
```bash
# Проверка синтаксиса всех файлов
python3 -m py_compile main.py
find src -name "*.py" -exec python3 -m py_compile {} \;
```

## Полная проверка (после установки зависимостей)

### 1. Установить зависимости
```bash
pip install -r requirements.txt
# или
make install
```

### 2. Проверить код
```bash
make check    # Синтаксис + импорты
make lint     # Линтер (flake8)
make format   # Форматирование (black)
make test     # Тесты (pytest)
```

## Инструменты для проверки кода

### Базовые (встроенные в Python)
- `python3 -m py_compile file.py` - проверка синтаксиса
- `python3 -c "import ast; ast.parse(open('file.py').read())"` - парсинг AST

### Рекомендуемые (установить отдельно)
- **flake8** - линтер (стиль, ошибки)
  ```bash
  pip install flake8
  flake8 src/ main.py
  ```

- **black** - форматировщик кода
  ```bash
  pip install black
  black src/ main.py
  ```

- **mypy** - проверка типов
  ```bash
  pip install mypy
  mypy src/ main.py
  ```

- **pylint** - расширенный линтер
  ```bash
  pip install pylint
  pylint src/ main.py
  ```

## Что проверяется

### ✅ Текущая проверка (`make check`)
1. Синтаксис всех `.py` файлов
2. Корректность структуры проекта

### ✅ После установки зависимостей
1. Синтаксис
2. Импорты модулей
3. Структура файлов

### ✅ С дополнительными инструментами
1. Стиль кода (flake8/pylint)
2. Типы (mypy)
3. Форматирование (black)
4. Тесты (pytest)

## Примеры использования

```bash
# Быстрая проверка синтаксиса
make check

# Установить зависимости и проверить всё
make install && make check

# Проверить стиль кода
make lint

# Отформатировать код
make format

# Запустить тесты
make test

# Очистить кэш
make clean
```

## Отличие от JavaScript

В Python нет единого инструмента типа `yarn build`, но есть эквиваленты:

| JavaScript | Python |
|------------|--------|
| `yarn build` | `make check` или `python3 -m py_compile` |
| `yarn lint` | `make lint` или `flake8` |
| `yarn format` | `make format` или `black` |
| `yarn test` | `make test` или `pytest` |

