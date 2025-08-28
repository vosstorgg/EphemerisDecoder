# Локальная настройка и запуск Ephemeris Decoder

Это руководство поможет вам настроить и запустить Ephemeris Decoder локально для разработки и тестирования.

## 🛠️ Требования

### Системные требования

- **Python**: 3.8 или выше
- **ОС**: Windows, macOS или Linux
- **Память**: Минимум 2 GB RAM
- **Дисковое пространство**: Минимум 500 MB

### Программное обеспечение

- Python 3.8+
- pip (менеджер пакетов Python)
- Git (для клонирования репозитория)

## 📥 Установка

### 1. Клонирование репозитория

```bash
git clone <your-repository-url>
cd EphemerisDecoder
```

### 2. Создание виртуального окружения

#### Windows
```bash
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Проверка установки

```bash
python -c "import fastapi, uvicorn, pyswisseph, yaml; print('✅ Все зависимости установлены')"
```

## 🚀 Запуск

### Быстрый запуск

Используйте готовый скрипт:

```bash
python run_local.py
```

### Ручной запуск

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### Запуск в фоновом режиме

#### Windows
```bash
start /B uvicorn app:app --host 0.0.0.0 --port 8000
```

#### macOS/Linux
```bash
nohup uvicorn app:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
```

## 🌐 Доступ к API

После запуска API будет доступен по адресам:

- **Основной URL**: http://localhost:8000
- **Документация**: http://localhost:8000/docs
- **Альтернативная документация**: http://localhost:8000/redoc
- **Проверка здоровья**: http://localhost:8000/health

## 🧪 Тестирование

### Запуск тестов

```bash
python run_tests.py
```

### Запуск конкретных тестов

```bash
# Тесты утилит зодиака
pytest tests/test_zodiac.py -v

# Тесты сервиса эфемерид
pytest tests/test_ephem.py -v

# Тесты API
pytest tests/test_api.py -v

# Все тесты с подробным выводом
pytest tests/ -v --tb=long
```

### Покрытие тестами

```bash
pip install pytest-cov
pytest tests/ --cov=. --cov-report=html
```

Откройте `htmlcov/index.html` в браузере для просмотра отчета о покрытии.

## 📝 Примеры использования

### Запуск примеров

```bash
python examples/api_usage.py
```

### Тестирование API вручную

#### Получение позиций планет
```bash
curl "http://localhost:8000/planets?datetime=2024-01-15T12:00:00&lat=55.7558&lon=37.6176"
```

#### Получение аспектов
```bash
curl "http://localhost:8000/aspects?datetime=2024-01-15T12:00:00&lat=55.7558&lon=37.6176"
```

#### Получение домов
```bash
curl "http://localhost:8000/houses?datetime=2024-01-15T12:00:00&lat=55.7558&lon=37.6176"
```

#### Получение фазы Луны
```bash
curl "http://localhost:8000/moon_phase?datetime=2024-01-15T12:00:00"
```

## 🔧 Конфигурация

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
# Настройки приложения
DEBUG=true
LOG_LEVEL=INFO

# Настройки Swiss Ephemeris
EPHE_PATH=/path/to/ephemeris/files

# Настройки сервера
HOST=0.0.0.0
PORT=8000
```

### Настройка Swiss Ephemeris

Swiss Ephemeris автоматически загружает эфемеридные файлы. Если у вас есть локальные файлы:

1. Скачайте эфемеридные файлы с [Astro.com](https://www.astro.com/ftp/swisseph/ephe/)
2. Распакуйте в папку `ephemeris/` в корне проекта
3. Установите переменную окружения:
   ```bash
   export EPHE_PATH=./ephemeris
   ```

## 🐛 Устранение неполадок

### Ошибки установки зависимостей

#### pyswisseph не устанавливается

**Windows:**
```bash
pip install --only-binary=all pyswisseph
```

**macOS:**
```bash
brew install swisseph
pip install pyswisseph
```

**Linux:**
```bash
sudo apt-get install libswisseph-dev
pip install pyswisseph
```

#### Проблемы с компиляцией

Убедитесь, что у вас установлены инструменты разработки:

**Windows:**
- Visual Studio Build Tools
- Windows SDK

**macOS:**
```bash
xcode-select --install
```

**Linux:**
```bash
sudo apt-get install build-essential python3-dev
```

### Ошибки запуска

#### Порт уже занят

```bash
# Найти процесс, использующий порт 8000
lsof -i :8000

# Завершить процесс
kill -9 <PID>

# Или использовать другой порт
uvicorn app:app --host 0.0.0.0 --port 8001
```

#### Ошибки Swiss Ephemeris

```bash
# Проверить логи
tail -f app.log

# Проверить переменные окружения
echo $EPHE_PATH

# Запустить с отладкой
python -c "import swisseph; print(swisseph.__file__)"
```

### Проблемы с тестами

#### Тесты не запускаются

```bash
# Проверить установку pytest
pip install pytest

# Запустить с verbose
pytest -v

# Запустить конкретный тест
pytest tests/test_zodiac.py::TestZodiacUtils::test_zodiac_constants -v
```

#### Ошибки импорта

```bash
# Добавить текущую директорию в PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Или запустить из корня проекта
python -m pytest tests/
```

## 📊 Мониторинг

### Логи приложения

Логи выводятся в консоль. Для сохранения в файл:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --log-level info > app.log 2>&1
```

### Метрики производительности

Используйте встроенные эндпоинты:

- `/health` - состояние сервиса
- `/docs` - документация API
- `/redoc` - альтернативная документация

### Профилирование

```bash
pip install py-spy

# Профилирование CPU
py-spy top -- python run_local.py

# Профилирование памяти
py-spy record --format flamegraph --output profile.svg -- python run_local.py
```

## 🔄 Разработка

### Структура проекта

```
EphemerisDecoder/
├── app.py                 # Основное приложение
├── services/              # Бизнес-логика
│   └── ephem.py          # Сервис эфемерид
├── utils/                 # Утилиты
│   └── zodiac.py         # Работа со знаками зодиака
├── config/                # Конфигурация
│   └── aspects.yaml      # Аспекты и орбисы
├── tests/                 # Тесты
├── examples/              # Примеры использования
└── docs/                  # Документация
```

### Добавление новых функций

1. Создайте функцию в соответствующем модуле
2. Добавьте тесты
3. Обновите API эндпоинты
4. Обновите документацию

### Стиль кода

Проект использует:
- **Black** для форматирования
- **Flake8** для линтинга
- **isort** для сортировки импортов

```bash
pip install black flake8 isort

# Форматирование
black .

# Линтинг
flake8 .

# Сортировка импортов
isort .
```

## 📚 Дополнительные ресурсы

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Swiss Ephemeris Documentation](https://www.astro.com/swisseph/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Python Testing with pytest](https://pytest.org/)

## 🆘 Получение помощи

Если у вас возникли проблемы:

1. Проверьте логи приложения
2. Запустите тесты для диагностики
3. Создайте issue в GitHub репозитории
4. Обратитесь к документации зависимостей



