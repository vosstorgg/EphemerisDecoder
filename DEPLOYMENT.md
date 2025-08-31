# Деплой Ephemeris Decoder v2.0.0

## 🚀 Готовность к деплою

### ✅ Проверки перед деплоем

- [x] **Структура проекта очищена**
  - Удалены тестовые файлы
  - Основной файл переименован в `app.py`
  - Удалены ненужные конфигурации

- [x] **Безопасность настроена**
  - Тестовые API ключи удалены
  - Оставлены только продакшн ключи
  - Хеширование ключей работает
  - Rate limiting настроен

- [x] **Производительность оптимизирована**
  - Кеширование работает эффективно
  - Асинхронная обработка настроена
  - Отладочные print'ы удалены

- [x] **Конфигурация деплоя**
  - `Procfile` обновлен
  - `railway.json` настроен
  - `requirements.txt` актуален

## 🎯 Платформы для деплоя

### Railway (Рекомендуется)

**Преимущества:**
- Автоматический деплой из Git
- Встроенная поддержка Python
- Простая настройка переменных окружения
- Автоматическое масштабирование

**Шаги деплоя:**
1. Подключите репозиторий к Railway
2. Настройте переменные окружения (если нужно)
3. Деплой произойдет автоматически

**Конфигурация:**
- `Procfile`: `web: python app.py`
- `railway.json`: Настроен для Python
- Health check: `/health`

### Docker

**Dockerfile:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "app.py"]
```

**Запуск:**
```bash
docker build -t ephemeris-decoder .
docker run -p 8000:8000 ephemeris-decoder
```

### Heroku

**Procfile:**
```
web: python app.py
```

**Переменные окружения:**
- `PORT` - автоматически устанавливается Heroku

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `PORT` | Порт сервера | `8000` |
| `HOST` | Хост сервера | `0.0.0.0` |

### Файлы конфигурации

- `config/api_keys.yaml` - API ключи (только хеши)
- `config/aspects.yaml` - конфигурация аспектов
- `requirements.txt` - зависимости Python

## 📊 Мониторинг

### Health Check

```bash
curl https://your-app.railway.app/health
```

**Ответ:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-31T23:10:00.000000",
  "service": "Ephemeris Decoder",
  "version": "2.0.0",
  "api_keys_count": 2,
  "cache_size": 0,
  "features": {
    "authentication": "enabled",
    "caching": "enabled",
    "rate_limiting": "enabled"
  }
}
```

### Логи

- Railway: Автоматическое логирование
- Docker: `docker logs <container-id>`
- Heroku: `heroku logs --tail`

## 🔐 Безопасность деплоя

### Проверки безопасности

- [x] API ключи хешированы
- [x] Тестовые ключи удалены
- [x] Security headers настроены
- [x] Rate limiting активен
- [x] CORS настроен

### Рекомендации

1. **Регулярно обновляйте зависимости**
2. **Мониторьте использование API ключей**
3. **Проверяйте логи на подозрительную активность**
4. **Используйте HTTPS в продакшене**

## 🚨 Troubleshooting

### Частые проблемы

**Ошибка: Port already in use**
```bash
# Проверьте, что порт свободен
netstat -ano | findstr :8000
```

**Ошибка: Module not found**
```bash
# Установите зависимости
pip install -r requirements.txt
```

**Ошибка: API key invalid**
- Проверьте конфигурацию `config/api_keys.yaml`
- Убедитесь, что используется правильный ключ

### Логи и отладка

**Включение отладочных логов:**
```python
# В app.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Проверка состояния сервиса:**
```bash
curl https://your-app.railway.app/health
```

## 📈 Масштабирование

### Railway

- Автоматическое масштабирование
- Настройка через Railway Dashboard

### Docker

```bash
# Масштабирование контейнеров
docker-compose up --scale web=3
```

### Мониторинг производительности

- Время ответа API
- Размер кеша
- Количество запросов
- Использование памяти

## 🔄 CI/CD

### GitHub Actions

```yaml
name: Deploy to Railway
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy to Railway
      uses: railway/deploy@v1
      with:
        railway_token: ${{ secrets.RAILWAY_TOKEN }}
```

### Автоматические тесты

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Run tests
      run: |
        pip install -r requirements.txt
        pytest
```

---

**Ephemeris Decoder v2.0.0** готов к деплою! 🚀
