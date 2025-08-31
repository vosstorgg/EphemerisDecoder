# Руководство по работе с натальными картами

## Обзор

Ephemeris Decoder теперь поддерживает расчёт натальных карт с помощью библиотеки **kerykeion**. Новый функционал позволяет:

- Рассчитывать полные натальные карты по данным о рождении
- Получать позиции планет, домов и аспектов
- Получать готовые данные для построения круговых диаграмм
- Анализировать распределение элементов и качеств

## Новый эндпоинт

### POST `/natal_chart`

Создаёт натальную карту на основе данных о рождении.

**Заголовки:**
```
X-API-Key: your-api-key
Content-Type: application/json
```

**Тело запроса:**
```json
{
  "year": 1990,
  "month": 6,
  "day": 15,
  "hour": 14,
  "minute": 30,
  "city": "Москва",
  "nation": "Россия",
  "lat": 55.7558,
  "lon": 37.6176,
  "timezone": "+03:00"
}
```

**Обязательные поля:**
- `year` - год рождения (1900-текущий год)
- `month` - месяц рождения (1-12)
- `day` - день рождения (1-31)
- `hour` - час рождения (0-23)
- `minute` - минута рождения (0-59)
- `city` - город рождения (1-100 символов)
- `nation` - страна рождения (1-100 символов)
- `lat` - широта места рождения (-90 до 90)
- `lon` - долгота места рождения (-180 до 180)

**Опциональные поля:**
- `timezone` - часовой пояс (будет вычислен автоматически, если не указан)

## Структура ответа

### Основные разделы

```json
{
  "subject_info": {
    "birth_date": "1990-06-15",
    "birth_time": "14:30",
    "location": "Москва, Россия",
    "coordinates": "55.7558, 37.6176",
    "timezone": "+03:00"
  },
  "planets": {
    "Sun": {
      "name": "Sun",
      "longitude": 54.123456,
      "sign": "Gemini",
      "sign_symbol": "♊",
      "degrees_in_sign": 24.12,
      "house": 10,
      "retrograde": false,
      "symbol": "☉",
      "element": "Air",
      "quality": "Mutable"
    }
    // ... остальные планеты
  },
  "houses": [
    {
      "house": 1,
      "longitude": 120.456789,
      "sign": "Leo",
      "sign_symbol": "♌",
      "degrees_in_sign": 0.46,
      "meaning": "Личность, внешность, первые впечатления",
      "element": "Fire",
      "quality": "Fixed"
    }
    // ... остальные дома
  ],
  "aspects": [
    {
      "planet1": "Sun",
      "planet2": "Moon",
      "aspect": "Trine",
      "orb": 2.34,
      "aspect_degrees": 120,
      "color": "#0000FF",
      "is_major": true
    }
    // ... остальные аспекты
  ],
  "chart_data": {
    "inner_circle": [...],    // Данные для внешнего круга зодиака
    "houses_circle": [...],   // Данные для круга домов
    "planets_circle": [...],  // Данные для размещения планет
    "aspects_lines": [...]    // Данные для линий аспектов
  },
  "statistics": {
    "planets_count": 12,
    "aspects_count": 15,
    "major_aspects_count": 8,
    "elements_distribution": {
      "Fire": 3,
      "Earth": 2,
      "Air": 4,
      "Water": 3
    },
    "qualities_distribution": {
      "Cardinal": 4,
      "Fixed": 5,
      "Mutable": 3
    }
  }
}
```

### Данные для построения диаграммы

Раздел `chart_data` содержит готовые данные для построения круговой натальной карты:

#### `inner_circle` - Внешний круг зодиака
```json
[
  {
    "name": "Aries",
    "symbol": "♈",
    "start_angle": 0,
    "end_angle": 30,
    "element": "Fire",
    "quality": "Cardinal",
    "color": "#FF4444"
  }
  // ... остальные знаки
]
```

#### `houses_circle` - Круг домов
```json
[
  {
    "house": 1,
    "start_angle": 120.45,
    "size": 28.67,
    "sign": "Leo",
    "meaning": "Личность, внешность..."
  }
  // ... остальные дома
]
```

#### `planets_circle` - Размещение планет
```json
[
  {
    "name": "Sun",
    "symbol": "☉",
    "angle": 54.12,
    "house": 10,
    "sign": "Gemini",
    "retrograde": false,
    "color": "#FFD700"
  }
  // ... остальные планеты
]
```

#### `aspects_lines` - Линии аспектов
```json
[
  {
    "planet1": "Sun",
    "planet2": "Moon",
    "angle1": 54.12,
    "angle2": 234.56,
    "aspect_type": "Trine",
    "orb": 2.34,
    "color": "#0000FF",
    "line_style": "solid"
  }
  // ... остальные аспекты
]
```

## Примеры использования

### Python с requests

