# Ephemeris Decoder

Микросервис на FastAPI для работы со Swiss Ephemeris (pyswisseph), предоставляющий API для расчёта позиций планет, аспектов, домов и фаз Луны.

## Возможности

- 🌟 Расчёт позиций основных планет (Солнце, Луна, Меркурий... Плутон)
- 🔮 Дополнительные точки (узлы, фиктивные планеты) по запросу
- 📐 Расчёт аспектов между планетами
- 🏠 Определение границ домов (Whole Sign)
- 🌙 Расчёт фаз Луны
- 🔐 **API аутентификация с ключами**
- ⚡ Кеширование результатов с шагом 1 час
- 🚀 Асинхронный API на FastAPI
- 🛡️ Rate limiting и security headers
- 👑 Управление API ключами через админ-интерфейс

## Установка и запуск

### Локально

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

### На Railway

Проект автоматически развернётся при подключении к Railway.

## API Endpoints

### GET /planets
Получение позиций планет на указанное время и место.

**Параметры:**
- `datetime` (обязательный): Время в формате ISO 8601 (YYYY-MM-DDTHH:MM:SS)
- `lat` (обязательный): Широта в градусах
- `lon` (обязательный): Долгота в градусах
- `extra` (опциональный): Включить дополнительные точки (true/false)

**Пример:**
```
GET /planets?datetime=2024-01-15T12:00:00&lat=55.7558&lon=37.6176
```

### GET /aspects
Расчёт аспектов между планетами.

**Параметры:**
- `datetime` (обязательный): Время в формате ISO 8601
- `lat` (обязательный): Широта в градусах
- `lon` (обязательный): Долгота в градусах

### GET /houses
Определение границ домов (Whole Sign).

**Параметры:**
- `datetime` (обязательный): Время в формате ISO 8601
- `lat` (обязательный): Широта в градусах
- `lon` (обязательный): Долгота в градусах

### GET /moon_phase
Расчёт фазы Луны.

**Параметры:**
- `datetime` (обязательный): Время в формате ISO 8601

## 🔐 Аутентификация

Все API запросы требуют аутентификации через API ключ. Ключ должен передаваться одним из способов:

### Способы передачи ключа

1. **HTTP заголовок** (рекомендуется):
   ```
   X-API-Key: ваш_api_ключ
   ```

2. **Параметр запроса**:
   ```
   ?api_key=ваш_api_ключ
   ```

3. **Authorization header** (Bearer token):
   ```
   Authorization: Bearer ваш_api_ключ
   ```

### Получение API ключа

#### Для тестирования
При первом запуске автоматически создается демо-ключ:
```bash
python run_local.py
```

Или сгенерируйте ключ вручную:
```bash
python generate_demo_key.py
```

#### Для продакшена
Используйте административный эндпоинт для создания ключей:
```bash
curl -X POST "http://localhost:8000/admin/keys?name=MyApp&permissions=read" \
  -H "X-API-Key: ваш_админ_ключ"
```

### Примеры запросов с аутентификацией

```bash
# С заголовком X-API-Key
curl -H "X-API-Key: ваш_api_ключ" \
  "http://localhost:8000/planets?datetime=2024-01-15T12:00:00&lat=55.7558&lon=37.6176"

# С параметром api_key
curl "http://localhost:8000/planets?datetime=2024-01-15T12:00:00&lat=55.7558&lon=37.6176&api_key=ваш_api_ключ"

# С Authorization header
curl -H "Authorization: Bearer ваш_api_ключ" \
  "http://localhost:8000/planets?datetime=2024-01-15T12:00:00&lat=55.7558&lon=37.6176"
```

## 👑 Административные функции

### Создание API ключей
```http
POST /admin/keys?name=AppName&permissions=read,write&expires_days=30&rate_limit=1000
Authorization: Bearer ваш_админ_ключ
```

### Просмотр всех ключей
```http
GET /admin/keys
Authorization: Bearer ваш_админ_ключ
```

### Отзыв ключа
```http
DELETE /admin/keys/{key_id}
Authorization: Bearer ваш_админ_ключ
```

### Уровни разрешений

- **READ**: Только чтение данных (планеты, аспекты, дома, фазы Луны)
- **WRITE**: Чтение и запись (расширенные функции)
- **ADMIN**: Полный доступ + управление API ключами

## 🛡️ Безопасность

- **Rate limiting**: 100 запросов в минуту по IP + лимиты по ключам
- **Security headers**: XSS защита, CSRF защита, Content-Type sniffing
- **API key hashing**: Ключи хранятся в виде хешей SHA-256
- **Expiration**: Возможность установки срока действия ключей
- **Usage tracking**: Отслеживание использования каждого ключа

## Структура проекта

```
├── app.py                          # Основное FastAPI приложение
├── services/
│   └── ephem.py                   # Функции для расчётов эфемерид
├── utils/
│   ├── auth.py                    # 🔐 Система аутентификации и API ключей
│   ├── middleware.py              # 🛡️ Middleware для безопасности
│   └── zodiac.py                  # Утилиты для работы со знаками зодиака
├── config/
│   ├── api_keys.yaml              # 🔑 Конфигурация API ключей
│   └── aspects.yaml               # Конфигурация аспектов
├── tests/
│   ├── test_auth.py               # 🧪 Тесты аутентификации
│   ├── test_api.py                # Тесты API
│   ├── test_ephem.py              # Тесты эфемерид
│   └── test_zodiac.py             # Тесты утилит зодиака
├── examples/
│   └── api_usage.py               # 📝 Примеры использования API с аутентификацией
├── generate_demo_key.py           # 🔑 Генерация демо-API ключей
├── run_local.py                   # 🚀 Локальный запуск с авто-генерацией ключей
├── run_tests.py                   # 🧪 Запуск тестов
├── test_auth_quick.py             # ⚡ Быстрое тестирование аутентификации
├── requirements.txt                # Зависимости Python
├── Procfile                       # Конфигурация для Railway
├── AUTHENTICATION_GUIDE.md        # 📖 Полное руководство по аутентификации
├── LOCAL_SETUP.md                 # 🛠️ Локальная настройка
├── PROJECT_OVERVIEW.md            # 📋 Обзор проекта
├── RAILWAY_DEPLOYMENT.md          # 🚂 Развертывание на Railway
└── README.md                      # Документация
```

## 🧪 Тестирование

### Запуск всех тестов
```bash
python run_tests.py
```

### Запуск конкретных тестов
```bash
# Тесты аутентификации
pytest tests/test_auth.py -v

# Тесты API с аутентификацией
pytest tests/test_api.py -v

# Тесты эфемерид
pytest tests/test_ephem.py -v

# Тесты утилит зодиака
pytest tests/test_zodiac.py -v
```

### Быстрое тестирование аутентификации
```bash
python test_auth_quick.py
```

### Покрытие тестами
```bash
pip install pytest-cov
pytest tests/ --cov=. --cov-report=html
```

## 🚀 Скрипты для запуска

### Локальный запуск с авто-генерацией ключей
```bash
python run_local.py
```

### Генерация демо-API ключей
```bash
python generate_demo_key.py
```

### Примеры использования API
```bash
python examples/api_usage.py
```

## Лицензия

Copyright (C) 2024 Ephemeris Decoder

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.


