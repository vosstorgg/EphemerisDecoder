# 📚 Документация API Ephemeris Decoder

## 🌟 Обзор

Ephemeris Decoder - это мощный API для астрологических расчётов, включающий:
- Натальные карты
- Аспекты между планетами
- Транзиты
- Прогрессии
- Синастрию (совместимость)
- Силу планет

## 🔑 Аутентификация

Все endpoints требуют валидный API ключ в заголовке или параметре `api_key`.

### Получение API ключа
```bash
# Создание ключа (требует ADMIN права)
POST /admin/keys?name=my_key&permissions=read&rate_limit=100
```

## 📐 Структура объекта планеты

Во всех ответах, где возвращаются планеты (например, `/planets`, `transit_planets`, планеты в натальной карте из ephem), каждый объект планеты имеет вид:

| Поле | Тип | Описание |
|------|-----|----------|
| `name` | string | Название планеты (Sun, Moon, Mercury, …) |
| `longitude` | float | Эклиптическая долгота (°) |
| `sign` | string | Знак зодиака (Aries, Taurus, …) |
| `degrees_in_sign` | float | Градусы внутри знака |
| `retrograde` | boolean | Ретроградность |
| `illumination_percent` | float \| null | Процент освещённости диска (0–100). Луна — фаза; Меркурий/Венера — фаза с Земли; Солнце — 100; внешние планеты — ~100; узлы и т.п. — `null`. Расчёт: Swiss Ephemeris `swe.pheno_ut`. |

## 📊 Базовые эндпоинты

### GET `/planets`

Позиции планет на заданные время и место.

**Параметры:**
- `datetime` (str): Время в формате ISO 8601
- `lat` (float): Широта (-90 … 90)
- `lon` (float): Долгота (-180 … 180)
- `extra` (bool, опционально): Включить узлы, Хирон, Лилит, Цереру, Палладу, Юнону, Весту

**Ответ:** `{ "datetime", "latitude", "longitude", "planets": { "Sun": { ... }, ... } }`  
Каждая планета в `planets` — объект по структуре выше (включая `illumination_percent`).

### GET `/aspects`

Аспекты между планетами (включая Lilith, Chiron и др. при `extra=true` в `/planets`). Для каждой пары возвращается только самый точный аспект (с наименьшим орбисом). Параметры: `datetime`, `lat`, `lon`.

### GET `/houses`

Границы домов (система Placidus; при широте >66° — Equal House).

**Параметры:** `datetime`, `lat`, `lon`

**Ответ:** `{ "datetime", "latitude", "longitude", "house_system", "houses": [...] }`

- `house_system` — `"Placidus"` или `"Equal"` (при фоллбеке на высоких широтах)

### GET `/moon_phase`

Фаза Луны. Параметр: `datetime`.

---

## 📊 Основные Endpoints

### 1. 🚀 Транзиты - `/transits`

Рассчитывает транзиты текущих планет к натальной карте.

**Метод:** `GET`

**Параметры:**
- `natal_year` (int): Год рождения
- `natal_month` (int): Месяц рождения (1-12)
- `natal_day` (int): День рождения (1-31)
- `natal_hour` (int): Час рождения (0-23)
- `natal_minute` (int): Минута рождения (0-59)
- `natal_city` (str): Город рождения
- `natal_nation` (str): Страна рождения
- `natal_lat` (float): Широта места рождения (-90 до 90)
- `natal_lon` (float): Долгота места рождения (-180 до 180)
- `transit_date` (str): Дата транзита в формате ISO 8601
- `natal_timezone` (str, опционально): Часовой пояс рождения
- `transit_timezone` (str, опционально): Часовой пояс транзита
- `api_key` (str): API ключ

**Пример запроса:**
```bash
GET /transits?natal_year=1990&natal_month=6&natal_day=15&natal_hour=14&natal_minute=30&natal_city=Москва&natal_nation=Россия&natal_lat=55.7558&natal_lon=37.6176&transit_date=2024-01-01T12:00:00&api_key=your_api_key
```

**Ответ:**
```json
{
  "natal_chart": {...},
  "transit_date": "2024-01-01T12:00:00",
  "transit_planets": {...},
  "transits": [
    {
      "transit_planet": "Venus",
      "natal_planet": "Moon",
      "aspect": "Biquintile",
      "orb": 0.2,
      "is_major": false,
      "color": "#800080",
      "style": "dotted",
      "description": "Venus Biquintile Moon (орб: 0.2°)"
    }
  ],
  "summary": {
    "total_transits": 60,
    "major_aspects": 41,
    "minor_aspects": 19
  }
}
```

### 2. 🌙 Прогрессии - `/progressions`

Рассчитывает вторичные прогрессии планет (1 день = 1 год).

**Метод:** `GET`

