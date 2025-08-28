# Ephemeris Decoder

Микросервис на FastAPI для работы со Swiss Ephemeris (pyswisseph), предоставляющий API для расчёта позиций планет, аспектов, домов и фаз Луны.

## Возможности

- 🌟 Расчёт позиций основных планет (Солнце, Луна, Меркурий... Плутон)
- 🔮 Дополнительные точки (узлы, фиктивные планеты) по запросу
- 📐 Расчёт аспектов между планетами
- 🏠 Определение границ домов (Whole Sign)
- 🌙 Расчёт фаз Луны
- ⚡ Кеширование результатов с шагом 1 час
- 🚀 Асинхронный API на FastAPI

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

### GET /moonphase
Расчёт фазы Луны.

**Параметры:**
- `datetime` (обязательный): Время в формате ISO 8601

## Структура проекта

```
├── app.py                 # Основное FastAPI приложение
├── services/
│   └── ephem.py          # Функции для расчётов
├── utils/
│   └── zodiac.py         # Утилиты для работы со знаками зодиака
├── config/
│   └── aspects.yaml      # Конфигурация аспектов
├── tests/                 # Тесты
├── requirements.txt       # Зависимости
└── Procfile              # Конфигурация для Railway
```

## Тестирование

```bash
pytest tests/
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


