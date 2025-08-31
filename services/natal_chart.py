"""
Сервис для работы с натальными картами
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import math

try:
    from kerykeion import AstrologicalSubject, KerykeionChartSVG, Report
except ImportError:
    print("Предупреждение: библиотека kerykeion не установлена")
    AstrologicalSubject = None

from utils.zodiac import degrees_to_sign_and_degrees

# Глобальный executor для синхронных вычислений
executor = ThreadPoolExecutor(max_workers=2)

# Соответствие планет и их символов
PLANET_SYMBOLS = {
    "Sun": "☉",
    "Moon": "☽", 
    "Mercury": "☿",
    "Venus": "♀",
    "Mars": "♂",
    "Jupiter": "♃",
    "Saturn": "♄",
    "Uranus": "♅",
    "Neptune": "♆",
    "Pluto": "♇",
    "Asc": "ASC",
    "Mc": "MC",
    "True_Node": "☊",
    "Chiron": "⚷"
}

# Соответствие знаков зодиака и их символов
ZODIAC_SYMBOLS = {
    "Aries": "♈",
    "Taurus": "♉", 
    "Gemini": "♊",
    "Cancer": "♋",
    "Leo": "♌",
    "Virgo": "♍",
    "Libra": "♎",
    "Scorpio": "♏",
    "Sagittarius": "♐",
    "Capricorn": "♑",
    "Aquarius": "♒",
    "Pisces": "♓"
}

# Соответствие домов и их значений
HOUSE_MEANINGS = {
    1: "Личность, внешность, первые впечатления",
    2: "Ценности, имущество, самооценка",
    3: "Общение, обучение, ближайшее окружение",
    4: "Дом, семья, корни, эмоциональная основа",
    5: "Творчество, дети, удовольствия, романтика",
    6: "Работа, здоровье, служение, повседневные дела",
    7: "Партнёрство, брак, открытые враги",
    8: "Трансформация, общие ресурсы, смерть и возрождение",
    9: "Философия, высшее образование, дальние путешествия",
    10: "Карьера, репутация, общественное положение",
    11: "Дружба, надежды, группы, коллективные цели",
    12: "Подсознание, скрытые враги, духовность, изоляция"
}


def _calculate_natal_chart_sync(year: int, month: int, day: int, 
                               hour: int, minute: int, city: str, 
                               nation: str, lat: float, lon: float, tz_str: str) -> Dict:
    """
    Синхронная функция для расчёта натальной карты
    
    Args:
        name: Имя человека
        year: Год рождения
        month: Месяц рождения
        day: День рождения
        hour: Час рождения
        minute: Минута рождения
        city: Город рождения
        nation: Страна рождения
        lat: Широта
        lon: Долгота
        tz_str: Часовой пояс
        
    Returns:
        Dict: Данные натальной карты
    """
    try:
        if AstrologicalSubject is None:
            raise ImportError("Библиотека kerykeion не установлена")
            
        # Создаём астрологический субъект
        subject = AstrologicalSubject(
            name="Anonymous",  # Используем анонимное имя
            year=year,
            month=month,
            day=day,
            hour=hour,
            minute=minute,
            city=city,
            nation=nation,
            lat=lat,
            lng=lon,
            tz_str=tz_str
        )
        
        # Получаем данные о планетах
        planets_data = {}
        for planet in subject.planets_list:
            planet_name = planet.name
            # Получаем полное название знака
            sign_map = {
                "Ari": "Aries", "Tau": "Taurus", "Gem": "Gemini", 
                "Can": "Cancer", "Leo": "Leo", "Vir": "Virgo",
                "Lib": "Libra", "Sco": "Scorpio", "Sag": "Sagittarius",
                "Cap": "Capricorn", "Aqu": "Aquarius", "Pis": "Pisces"
            }
            sign_full = sign_map.get(planet.sign, planet.sign)
            
            planet_info = {
                "name": planet_name,
                "longitude": round(planet.abs_pos, 6),
                "sign": sign_full,
                "sign_symbol": ZODIAC_SYMBOLS.get(sign_full, ""),
                "degrees_in_sign": round(planet.position, 2),
                "house": getattr(planet, "house", 0),
                "retrograde": getattr(planet, "retrograde", False),
                "symbol": PLANET_SYMBOLS.get(planet_name, ""),
                "element": _get_element_by_sign(sign_full),
                "quality": _get_quality_by_sign(sign_full)
            }
            planets_data[planet_name] = planet_info
        
        # Получаем данные о домах
        houses_data = []
        houses_list = subject.houses_list
        for i, house in enumerate(houses_list, 1):
            if hasattr(house, 'abs_pos'):
                longitude = house.abs_pos
            else:
                # Если нет abs_pos, используем degree_ut
                longitude = getattr(house, 'degree_ut', 0)
            
            sign_name, degrees_in_sign = degrees_to_sign_and_degrees(longitude)
            house_info = {
                "house": i,
                "longitude": round(longitude, 6),
                "sign": sign_name,
                "sign_symbol": ZODIAC_SYMBOLS.get(sign_name, ""),
                "degrees_in_sign": round(degrees_in_sign, 2),
                "meaning": HOUSE_MEANINGS.get(i, ""),
                "element": _get_element_by_sign(sign_name),
                "quality": _get_quality_by_sign(sign_name)
            }
            houses_data.append(house_info)
        
        # Аспекты пока недоступны в данной версии kerykeion
        # Можно добавить расчёт вручную в будущем
        aspects_data = []
        
        # Данные для построения круговой диаграммы
        chart_data = {
            "inner_circle": _calculate_zodiac_circle(),
            "houses_circle": _calculate_houses_circle(houses_data),
            "planets_circle": _calculate_planets_circle(planets_data),
            "aspects_lines": _calculate_aspect_lines(aspects_data, planets_data)
        }
        
        return {
            "subject_info": {
                "birth_date": f"{year}-{month:02d}-{day:02d}",
                "birth_time": f"{hour:02d}:{minute:02d}",
                "location": f"{city}, {nation}",
                "coordinates": f"{lat:.4f}, {lon:.4f}",
                "timezone": tz_str
            },
            "planets": planets_data,
            "houses": houses_data,
            "aspects": aspects_data,
            "chart_data": chart_data,
            "statistics": {
                "planets_count": len(planets_data),
                "aspects_count": len(aspects_data),
                "major_aspects_count": len([a for a in aspects_data if a["is_major"]]),
                "elements_distribution": _calculate_elements_distribution(planets_data),
                "qualities_distribution": _calculate_qualities_distribution(planets_data)
            }
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "subject_info": {
                "name": name,
                "birth_date": f"{year}-{month:02d}-{day:02d}",
                "birth_time": f"{hour:02d}:{minute:02d}",
                "location": f"{city}, {nation}",
                "coordinates": f"{lat:.4f}, {lon:.4f}",
                "timezone": tz_str
            },
            "planets": {},
            "houses": [],
            "aspects": [],
            "chart_data": {},
            "statistics": {}
        }


def _calculate_zodiac_circle() -> List[Dict]:
    """Рассчитывает данные для внешнего круга зодиака"""
    zodiac_signs = [
        {"name": "Aries", "symbol": "♈", "start": 0},
        {"name": "Taurus", "symbol": "♉", "start": 30},
        {"name": "Gemini", "symbol": "♊", "start": 60},
        {"name": "Cancer", "symbol": "♋", "start": 90},
        {"name": "Leo", "symbol": "♌", "start": 120},
        {"name": "Virgo", "symbol": "♍", "start": 150},
        {"name": "Libra", "symbol": "♎", "start": 180},
        {"name": "Scorpio", "symbol": "♏", "start": 210},
        {"name": "Sagittarius", "symbol": "♐", "start": 240},
        {"name": "Capricorn", "symbol": "♑", "start": 270},
        {"name": "Aquarius", "symbol": "♒", "start": 300},
        {"name": "Pisces", "symbol": "♓", "start": 330}
    ]
    
    circle_data = []
    for sign in zodiac_signs:
        circle_data.append({
            "name": sign["name"],
            "symbol": sign["symbol"],
            "start_angle": sign["start"],
            "end_angle": sign["start"] + 30,
            "element": _get_element_by_sign(sign["name"]),
            "quality": _get_quality_by_sign(sign["name"]),
            "color": _get_element_color(_get_element_by_sign(sign["name"]))
        })
    
    return circle_data


def _calculate_houses_circle(houses_data: List[Dict]) -> List[Dict]:
    """Рассчитывает данные для круга домов"""
    houses_circle = []
    for i, house in enumerate(houses_data):
        next_house_longitude = houses_data[(i + 1) % 12]["longitude"]
        
        # Рассчитываем размер дома
        house_size = next_house_longitude - house["longitude"]
        if house_size < 0:
            house_size += 360
            
        houses_circle.append({
            "house": house["house"],
            "start_angle": house["longitude"],
            "size": house_size,
            "sign": house["sign"],
            "meaning": house["meaning"]
        })
    
    return houses_circle


def _calculate_planets_circle(planets_data: Dict) -> List[Dict]:
    """Рассчитывает данные для размещения планет на круге"""
    planets_circle = []
    for planet_name, planet_info in planets_data.items():
        if planet_name not in ["Asc", "Mc"]:  # Исключаем углы
            planets_circle.append({
                "name": planet_name,
                "symbol": planet_info["symbol"],
                "angle": planet_info["longitude"],
                "house": planet_info["house"],
                "sign": planet_info["sign"],
                "retrograde": planet_info["retrograde"],
                "color": _get_planet_color(planet_name)
            })
    
    return sorted(planets_circle, key=lambda x: x["angle"])


def _calculate_aspect_lines(aspects_data: List[Dict], planets_data: Dict) -> List[Dict]:
    """Рассчитывает линии аспектов для диаграммы"""
    aspect_lines = []
    for aspect in aspects_data:
        if aspect["is_major"]:  # Показываем только мажорные аспекты
            planet1 = planets_data.get(aspect["planet1"])
            planet2 = planets_data.get(aspect["planet2"])
            
            if planet1 and planet2:
                aspect_lines.append({
                    "planet1": aspect["planet1"],
                    "planet2": aspect["planet2"],
                    "angle1": planet1["longitude"],
                    "angle2": planet2["longitude"],
                    "aspect_type": aspect["aspect"],
                    "orb": aspect["orb"],
                    "color": aspect["color"],
                    "line_style": _get_aspect_line_style(aspect["aspect"])
                })
    
    return aspect_lines


def _get_element_by_sign(sign: str) -> str:
    """Возвращает стихию знака зодиака"""
    fire_signs = ["Aries", "Leo", "Sagittarius"]
    earth_signs = ["Taurus", "Virgo", "Capricorn"]
    air_signs = ["Gemini", "Libra", "Aquarius"] 
    water_signs = ["Cancer", "Scorpio", "Pisces"]
    
    if sign in fire_signs:
        return "Fire"
    elif sign in earth_signs:
        return "Earth"
    elif sign in air_signs:
        return "Air"
    elif sign in water_signs:
        return "Water"
    else:
        return "Unknown"


def _get_quality_by_sign(sign: str) -> str:
    """Возвращает качество знака зодиака"""
    cardinal_signs = ["Aries", "Cancer", "Libra", "Capricorn"]
    fixed_signs = ["Taurus", "Leo", "Scorpio", "Aquarius"]
    mutable_signs = ["Gemini", "Virgo", "Sagittarius", "Pisces"]
    
    if sign in cardinal_signs:
        return "Cardinal"
    elif sign in fixed_signs:
        return "Fixed"
    elif sign in mutable_signs:
        return "Mutable"
    else:
        return "Unknown"


def _get_element_color(element: str) -> str:
    """Возвращает цвет стихии"""
    colors = {
        "Fire": "#FF4444",
        "Earth": "#8B4513", 
        "Air": "#87CEEB",
        "Water": "#4169E1"
    }
    return colors.get(element, "#808080")


def _get_planet_color(planet: str) -> str:
    """Возвращает цвет планеты"""
    colors = {
        "Sun": "#FFD700",
        "Moon": "#C0C0C0",
        "Mercury": "#FFA500",
        "Venus": "#FF69B4",
        "Mars": "#FF0000",
        "Jupiter": "#8A2BE2",
        "Saturn": "#2F4F4F",
        "Uranus": "#00CED1",
        "Neptune": "#0000FF",
        "Pluto": "#800080",
        "True_Node": "#228B22",
        "Chiron": "#DC143C"
    }
    return colors.get(planet, "#808080")


def _get_aspect_color(aspect: str) -> str:
    """Возвращает цвет аспекта"""
    colors = {
        "Conjunction": "#FF0000",
        "Opposition": "#FF0000",
        "Trine": "#0000FF",
        "Square": "#FF0000",
        "Sextile": "#0000FF",
        "Quincunx": "#808080",
        "Semisextile": "#808080"
    }
    return colors.get(aspect, "#808080")


def _get_aspect_line_style(aspect: str) -> str:
    """Возвращает стиль линии для аспекта"""
    styles = {
        "Conjunction": "solid",
        "Opposition": "solid",
        "Trine": "solid",
        "Square": "solid",
        "Sextile": "dashed",
        "Quincunx": "dotted",
        "Semisextile": "dotted"
    }
    return styles.get(aspect, "dotted")


def _is_major_aspect(aspect: str) -> bool:
    """Проверяет, является ли аспект мажорным"""
    major_aspects = ["Conjunction", "Opposition", "Trine", "Square", "Sextile"]
    return aspect in major_aspects


def _calculate_elements_distribution(planets_data: Dict) -> Dict:
    """Рассчитывает распределение планет по стихиям"""
    elements = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    
    for planet_info in planets_data.values():
        element = planet_info.get("element")
        if element in elements:
            elements[element] += 1
    
    return elements


def _calculate_qualities_distribution(planets_data: Dict) -> Dict:
    """Рассчитывает распределение планет по качествам"""
    qualities = {"Cardinal": 0, "Fixed": 0, "Mutable": 0}
    
    for planet_info in planets_data.values():
        quality = planet_info.get("quality")
        if quality in qualities:
            qualities[quality] += 1
    
    return qualities


async def calculate_natal_chart(year: int, month: int, day: int,
                               hour: int, minute: int, city: str, nation: str,
                               lat: float, lon: float, tz_str: str) -> Dict:
    """
    Асинхронная функция для расчёта натальной карты
    
    Args:
        name: Имя человека
        year: Год рождения
        month: Месяц рождения
        day: День рождения
        hour: Час рождения
        minute: Минута рождения
        city: Город рождения
        nation: Страна рождения
        lat: Широта
        lon: Долгота
        tz_str: Часовой пояс
        
    Returns:
        Dict: Данные натальной карты
    """
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        _calculate_natal_chart_sync,
        year, month, day, hour, minute, city, nation, lat, lon, tz_str
    )
    
    return result


def get_timezone_by_coordinates(lat: float, lon: float) -> str:
    """
    Простая функция для определения часового пояса по координатам
    В реальном проекте стоит использовать библиотеку timezonefinder
    """
    # Простое приближение на основе долготы
    utc_offset = round(lon / 15)
    
    # Ограничиваем диапазон
    utc_offset = max(-12, min(12, utc_offset))
    
    # Для московских координат возвращаем московское время
    if 37.0 <= lon <= 38.0 and 55.0 <= lat <= 56.0:
        return "Europe/Moscow"
    
    # Иначе возвращаем UTC для совместимости
    return "UTC"


def validate_birth_data(year: int, month: int, day: int, hour: int, minute: int) -> Tuple[bool, str]:
    """
    Валидирует данные о рождении
    
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    try:
        # Проверяем год
        if not (1900 <= year <= datetime.now().year):
            return False, f"Год должен быть между 1900 и {datetime.now().year}"
        
        # Проверяем месяц
        if not (1 <= month <= 12):
            return False, "Месяц должен быть между 1 и 12"
        
        # Проверяем день
        if not (1 <= day <= 31):
            return False, "День должен быть между 1 и 31"
        
        # Проверяем час
        if not (0 <= hour <= 23):
            return False, "Час должен быть между 0 и 23"
        
        # Проверяем минуту
        if not (0 <= minute <= 59):
            return False, "Минута должна быть между 0 и 59"
        
        # Проверяем валидность даты
        try:
            datetime(year, month, day, hour, minute)
        except ValueError as e:
            return False, f"Невалидная дата: {str(e)}"
        
        return True, ""
        
    except Exception as e:
        return False, f"Ошибка валидации: {str(e)}"