**Параметры:**
- `birth_year` (int): Год рождения
- `birth_month` (int): Месяц рождения (1-12)
- `birth_day` (int): День рождения (1-31)
- `birth_hour` (int): Час рождения (0-23)
- `birth_minute` (int): Минута рождения (0-59)
- `birth_city` (str): Город рождения
- `birth_nation` (str): Страна рождения
- `birth_lat` (float): Широта места рождения (-90 до 90)
- `birth_lon` (float): Долгота места рождения (-180 до 180)
- `progression_date` (str): Дата прогрессии в формате ISO 8601
- `birth_timezone` (str, опционально): Часовой пояс рождения
- `api_key` (str): API ключ

**Пример запроса:**
```bash
GET /progressions?birth_year=1990&birth_month=6&birth_day=15&birth_hour=14&birth_minute=30&birth_city=Москва&birth_nation=Россия&birth_lat=55.7558&birth_lon=37.6176&progression_date=2020-06-15T00:00:00&api_key=your_api_key
```

**Ответ:**
```json
{
  "natal_chart": {...},
  "progressions": [
    {
      "planet": "Sun",
      "natal_longitude": 84.1,
      "progressed_longitude": 84.1,
      "progressed_sign": "Gemini",
      "days_since_birth": 10957,
      "progression_date": "2020-06-15T00:00:00"
    }
  ],
  "summary": {
    "total_planets": 13,
    "days_since_birth": 10957
  }
}
```

### 3. 💕 Синастрия - `/synastry`

Рассчитывает совместимость между двумя людьми.

**Метод:** `POST`

**Тело запроса:**
```json
{
  "person1": {
    "year": 1990,
    "month": 6,
    "day": 15,
    "hour": 14,
    "minute": 30,
    "city": "Москва",
    "nation": "Россия",
    "lat": 55.7558,
    "lon": 37.6176,
    "timezone": "Europe/Moscow"
  },
  "person2": {
    "year": 1992,
    "month": 8,
    "day": 20,
    "hour": 10,
    "minute": 15,
    "city": "Санкт-Петербург",
    "nation": "Россия",
    "lat": 59.9311,
    "lon": 30.3609,
    "timezone": "Europe/Moscow"
  },
  "api_key": "your_api_key"
}
```

**Ответ:**
```json
{
  "person1": {...},
  "person2": {...},
  "synastry": {
    "aspects": [
      {
        "person1_planet": "Sun",
        "person2_planet": "Sun",
        "aspect": "Sextile",
        "orb": 1.2,
        "is_major": true,
        "color": "#0000FF",
        "style": "dashed",
        "description": "Sun Sextile Sun"
      }
    ],
    "composite_points": [
      {
        "planet": "Sun",
        "person1_longitude": 84.1,
        "person2_longitude": 147.8,
        "composite_longitude": 115.95,
        "composite_sign": "Leo"
      }
    ],
    "compatibility_score": 61
  },
  "summary": {
    "total_aspects": 90,
    "major_aspects": 70,
    "compatibility_score": 61,
    "composite_points": 13
  }
}
```

### 4. ⚡ Сила планет - `/planetary_strength`

Рассчитывает силу и достоинство планет в натальной карте.

**Метод:** `GET`

**Параметры:**
- `year` (int): Год рождения
- `month` (int): Месяц рождения (1-12)
- `day` (int): День рождения (1-31)
- `hour` (int): Час рождения (0-23)
- `minute` (int): Минута рождения (0-59)
- `city` (str): Город рождения
- `nation` (str): Страна рождения
- `lat` (float): Широта места рождения (-90 до 90)
- `lon` (float): Долгота места рождения (-180 до 180)
- `timezone` (str, опционально): Часовой пояс
- `api_key` (str): API ключ

**Пример запроса:**
```bash
GET /planetary_strength?year=1990&month=6&day=15&hour=14&minute=30&city=Москва&nation=Россия&lat=55.7558&lon=37.6176&api_key=your_api_key
```

**Ответ:**
```json
{
  "natal_chart": {...},
  "planets_strength": {
    "Venus": {
      "planet_info": {...},
      "strength": {
        "dignity": "rulership",
        "score": 87,
        "factors": ["Управление", "Угловой дом", "Гармоничный аспект: Trine"]
      }
    }
  },
  "summary": {
    "total_planets": 13,
    "strongest_planet": "Venus",
    "weakest_planet": "Uranus"
  }
}
```

## 🔮 Типы аспектов

### Мажорные аспекты
- **Conjunction** (Соединение): 0° ± 8°, красный, сплошная линия
- **Opposition** (Оппозиция): 180° ± 8°, красный, сплошная линия
- **Trine** (Трин): 120° ± 8°, синий, сплошная линия
- **Square** (Квадрат): 90° ± 8°, красный, сплошная линия
- **Sextile** (Секстиль): 60° ± 6°, синий, пунктирная линия

