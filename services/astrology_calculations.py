"""
Сервис для астрологических расчётов: аспекты, транзиты, прогрессии
"""

from typing import Dict, List, Optional, Tuple
import math
from datetime import datetime, timedelta


class AspectCalculator:
    """Калькулятор аспектов между планетами"""

    # Мажорные аспекты с орбами
    MAJOR_ASPECTS = {
        "Conjunction": {"angle": 0, "orb": 8, "color": "#FF0000", "style": "solid"},
        "Opposition": {"angle": 180, "orb": 8, "color": "#FF0000", "style": "solid"},
        "Trine": {"angle": 120, "orb": 8, "color": "#0000FF", "style": "solid"},
        "Square": {"angle": 90, "orb": 8, "color": "#FF0000", "style": "solid"},
        "Sextile": {"angle": 60, "orb": 6, "color": "#0000FF", "style": "dashed"}
    }

    # Минорные аспекты с орбами
    MINOR_ASPECTS = {
        "Quincunx": {"angle": 150, "orb": 3, "color": "#808080", "style": "dotted"},
        "Semisextile": {"angle": 30, "orb": 3, "color": "#808080", "style": "dotted"},
        "Quintile": {"angle": 72, "orb": 2, "color": "#800080", "style": "dotted"},
        "Biquintile": {"angle": 144, "orb": 2, "color": "#800080", "style": "dotted"},
        "Sesquiquadrate": {"angle": 135, "orb": 3, "color": "#FF8C00", "style": "dotted"}
    }

    @classmethod
    def calculate_aspects(cls, planets_data: Dict) -> List[Dict]:
        """Рассчитывает все аспекты между планетами"""
        aspects = []
        planet_names = list(planets_data.keys())

        # Проверяем все пары планет
        for i, planet1_name in enumerate(planet_names):
            for planet2_name in planet_names[i+1:]:
                planet1 = planets_data[planet1_name]
                planet2 = planets_data[planet2_name]

                # Вычисляем угловое расстояние между планетами
                angle1 = planet1["longitude"]
                angle2 = planet2["longitude"]

                # Нормализуем углы
                diff = abs(angle1 - angle2)
                if diff > 180:
                    diff = 360 - diff

                # Определяем аспект и орб
                aspect_info = cls._determine_aspect(diff)
                if aspect_info:
                    aspects.append({
                        "planet1": planet1_name,
                        "planet2": planet2_name,
                        "aspect": aspect_info["aspect"],
                        "orb": aspect_info["orb"],
                        "is_major": aspect_info["is_major"],
                        "color": aspect_info["color"],
                        "style": aspect_info["style"],
                        "angle_diff": diff,
                        "description": f"{planet1_name} {aspect_info['aspect']} {planet2_name} (орб: {aspect_info['orb']:.1f}°)"
                    })

        return sorted(aspects, key=lambda x: x["orb"])  # Сортируем по орбу

    @classmethod
    def _determine_aspect(cls, angle_diff: float) -> Optional[Dict]:
        """Определяет тип аспекта по угловому расстоянию"""
        # Сначала проверяем мажорные аспекты
        for aspect_name, aspect_data in cls.MAJOR_ASPECTS.items():
            if abs(angle_diff - aspect_data["angle"]) <= aspect_data["orb"]:
                return {
                    "aspect": aspect_name,
                    "orb": abs(angle_diff - aspect_data["angle"]),
                    "is_major": True,
                    "color": aspect_data["color"],
                    "style": aspect_data["style"]
                }

        # Затем проверяем минорные аспекты
        for aspect_name, aspect_data in cls.MINOR_ASPECTS.items():
            if abs(angle_diff - aspect_data["angle"]) <= aspect_data["orb"]:
                return {
                    "aspect": aspect_name,
                    "orb": abs(angle_diff - aspect_data["angle"]),
                    "is_major": False,
                    "color": aspect_data["color"],
                    "style": aspect_data["style"]
                }

        return None


