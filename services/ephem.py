"""
Сервис для работы со Swiss Ephemeris
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, List, Optional, Tuple
import yaml
import swisseph as swe

from utils.zodiac import degrees_to_sign_and_degrees, normalize_angle, calculate_orb

# Глобальный executor для синхронных вычислений
executor = ThreadPoolExecutor(max_workers=4)

# Основные планеты (по умолчанию)
MAIN_PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO
}

# Дополнительные точки
EXTRA_POINTS = {
    "North Node": swe.MEAN_NODE,
    "South Node": -swe.MEAN_NODE,
    "Chiron": swe.CHIRON,
    "Ceres": swe.CERES,
    "Pallas": swe.PALLAS,
    "Juno": swe.JUNO,
    "Vesta": swe.VESTA
}

# Кеш для результатов (шаг 1 час)
_cache: Dict[str, Dict] = {}
_cache_timestamps: Dict[str, datetime] = {}


def _get_cache_key(dt: datetime, lat: float, lon: float, extra: bool = False) -> str:
    """Генерирует ключ для кеша"""
    # Округляем время до часа для кеширования
    rounded_time = dt.replace(minute=0, second=0, microsecond=0)
    return f"{rounded_time.isoformat()}_{lat}_{lon}_{extra}"


def _is_cache_valid(cache_key: str) -> bool:
    """Проверяет валидность кеша (не старше 1 часа)"""
    if cache_key not in _cache_timestamps:
        return False
    
    cache_time = _cache_timestamps[cache_key]
    return datetime.now() - cache_time < timedelta(hours=1)


def _get_from_cache(cache_key: str) -> Optional[Dict]:
    """Получает данные из кеша"""
    if _is_cache_valid(cache_key):
        return _cache.get(cache_key)
    return None


def _save_to_cache(cache_key: str, data: Dict):
    """Сохраняет данные в кеш"""
    _cache[cache_key] = data
    _cache_timestamps[cache_key] = datetime.now()


def _calculate_planet_position(planet_id: int, jd: float) -> Tuple[float, float, bool]:
    """
    Вычисляет позицию планеты

    Args:
        planet_id: ID планеты в Swiss Ephemeris
        jd: Юлианская дата

    Returns:
        Tuple: (долгота, скорость, ретроградность)
    """
    try:
        # Получаем позицию планеты
        result = swe.calc_ut(jd, planet_id)
        longitude = result[0][0]  # Долгота
        speed = result[0][3]      # Скорость

        # Определяем ретроградность
        retrograde = speed < 0

        return longitude, speed, retrograde
    except Exception:
        # В случае ошибки возвращаем 0
        return 0.0, 0.0, False


def _get_illumination_percent(planet_id: int, jd: float) -> Optional[float]:
    """
    Процент освещённости диска планеты (Swiss Ephemeris swe.pheno_ut).
    Для Луны — фаза; для Венеры/Меркурия — фаза при наблюдении с Земли;
    для Солнца — 100; для внешних планет обычно ~100.

    Returns:
        Значение 0–100 или None, если явление не определено (узлы и т.п.).
    """
    try:
        swe.set_ephe_path()
        xx, ret = swe.pheno_ut(jd, planet_id)
        # xx[1] = phase = illuminated fraction (0..1)
        phase = xx[1]
        return round(float(phase) * 100.0, 2)
    except (Exception, TypeError, IndexError):
        return None


def _calculate_ascendant(jd: float, lat: float, lon: float) -> float:
    """Вычисляет асцендент"""
    try:
        # Получаем асцендент
        result = swe.houses(jd, lat, lon)[0]
        return result[0]  # Асцендент
    except Exception:
        return 0.0


def _calculate_houses(jd: float, lat: float, lon: float) -> List[Dict]:
    """Вычисляет границы домов (Whole Sign)"""
    try:
        # Получаем асцендент
        ascendant = _calculate_ascendant(jd, lat, lon)
        
        houses = []
        for i in range(12):
            house_start = (ascendant + i * 30) % 360
            sign_name, degrees_in_sign = degrees_to_sign_and_degrees(house_start)
            
            houses.append({
                "house": i + 1,
                "longitude": house_start,
                "sign": sign_name,
                "degrees_in_sign": degrees_in_sign
            })
        
        return houses
    except Exception:
        return []


def _calculate_aspects(planets_data: Dict) -> List[Dict]:
    """Вычисляет аспекты между планетами"""
    try:
        # Загружаем конфигурацию аспектов
        with open("config/aspects.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        
        aspects = []
        planet_names = list(planets_data.keys())
        
        for i, planet1 in enumerate(planet_names):
            for planet2 in planet_names[i+1:]:
                long1 = planets_data[planet1]["longitude"]
                long2 = planets_data[planet2]["longitude"]
                
                # Проверяем каждый аспект
                for aspect_name, aspect_data in config["aspects"].items():
                    target_angle = aspect_data["angle"]
                    orb = aspect_data["orb"]
                    
                    # Вычисляем орбис
                    actual_orb = calculate_orb(long1, long2)
                    target_orb = calculate_orb(actual_orb, target_angle)
                    
                    # Если орбис в пределах допустимого
                    if target_orb <= orb:
                        aspects.append({
                            "name": aspect_data["name"],
                            "planets": [planet1, planet2],
                            "angle": target_angle,
                            "orb": target_orb,
                            "type": aspect_name
                        })
        
        return aspects
    except Exception:
        return []


def _calculate_moon_phase_sync(dt: datetime) -> Dict:
    """Синхронная версия вычисления фазы Луны"""
    try:
        # Конвертируем время в юлианскую дату
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)
        
        # Убеждаемся, что Swiss Ephemeris инициализирован
        swe.set_ephe_path()
        
        # Получаем позиции Солнца и Луны
        sun_pos = swe.calc_ut(jd, swe.SUN)[0]
        moon_pos = swe.calc_ut(jd, swe.MOON)[0]
        
        sun_long = sun_pos[0]
        moon_long = moon_pos[0]
        
        # Вычисляем угол между Солнцем и Луной
        angle = normalize_angle(moon_long - sun_long)
        
        # Определяем фазу
        if angle < 45:
            phase_name = "Новолуние"
        elif angle < 90:
            phase_name = "Растущий серп"
        elif angle < 135:
            phase_name = "Первая четверть"
        elif angle < 180:
            phase_name = "Растущая Луна"
        elif angle < 225:
            phase_name = "Полнолуние"
        elif angle < 270:
            phase_name = "Убывающая Луна"
        elif angle < 315:
            phase_name = "Последняя четверть"
        else:
            phase_name = "Убывающий серп"
        
        return {
            "angle": round(angle, 2),
            "phase_name": phase_name,
            "sun_longitude": round(sun_long, 2),
            "moon_longitude": round(moon_long, 2)
        }
    except Exception as e:
        print(f"Ошибка в _calculate_moon_phase_sync: {e}")
        return {
            "angle": 0.0,
            "phase_name": "Ошибка",
            "sun_longitude": 0.0,
            "moon_longitude": 0.0
        }


def _calculate_moon_phase(jd: float) -> Dict:
    """Вычисляет фазу Луны (принимает юлианскую дату)"""
    try:
        # Убеждаемся, что Swiss Ephemeris инициализирован
        swe.set_ephe_path()
        
        # Получаем позиции Солнца и Луны
        sun_pos = swe.calc_ut(jd, swe.SUN)[0]
        moon_pos = swe.calc_ut(jd, swe.MOON)[0]
        
        sun_long = sun_pos[0]
        moon_long = moon_pos[0]
        
        # Вычисляем угол между Солнцем и Луной
        angle = normalize_angle(moon_long - sun_long)
        
        # Определяем фазу
        if angle < 45:
            phase_name = "Новолуние"
        elif angle < 90:
            phase_name = "Растущий серп"
        elif angle < 135:
            phase_name = "Первая четверть"
        elif angle < 180:
            phase_name = "Растущая Луна"
        elif angle < 225:
            phase_name = "Полнолуние"
        elif angle < 270:
            phase_name = "Убывающая Луна"
        elif angle < 315:
            phase_name = "Последняя четверть"
        else:
            phase_name = "Убывающий серп"
        
        return {
            "angle": round(angle, 2),
            "phase_name": phase_name,
            "sun_longitude": round(sun_long, 2),
            "moon_longitude": round(moon_long, 2)
        }
    except Exception as e:
        print(f"Ошибка в _calculate_moon_phase: {e}")
        return {
            "angle": 0.0,
            "phase_name": "Ошибка",
            "sun_longitude": 0.0,
            "moon_longitude": 0.0
        }


async def get_planets(dt: datetime, lat: float, lon: float, extra: bool = False) -> Dict:
    """
    Получает позиции планет
    
    Args:
        dt: Время
        lat: Широта
        lon: Долгота
        extra: Включить дополнительные точки
        
    Returns:
        Dict: Позиции планет
    """
    cache_key = _get_cache_key(dt, lat, lon, extra)
    
    # Проверяем кеш
    cached_result = _get_from_cache(cache_key)
    if cached_result:
        return cached_result
    
    # Вычисляем в отдельном потоке
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor, 
        _calculate_planets_sync, 
        dt, lat, lon, extra
    )
    
    # Сохраняем в кеш
    _save_to_cache(cache_key, result)
    
    return result


def _calculate_planets_sync(dt: datetime, lat: float, lon: float, extra: bool = False) -> Dict:
    """Синхронная версия вычисления планет"""
    try:
        # Конвертируем время в юлианскую дату
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60.0)
        
        planets_data = {}
        
        # Основные планеты
        for name, planet_id in MAIN_PLANETS.items():
            longitude, speed, retrograde = _calculate_planet_position(planet_id, jd)
            sign_name, degrees_in_sign = degrees_to_sign_and_degrees(longitude)
            illumination = _get_illumination_percent(planet_id, jd)
            planets_data[name] = {
                "name": name,
                "longitude": round(longitude, 6),
                "sign": sign_name,
                "degrees_in_sign": round(degrees_in_sign, 2),
                "retrograde": retrograde,
                "illumination_percent": illumination,
            }

        # Дополнительные точки
        if extra:
            for name, point_id in EXTRA_POINTS.items():
                longitude, speed, retrograde = _calculate_planet_position(point_id, jd)
                sign_name, degrees_in_sign = degrees_to_sign_and_degrees(longitude)
                illumination = _get_illumination_percent(point_id, jd)
                planets_data[name] = {
                    "name": name,
                    "longitude": round(longitude, 6),
                    "sign": sign_name,
                    "degrees_in_sign": round(degrees_in_sign, 2),
                    "retrograde": retrograde,
                    "illumination_percent": illumination,
                }
        
        return {
            "datetime": dt.isoformat(),
            "latitude": lat,
            "longitude": lon,
            "planets": planets_data
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "datetime": dt.isoformat(),
            "latitude": lat,
            "longitude": lon,
            "planets": {}
        }


async def get_aspects(dt: datetime, lat: float, lon: float) -> Dict:
    """Получает аспекты между планетами"""
    # Сначала получаем планеты
    planets_data = await get_planets(dt, lat, lon, extra=True)
    
    if "error" in planets_data:
        return planets_data
    
    # Вычисляем аспекты в отдельном потоке
    loop = asyncio.get_event_loop()
    aspects = await loop.run_in_executor(
        executor,
        _calculate_aspects,
        planets_data["planets"]
    )
    
    return {
        "datetime": dt.isoformat(),
        "latitude": lat,
        "longitude": lon,
        "aspects": aspects
    }


async def get_houses(dt: datetime, lat: float, lon: float) -> Dict:
    """Получает границы домов"""
    loop = asyncio.get_event_loop()
    houses = await loop.run_in_executor(
        executor,
        _calculate_houses,
        dt, lat, lon
    )
    
    return {
        "datetime": dt.isoformat(),
        "latitude": lat,
        "longitude": lon,
        "houses": houses
    }


async def get_moon_phase(dt: datetime) -> Dict:
    """Получает фазу Луны"""
    loop = asyncio.get_event_loop()
    moon_data = await loop.run_in_executor(
        executor,
        _calculate_moon_phase_sync,
        dt
    )
    
    return {
        "datetime": dt.isoformat(),
        "moon_phase": moon_data
    }


def initialize_ephemeris():
    """Инициализирует Swiss Ephemeris при старте"""
    try:
        # Устанавливаем путь к эфемеридным файлам
        swe.set_ephe_path()
        print("Swiss Ephemeris инициализирован успешно")
    except Exception as e:
        print(f"Ошибка инициализации Swiss Ephemeris: {e}")


def cleanup_ephemeris():
    """Очищает ресурсы Swiss Ephemeris"""
    try:
        swe.close()
        print("Swiss Ephemeris закрыт")
    except Exception as e:
        print(f"Ошибка при закрытии Swiss Ephemeris: {e}")