### Минорные аспекты
- **Quincunx** (Квинкункс): 150° ± 3°, серый, точечная линия
- **Semisextile** (Полусекстиль): 30° ± 3°, серый, точечная линия
- **Quintile** (Квинтиль): 72° ± 2°, фиолетовый, точечная линия
- **Biquintile** (Биквинтиль): 144° ± 2°, фиолетовый, точечная линия
- **Sesquiquadrate** (Сесквиквадрат): 135° ± 3°, оранжевый, точечная линия

## 🏠 Система домов

Эндпоинт `/houses` использует **Placidus** по умолчанию. При широте >66° (полярные регионы) автоматически применяется **Equal House**, т.к. Placidus там не работает. В ответе поле `house_system` указывает использованную систему.

- **Угловые дома** (1, 4, 7, 10): +10 к силе планеты
- **Успешные дома** (2, 5, 8, 11): +5 к силе планеты
- **Падающие дома** (3, 6, 9, 12): -5 к силе планеты

## 🌟 Достоинства планет

### Солнце
- **Экзальтация**: Овен (+20)
- **Падение**: Весы (-20)
- **Управление**: Лев (+15)

### Луна
- **Экзальтация**: Телец (+20)
- **Падение**: Скорпион (-20)
- **Управление**: Рак (+15)

### Меркурий
- **Экзальтация**: Дева (+20)
- **Падение**: Рыбы (-20)
- **Управление**: Близнецы, Дева (+15)

### Венера
- **Экзальтация**: Рыбы (+20)
- **Падение**: Дева (-20)
- **Управление**: Телец, Весы (+15)

### Марс
- **Экзальтация**: Козерог (+20)
- **Падение**: Рак (-20)
- **Управление**: Овен, Скорпион (+15)

### Юпитер
- **Экзальтация**: Рак (+20)
- **Падение**: Козерог (-20)
- **Управление**: Стрелец, Рыбы (+15)

### Сатурн
- **Экзальтация**: Весы (+20)
- **Падение**: Овен (-20)
- **Управление**: Козерог, Водолей (+15)

## 🚀 Примеры использования

### Python
```python
import requests

# Получение транзитов
response = requests.get(
    "http://localhost:8000/transits",
    params={
        "natal_year": 1990,
        "natal_month": 6,
        "natal_day": 15,
        "natal_hour": 14,
        "natal_minute": 30,
        "natal_city": "Москва",
        "natal_nation": "Россия",
        "natal_lat": 55.7558,
        "natal_lon": 37.6176,
        "transit_date": "2024-01-01T12:00:00",
        "api_key": "your_api_key"
    }
)

if response.status_code == 200:
    transits = response.json()
    print(f"Найдено {transits['summary']['total_transits']} транзитов")
```

### JavaScript
```javascript
// Получение прогрессий
const response = await fetch(
    `http://localhost:8000/progressions?birth_year=1990&birth_month=6&birth_day=15&birth_hour=14&birth_minute=30&birth_city=Москва&birth_nation=Россия&birth_lat=55.7558&birth_lon=37.6176&progression_date=2020-06-15T00:00:00&api_key=your_api_key`
);

if (response.ok) {
    const progressions = await response.json();
    console.log(`Прогрессии для ${progressions['summary']['total_planets']} планет`);
}
```

### cURL
```bash
# Синастрия
curl -X POST "http://localhost:8000/synastry" \
  -H "Content-Type: application/json" \
  -d '{
    "person1": {
      "year": 1990, "month": 6, "day": 15, "hour": 14, "minute": 30,
      "city": "Москва", "nation": "Россия", "lat": 55.7558, "lon": 37.6176
    },
    "person2": {
      "year": 1992, "month": 8, "day": 20, "hour": 10, "minute": 15,
      "city": "Санкт-Петербург", "nation": "Россия", "lat": 59.9311, "lon": 30.3609
    },
    "api_key": "your_api_key"
  }'
```

## ⚠️ Ограничения и рекомендации

1. **Время**: Формат ISO 8601; учитываются секунды и микросекунды для максимальной точности
2. **Часовые пояса**: Рекомендуется указывать точный часовой пояс для точных расчётов
3. **Географические координаты**: Используйте точные координаты для расчёта домов; при широте >66° используется Equal House
4. **API ключи**: Храните ключи в безопасном месте
5. **Лимиты**: Соблюдайте установленные лимиты запросов

## 🔧 Устранение неполадок

### Ошибка 401 Unauthorized
- Проверьте правильность API ключа
- Убедитесь, что ключ не истёк
- Проверьте права доступа

### Ошибка 400 Bad Request
- Проверьте корректность параметров
- Убедитесь, что даты в правильном формате
- Проверьте диапазоны значений

### Ошибка 500 Internal Server Error
- Проверьте логи сервера
- Убедитесь, что все зависимости установлены
- Проверьте корректность данных рождения

## 📞 Поддержка

При возникновении проблем:
1. Проверьте документацию
2. Изучите логи сервера
3. Обратитесь к администратору системы

---

**Версия API:** 1.0.0  
**Последнее обновление:** 2024