class TransitCalculator:
    """Калькулятор транзитов планет"""

    @classmethod
    def calculate_transits(cls, natal_planets: Dict, transit_planets: Dict,
                          transit_date: datetime) -> List[Dict]:
        """Рассчитывает транзиты планет к натальной карте"""
        transits = []

        for transit_planet_name, transit_planet in transit_planets.items():
            for natal_planet_name, natal_planet in natal_planets.items():
                # Вычисляем угловое расстояние
                transit_longitude = transit_planet["longitude"]
                natal_longitude = natal_planet["longitude"]

                # Нормализуем углы
                diff = abs(transit_longitude - natal_longitude)
                if diff > 180:
                    diff = 360 - diff

                # Определяем аспект
                aspect_info = AspectCalculator._determine_aspect(diff)
                if aspect_info:
                    transits.append({
                        "transit_planet": transit_planet_name,
                        "natal_planet": natal_planet_name,
                        "aspect": aspect_info["aspect"],
                        "orb": aspect_info["orb"],
                        "is_major": aspect_info["is_major"],
                        "color": aspect_info["color"],
                        "style": aspect_info["style"],
                        "transit_longitude": transit_longitude,
                        "natal_longitude": natal_longitude,
                        "angle_diff": diff,
                        "transit_date": transit_date.isoformat(),
                        "description": f"{transit_planet_name} {aspect_info['aspect']} {natal_planet_name} (орб: {aspect_info['orb']:.1f}°)"
                    })

        return sorted(transits, key=lambda x: x["orb"])

    @classmethod
    def calculate_progressions(cls, natal_planets: Dict, progression_date: datetime,
                              birth_date: datetime) -> List[Dict]:
        """Рассчитывает прогрессии планет (вторичные прогрессии)"""
        progressions = []

        # Вычисляем количество дней с рождения
        days_since_birth = (progression_date - birth_date).days

        for natal_planet_name, natal_planet in natal_planets.items():
            # Вторичные прогрессии: 1 день = 1 год
            # Луна движется примерно 1° в день
            if natal_planet_name == "Moon":
                # Для Луны используем более точный расчёт
                progressed_longitude = (natal_planet["longitude"] + days_since_birth) % 360
            else:
                # Для других планет прогрессия медленнее
                progressed_longitude = natal_planet["longitude"]

            progressions.append({
                "planet": natal_planet_name,
                "natal_longitude": natal_planet["longitude"],
                "progressed_longitude": progressed_longitude,
                "progressed_sign": cls._longitude_to_sign(progressed_longitude),
                "days_since_birth": days_since_birth,
                "progression_date": progression_date.isoformat()
            })

        return progressions

    @classmethod
    def _longitude_to_sign(cls, longitude: float) -> str:
        """Конвертирует долготу в знак зодиака"""
        signs = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        sign_index = int(longitude // 30)
        return signs[sign_index % 12]


class SynastryCalculator:
    """Калькулятор синастрии (совместимости)"""

    @classmethod
    def calculate_synastry(cls, person1_planets: Dict, person2_planets: Dict) -> Dict:
        """Рассчитывает синастрию между двумя людьми"""
        synastry = {
            "aspects": [],
            "composite_points": [],
            "compatibility_score": 0
        }

        # Рассчитываем аспекты между планетами двух людей
        for planet1_name, planet1 in person1_planets.items():
            for planet2_name, planet2 in person2_planets.items():
                # Вычисляем угловое расстояние
                angle1 = planet1["longitude"]
                angle2 = planet2["longitude"]

                # Нормализуем углы
                diff = abs(angle1 - angle2)
                if diff > 180:
                    diff = 360 - diff

                # Определяем аспект
                aspect_info = AspectCalculator._determine_aspect(diff)
                if aspect_info:
                    synastry["aspects"].append({
                        "person1_planet": planet1_name,
                        "person2_planet": planet2_name,
                        "aspect": aspect_info["aspect"],
                        "orb": aspect_info["orb"],
                        "is_major": aspect_info["is_major"],
                        "color": aspect_info["color"],
                        "style": aspect_info["style"],
                        "description": f"{planet1_name} {aspect_info['aspect']} {planet2_name}"
                    })

        # Рассчитываем композитные точки (средние позиции планет)
        for planet_name in person1_planets.keys():
            if planet_name in person2_planets:
                angle1 = person1_planets[planet_name]["longitude"]
                angle2 = person2_planets[planet_name]["longitude"]

                # Вычисляем среднюю позицию
                if abs(angle1 - angle2) > 180:
                    if angle1 < angle2:
                        angle1 += 360
                    else:
                        angle2 += 360

                composite_angle = (angle1 + angle2) / 2
                composite_angle = composite_angle % 360

                synastry["composite_points"].append({
                    "planet": planet_name,
                    "person1_longitude": person1_planets[planet_name]["longitude"],
                    "person2_longitude": person2_planets[planet_name]["longitude"],
                    "composite_longitude": composite_angle,
                    "composite_sign": TransitCalculator._longitude_to_sign(composite_angle)
                })

        # Рассчитываем общий балл совместимости
        synastry["compatibility_score"] = cls._calculate_compatibility_score(synastry["aspects"])

        return synastry

    @classmethod
    def _calculate_compatibility_score(cls, aspects: List[Dict]) -> int:
        """Рассчитывает балл совместимости на основе аспектов"""
        score = 0

        for aspect in aspects:
            if aspect["is_major"]:
                if aspect["aspect"] in ["Trine", "Sextile"]:
                    score += 3  # Гармоничные аспекты
                elif aspect["aspect"] in ["Conjunction"]:
                    score += 2  # Нейтральные аспекты
                elif aspect["aspect"] in ["Square", "Opposition"]:
                    score += 1  # Напряжённые аспекты
            else:
                score += 1  # Минорные аспекты

        # Нормализуем до 100 баллов
        max_possible_score = len(aspects) * 3
        if max_possible_score > 0:
            score = int((score / max_possible_score) * 100)

        return min(100, max(0, score))


class ReturnCalculator:
    """Калькулятор возвращений планет"""

    @classmethod
    def calculate_solar_return(cls, birth_date: datetime, return_year: int,
                              birth_lat: float, birth_lon: float) -> Dict:
        """Рассчитывает солнечное возвращение на указанный год"""
        # Солнечное возвращение происходит, когда Солнце возвращается в точку рождения
        # Обычно это происходит в день рождения или около него
        
        # Находим приблизительную дату возвращения
        return_date = datetime(return_year, birth_date.month, birth_date.day, 
                              birth_date.hour, birth_date.minute)
        
        # Корректируем время для точного возвращения Солнца
        # Это упрощённый расчёт - в реальности нужно учитывать движение Солнца
        
        return {
            "type": "Solar Return",
            "return_year": return_year,
            "return_date": return_date.isoformat(),
            "birth_lat": birth_lat,
            "birth_lon": birth_lon,
            "description": f"Солнечное возвращение {return_year} года"
        }

    @classmethod
    def calculate_lunar_return(cls, birth_date: datetime, return_date: datetime,
                              birth_lat: float, birth_lon: float) -> Dict:
        """Рассчитывает лунное возвращение"""
        # Лунное возвращение происходит каждые 27-29 дней
        # когда Луна возвращается в натальную позицию
        
        days_since_birth = (return_date - birth_date).days
        lunar_cycles = days_since_birth / 27.3  # Средний лунный цикл
        
        return {
            "type": "Lunar Return",
            "return_date": return_date.isoformat(),
            "days_since_birth": days_since_birth,
            "lunar_cycles": round(lunar_cycles, 2),
            "birth_lat": birth_lat,
            "birth_lon": birth_lon,
            "description": f"Лунное возвращение (цикл {int(lunar_cycles)})"
        }


class DirectionCalculator:
    """Калькулятор дирекций"""

    @classmethod
    def calculate_primary_directions(cls, natal_planets: Dict, 
                                   direction_date: datetime, birth_date: datetime) -> List[Dict]:
        """Рассчитывает первичные дирекции (1° = 1 год)"""
        directions = []
        
        # Вычисляем количество лет с рождения
        years_since_birth = (direction_date - birth_date).days / 365.25
        
        for planet_name, planet_info in natal_planets.items():
            # Первичные дирекции: 1° = 1 год
            directed_longitude = (planet_info["longitude"] + years_since_birth) % 360
            
            directions.append({
                "planet": planet_name,
                "natal_longitude": planet_info["longitude"],
                "directed_longitude": directed_longitude,
                "directed_sign": TransitCalculator._longitude_to_sign(directed_longitude),
                "years_since_birth": round(years_since_birth, 2),
                "direction_date": direction_date.isoformat(),
                "description": f"{planet_name} в {TransitCalculator._longitude_to_sign(directed_longitude)}"
            })
        
        return directions

    @classmethod
    def calculate_secondary_directions(cls, natal_planets: Dict,
                                     direction_date: datetime, birth_date: datetime) -> List[Dict]:
        """Рассчитывает вторичные дирекции (1 день = 1 год)"""
        directions = []
        
        # Вычисляем количество дней с рождения
        days_since_birth = (direction_date - birth_date).days
        
        for planet_name, planet_info in natal_planets.items():
            # Вторичные дирекции: 1 день = 1 год
            # Для Луны: 1° в день, для других планет медленнее
            if planet_name == "Moon":
                directed_longitude = (planet_info["longitude"] + days_since_birth) % 360
            else:
                # Для других планет используем более медленное движение
                directed_longitude = (planet_info["longitude"] + days_since_birth * 0.1) % 360
            
            directions.append({
                "planet": planet_name,
                "natal_longitude": planet_info["longitude"],
                "directed_longitude": directed_longitude,
                "directed_sign": TransitCalculator._longitude_to_sign(directed_longitude),
                "days_since_birth": days_since_birth,
                "direction_date": direction_date.isoformat(),
                "description": f"{planet_name} в {TransitCalculator._longitude_to_sign(directed_longitude)}"
            })
        
        return directions


class ArabicPartsCalculator:
    """Калькулятор арабских частей"""

    @classmethod
    def calculate_arabic_parts(cls, natal_planets: Dict, ascendant: float) -> Dict:
        """Рассчитывает основные арабские части"""
        parts = {}
        
        # Формула: Part = Asc + (Planet1 - Planet2)
        # где Asc - асцендент, Planet1 и Planet2 - позиции планет
        
        # Часть Фортуны (Part of Fortune)
        if "Sun" in natal_planets and "Moon" in natal_planets:
            sun_long = natal_planets["Sun"]["longitude"]
            moon_long = natal_planets["Moon"]["longitude"]
            
            # Для дневного рождения: Part = Asc + (Moon - Sun)
            # Для ночного рождения: Part = Asc + (Sun - Moon)
            # Упрощённо используем дневную формулу
            part_of_fortune = (ascendant + (moon_long - sun_long)) % 360
            parts["Part_of_Fortune"] = {
                "longitude": part_of_fortune,
                "sign": TransitCalculator._longitude_to_sign(part_of_fortune),
                "formula": "Asc + (Moon - Sun)",
                "description": "Часть Фортуны - показывает путь к успеху"
            }
        
        # Часть Духа (Part of Spirit)
        if "Sun" in natal_planets and "Moon" in natal_planets:
            sun_long = natal_planets["Sun"]["longitude"]
            moon_long = natal_planets["Moon"]["longitude"]
            
            # Для дневного рождения: Part = Asc + (Sun - Moon)
            part_of_spirit = (ascendant + (sun_long - moon_long)) % 360
            parts["Part_of_Spirit"] = {
                "longitude": part_of_spirit,
                "sign": TransitCalculator._longitude_to_sign(part_of_spirit),
                "formula": "Asc + (Sun - Moon)",
                "description": "Часть Духа - показывает духовные устремления"
            }
        
        # Часть Брака (Part of Marriage)
        if "Venus" in natal_planets and "Saturn" in natal_planets:
            venus_long = natal_planets["Venus"]["longitude"]
            saturn_long = natal_planets["Saturn"]["longitude"]
            
            part_of_marriage = (ascendant + (venus_long - saturn_long)) % 360
            parts["Part_of_Marriage"] = {
                "longitude": part_of_marriage,
                "sign": TransitCalculator._longitude_to_sign(part_of_marriage),
                "formula": "Asc + (Venus - Saturn)",
                "description": "Часть Брака - показывает потенциал отношений"
            }
        
        return parts


class AstrologicalUtilities:
    """Утилиты для астрологических расчётов"""

    @staticmethod
    def calculate_house_system(ascendant: float, house_system: str = "placidus") -> List[Dict]:
        """Рассчитывает систему домов"""
        houses = []

        # Простая система домов (равнодомная)
        if house_system == "equal":
            for i in range(12):
                house_start = (ascendant + i * 30) % 360
                houses.append({
                    "house": i + 1,
                    "start_longitude": house_start,
                    "end_longitude": (house_start + 30) % 360,
                    "sign": TransitCalculator._longitude_to_sign(house_start)
                })

        return houses

    @staticmethod
    def calculate_retrograde_motion(planet_longitude: float,
                                  previous_longitude: float) -> bool:
        """Определяет, ретроградна ли планета"""
        # Упрощённая логика: если планета движется назад
        diff = planet_longitude - previous_longitude

        # Нормализуем разность
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        return diff < 0

    @staticmethod
    def calculate_planetary_strength(planet: str, sign: str,
                                   house: int, aspects: List[Dict]) -> Dict:
        """Рассчитывает силу планеты"""
        strength = {
            "dignity": "neutral",
            "score": 50,
            "factors": []
        }

        # Достоинства и падения планет
        dignities = {
            "Sun": {"exaltation": "Aries", "fall": "Libra", "rulership": "Leo"},
            "Moon": {"exaltation": "Taurus", "fall": "Scorpio", "rulership": "Cancer"},
            "Mercury": {"exaltation": "Virgo", "fall": "Pisces", "rulership": ["Gemini", "Virgo"]},
            "Venus": {"exaltation": "Pisces", "fall": "Virgo", "rulership": ["Taurus", "Libra"]},
            "Mars": {"exaltation": "Capricorn", "fall": "Cancer", "rulership": ["Aries", "Scorpio"]},
            "Jupiter": {"exaltation": "Cancer", "fall": "Capricorn", "rulership": ["Sagittarius", "Pisces"]},
            "Saturn": {"exaltation": "Libra", "fall": "Aries", "rulership": ["Capricorn", "Aquarius"]}
        }

        if planet in dignities:
            planet_dignities = dignities[planet]

            if sign == planet_dignities.get("exaltation"):
                strength["dignity"] = "exaltation"
                strength["score"] += 20
                strength["factors"].append("Экзальтация")
            elif sign == planet_dignities.get("fall"):
                strength["dignity"] = "fall"
                strength["score"] -= 20
                strength["factors"].append("Падение")
            elif sign in planet_dignities.get("rulership", []):
                strength["dignity"] = "rulership"
                strength["score"] += 15
                strength["factors"].append("Управление")

        # Влияние дома
        if house in [1, 4, 7, 10]:  # Угловые дома
            strength["score"] += 10
            strength["factors"].append("Угловой дом")
        elif house in [2, 5, 8, 11]:  # Успешные дома
            strength["score"] += 5
            strength["factors"].append("Успешный дом")
        elif house in [3, 6, 9, 12]:  # Падающие дома
            strength["score"] -= 5
            strength["factors"].append("Падающий дом")

        # Влияние аспектов
        for aspect in aspects:
            if aspect["is_major"]:
                if aspect["aspect"] in ["Trine", "Sextile"]:
                    strength["score"] += 5
                    strength["factors"].append(f"Гармоничный аспект: {aspect['aspect']}")
                elif aspect["aspect"] in ["Square", "Opposition"]:
                    strength["score"] -= 3
                    strength["factors"].append(f"Напряжённый аспект: {aspect['aspect']}")

        strength["score"] = max(0, min(100, strength["score"]))

        return strength

    @staticmethod
    def calculate_eclipse_points(solar_longitude: float, lunar_longitude: float) -> Dict:
        """Рассчитывает точки затмений"""
        # Северный и южный узлы Луны
        # Упрощённо: северный узел = 0°, южный узел = 180°
        # В реальности нужно учитывать движение узлов
        
        north_node = 0.0  # Упрощённо
        south_node = 180.0
        
        # Расстояние до узлов
        solar_to_north = abs(solar_longitude - north_node)
        solar_to_south = abs(solar_longitude - south_node)
        
        if solar_to_north > 180:
            solar_to_north = 360 - solar_to_north
        if solar_to_south > 180:
            solar_to_south = 360 - solar_to_south
        
        return {
            "north_node": north_node,
            "south_node": south_node,
            "solar_to_north": solar_to_north,
            "solar_to_south": solar_to_south,
            "eclipse_potential": "high" if min(solar_to_north, solar_to_south) < 10 else "low"
        }
