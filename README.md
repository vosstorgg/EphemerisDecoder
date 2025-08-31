# Ephemeris Decoder v2.0.0

Высокопроизводительный микросервис для астрологических расчетов с оптимизированным кешированием и современной архитектурой.

## 🚀 Особенности

- **⚡ Высокая производительность**: Оптимизированное кеширование и асинхронная обработка
- **🔐 Безопасность**: API ключи с хешированием SHA256 и rate limiting
- **📊 Swiss Ephemeris**: Точные астрологические расчеты
- **🔄 Кеширование**: In-memory кеш для ускорения запросов
- **📚 Документация**: Автоматическая генерация OpenAPI/Swagger
- **🏗️ Современная архитектура**: FastAPI с Pydantic валидацией

## 🛠️ Технологии

- **FastAPI** - современный веб-фреймворк
- **Swiss Ephemeris** - точные астрологические расчеты
- **Pydantic** - валидация данных
- **Uvicorn** - ASGI сервер
- **YAML** - конфигурация

## 📦 Установка

### Требования

- Python 3.8+
- Swiss Ephemeris
- Зависимости из `requirements.txt`

### Быстрая установка

```bash
# Клонирование репозитория
git clone <repository-url>
cd EphemerisDecoder

# Установка зависимостей
pip install -r requirements.txt

# Запуск сервера
python app.py
```

## 🔑 Аутентификация

API использует систему API ключей для безопасности:

```bash
# Пример запроса с API ключом
curl -H "X-API-Key: YOUR_API_KEY" \
     "http://localhost:8000/planets?datetime_str=2024-01-15T12:00:00&lat=55.7558&lon=37.6176"
```

### Получение API ключа

1. Обратитесь к администратору для получения API ключа
2. Используйте ключ в заголовке `X-API-Key`
3. Ключи имеют ограничения по времени и количеству запросов

## 📖 API Endpoints

### Базовые эндпоинты

- `GET /planets` - позиции планет
- `GET /aspects` - аспекты между планетами
- `GET /houses` - границы домов
- `GET /moon_phase` - фаза Луны

### Натальная карта

- `POST /natal_chart` - расчет натальной карты

### Системные

- `GET /` - информация об API
- `GET /health` - проверка здоровья сервиса
- `GET /docs` - интерактивная документация

## 🚀 Использование

### Пример запроса планет

```python
import requests

url = "http://localhost:8000/planets"
headers = {"X-API-Key": "YOUR_API_KEY"}
params = {
    "datetime_str": "2024-01-15T12:00:00",
    "lat": 55.7558,
    "lon": 37.6176,
    "extra": False
}

response = requests.get(url, headers=headers, params=params)
data = response.json()
print(f"Найдено планет: {len(data['planets'])}")
```

### Пример натальной карты

```python
import requests

url = "http://localhost:8000/natal_chart"
headers = {"X-API-Key": "YOUR_API_KEY"}
data = {
    "year": 1990,
    "month": 5,
    "day": 15,
    "hour": 14,
    "minute": 30,
    "city": "Москва",
    "nation": "Россия",
    "lat": 55.7558,
    "lon": 37.6176
}

response = requests.post(url, headers=headers, json=data)
natal_chart = response.json()
```

## ⚙️ Конфигурация

### Переменные окружения

- `PORT` - порт сервера (по умолчанию 8000)
- `HOST` - хост сервера (по умолчанию 0.0.0.0)

### Конфигурация кеширования

- `cache_ttl` - время жизни кеша (3600 секунд)
- `rate_limit` - лимит запросов в минуту (200)

## 🔧 Разработка

### Запуск в режиме разработки

```bash
# Установка зависимостей для разработки
pip install -r requirements.txt

# Запуск с автоперезагрузкой
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Тестирование

```bash
# Запуск тестов
pytest

# Запуск конкретного теста
pytest tests/test_ephem.py
```

## 📊 Мониторинг

### Проверка здоровья сервиса

```bash
curl http://localhost:8000/health
```

Ответ включает:
- Статус сервиса
- Размер кеша
- Количество API ключей
- Версию приложения

## 🚀 Деплой

### Railway

Проект готов к деплою на Railway:

1. Подключите репозиторий к Railway
2. Настройте переменные окружения
3. Деплой произойдет автоматически

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "app.py"]
```

## 📚 Документация

- [API Documentation](API_DOCUMENTATION.md)
- [Authentication Guide](AUTHENTICATION_GUIDE.md)
- [Natal Chart Guide](NATAL_CHART_GUIDE.md)
- [Local Setup](LOCAL_SETUP.md)
- [Railway Deployment](RAILWAY_DEPLOYMENT.md)

## 🤝 Вклад в проект

1. Форкните репозиторий
2. Создайте ветку для новой функции
3. Внесите изменения
4. Добавьте тесты
5. Создайте Pull Request

## 📄 Лицензия

MIT License - см. файл LICENSE для деталей.

## 🆘 Поддержка

- Документация: `/docs` (Swagger UI)
- Issues: GitHub Issues
- Email: [your-email@example.com]

---

**Ephemeris Decoder v2.0.0** - Современный астрологический API с высокой производительностью и безопасностью.