```python
import requests

url = "http://localhost:8000/natal_chart"
headers = {
    "X-API-Key": "your-api-key",
    "Content-Type": "application/json"
}

data = {
    "year": 1985,
    "month": 3,
    "day": 21,
    "hour": 12,
    "minute": 0,
    "city": "Москва",
    "nation": "Россия",
    "lat": 55.7558,
    "lon": 37.6176
}

response = requests.post(url, headers=headers, json=data)
natal_chart = response.json()
```

### JavaScript с fetch

```javascript
const response = await fetch('http://localhost:8000/natal_chart', {
  method: 'POST',
  headers: {
    'X-API-Key': 'your-api-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    year: 1985,
    month: 3,
    day: 21,
    hour: 12,
    minute: 0,
    city: "Москва",
    nation: "Россия",
    lat: 55.7558,
    lon: 37.6176
  })
});

const natalChart = await response.json();
```

### cURL

```bash
curl -X POST "http://localhost:8000/natal_chart" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "year": 1985,
    "month": 3,
    "day": 21,
    "hour": 12,
    "minute": 0,
    "city": "Москва",
    "nation": "Россия",
    "lat": 55.7558,
    "lon": 37.6176
  }'
```

## Тестирование

### Быстрый тест натальной карты

```bash
python quick_test.py http://localhost:8000 natal
```

### Полное тестирование

```bash
python quick_test.py http://localhost:8000 full
```

### Пример использования

```bash
cd examples
python natal_chart_usage.py
```

## Построение визуализации

Данные из раздела `chart_data` можно использовать для построения круговых диаграмм с помощью различных библиотек:

### С matplotlib (Python)

```python
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

def draw_natal_chart(chart_data):
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
    
    # Рисуем знаки зодиака
    for sign in chart_data['inner_circle']:
        theta = np.radians(sign['start_angle'])
        width = np.radians(30)
        ax.bar(theta, 1, width=width, bottom=0.8, alpha=0.3, color=sign['color'])
    
    # Размещаем планеты
    for planet in chart_data['planets_circle']:
        theta = np.radians(planet['angle'])
        ax.scatter(theta, 0.6, s=100, color=planet['color'])
        ax.text(theta, 0.7, planet['symbol'], ha='center', va='center', fontsize=12)
    
    # Рисуем линии аспектов
    for aspect in chart_data['aspects_lines']:
        theta1 = np.radians(aspect['angle1'])
        theta2 = np.radians(aspect['angle2'])
        ax.plot([theta1, theta2], [0.5, 0.5], color=aspect['color'], alpha=0.7)
    
    ax.set_ylim(0, 1)
    ax.set_theta_zero_location('E')  # 0° справа (Овен)
    ax.set_theta_direction(-1)       # По часовой стрелке
    
    plt.title("Натальная карта", pad=20)
    plt.show()
```

### С D3.js (JavaScript)

```javascript
function drawNatalChart(chartData, containerId) {
    const svg = d3.select(`#${containerId}`)
        .append('svg')
        .attr('width', 500)
        .attr('height', 500);
    
    const center = { x: 250, y: 250 };
    const radius = 200;
    
    // Рисуем круг зодиака
    chartData.inner_circle.forEach(sign => {
        const startAngle = sign.start_angle * Math.PI / 180;
        const endAngle = sign.end_angle * Math.PI / 180;
        
        const arc = d3.arc()
            .innerRadius(radius - 30)
            .outerRadius(radius)
            .startAngle(startAngle)
            .endAngle(endAngle);
        
        svg.append('path')
            .attr('d', arc)
            .attr('transform', `translate(${center.x}, ${center.y})`)
            .attr('fill', sign.color)
            .attr('opacity', 0.3);
    });
    
    // Размещаем планеты
    chartData.planets_circle.forEach(planet => {
        const angle = planet.angle * Math.PI / 180;
        const x = center.x + (radius - 50) * Math.cos(angle);
        const y = center.y + (radius - 50) * Math.sin(angle);
        
        svg.append('circle')
            .attr('cx', x)
            .attr('cy', y)
            .attr('r', 8)
            .attr('fill', planet.color);
        
        svg.append('text')
            .attr('x', x)
            .attr('y', y + 20)
            .attr('text-anchor', 'middle')
            .text(planet.symbol);
    });
}
```

## Часовые пояса

Если часовой пояс не указан в запросе, система автоматически определит его на основе координат места рождения. Для более точных результатов рекомендуется указывать часовой пояс явно в формате `+HH:MM` или `-HH:MM`.

## Ограничения и рекомендации

1. **Годы рождения**: поддерживаются года с 1900 по текущий
2. **Координаты**: убедитесь в точности координат места рождения
3. **Время**: для наиболее точных результатов используйте точное время рождения
4. **Производительность**: расчёт натальной карты может занимать 1-3 секунды

## Коды ошибок

- `400` - Неверные входные данные или параметры
- `500` - Внутренняя ошибка сервера (часто связана с отсутствием библиотеки kerykeion)

## Установка зависимостей

Убедитесь, что установлена библиотека kerykeion:

```bash
pip install kerykeion==4.11.0
```

Или используйте обновлённый `requirements.txt`:

```bash
pip install -r requirements.txt
```
