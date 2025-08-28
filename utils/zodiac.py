"""
Утилиты для работы со знаками зодиака
"""

ZODIAC_SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
]

ZODIAC_DEGREES = 30


def degrees_to_sign_and_degrees(longitude: float) -> tuple[str, float]:
    """
    Конвертирует долготу в знак зодиака и градусы в знаке
    
    Args:
        longitude: Долгота в градусах (0-360)
        
    Returns:
        tuple: (название знака, градусы в знаке)
    """
    # Нормализуем долготу в диапазон 0-360
    longitude = longitude % 360
    
    # Определяем знак (каждый знак занимает 30 градусов)
    sign_index = int(longitude // ZODIAC_DEGREES)
    sign_name = ZODIAC_SIGNS[sign_index]
    
    # Градусы в знаке (остаток от деления на 30)
    degrees_in_sign = longitude % ZODIAC_DEGREES
    
    return sign_name, degrees_in_sign


def normalize_angle(angle: float) -> float:
    """
    Нормализует угол в диапазон 0-360 градусов
    
    Args:
        angle: Угол в градусах
        
    Returns:
        float: Нормализованный угол
    """
    return angle % 360


def calculate_orb(angle1: float, angle2: float) -> float:
    """
    Вычисляет орбис между двумя углами
    
    Args:
        angle1: Первый угол в градусах
        angle2: Второй угол в градусах
        
    Returns:
        float: Орбис в градусах
    """
    diff = abs(angle1 - angle2)
    return min(diff, 360 - diff)


