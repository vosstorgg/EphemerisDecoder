"""
Тесты для сервиса эфемерид
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
import swisseph as swe

from services.ephem import (
    _calculate_planet_position,
    _calculate_ascendant,
    _calculate_houses,
    _calculate_aspects,
    _calculate_moon_phase,
    _get_cache_key,
    _is_cache_valid,
    _get_from_cache,
    _save_to_cache,
    MAIN_PLANETS,
    EXTRA_POINTS
)


class TestEphemerisService:
    """Тесты для сервиса эфемерид"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.test_datetime = datetime(2024, 1, 15, 12, 0, 0)
        self.test_lat = 55.7558
        self.test_lon = 37.6176
        self.test_jd = 2460324.0  # Примерная юлианская дата
    
    def test_main_planets_constants(self):
        """Тест констант основных планет"""
        assert "Sun" in MAIN_PLANETS
        assert "Moon" in MAIN_PLANETS
        assert "Mercury" in MAIN_PLANETS
        assert "Venus" in MAIN_PLANETS
        assert "Mars" in MAIN_PLANETS
        assert "Jupiter" in MAIN_PLANETS
        assert "Saturn" in MAIN_PLANETS
        assert "Uranus" in MAIN_PLANETS
        assert "Neptune" in MAIN_PLANETS
        assert "Pluto" in MAIN_PLANETS
        
        # Проверяем, что ID планет корректные
        assert MAIN_PLANETS["Sun"] == swe.SUN
        assert MAIN_PLANETS["Moon"] == swe.MOON
        assert MAIN_PLANETS["Mercury"] == swe.MERCURY
    
    def test_extra_points_constants(self):
        """Тест констант дополнительных точек"""
        assert "North Node" in EXTRA_POINTS
        assert "South Node" in EXTRA_POINTS
        assert "Chiron" in EXTRA_POINTS
        assert "Ceres" in EXTRA_POINTS
        assert "Pallas" in EXTRA_POINTS
        assert "Juno" in EXTRA_POINTS
        assert "Vesta" in EXTRA_POINTS
    
    def test_get_cache_key(self):
        """Тест генерации ключа кеша"""
        # Округляем время до часа
        rounded_time = self.test_datetime.replace(minute=0, second=0, microsecond=0)
        expected_key = f"{rounded_time.isoformat()}_{self.test_lat}_{self.test_lon}_False"
        
        key = _get_cache_key(self.test_datetime, self.test_lat, self.test_lon, False)
        assert key == expected_key
        
        # Тест с extra=True
        key_extra = _get_cache_key(self.test_datetime, self.test_lat, self.test_lon, True)
        assert key_extra.endswith("_True")
    
    def test_cache_operations(self):
        """Тест операций с кешем"""
        cache_key = "test_key"
        test_data = {"test": "data"}
        
        # Изначально кеш пустой
        assert _get_from_cache(cache_key) is None
        
        # Сохраняем данные
        _save_to_cache(cache_key, test_data)
        
        # Получаем данные
        cached_data = _get_from_cache(cache_key)
        assert cached_data == test_data
        
        # Проверяем валидность
        assert _is_cache_valid(cache_key) is True
    
    @patch('services.ephem.swe.calc_ut')
    def test_calculate_planet_position_success(self, mock_calc_ut):
        """Тест успешного вычисления позиции планеты"""
        # Мокаем результат Swiss Ephemeris
        mock_result = MagicMock()
        mock_result.__getitem__.side_effect = lambda x: MagicMock(__getitem__=lambda y: 45.0 if y == 0 else 2.5)
        mock_calc_ut.return_value = [mock_result]
        
        longitude, speed, retrograde = _calculate_planet_position(swe.SUN, self.test_jd)
        
        assert longitude == 45.0
        assert speed == 2.5
        assert retrograde is False
        
        # Проверяем вызов Swiss Ephemeris
        mock_calc_ut.assert_called_once_with(self.test_jd, swe.SUN)
    
    @patch('services.ephem.swe.calc_ut')
    def test_calculate_planet_position_retrograde(self, mock_calc_ut):
        """Тест вычисления ретроградной планеты"""
        # Мокаем результат с отрицательной скоростью (ретроградность)
        mock_result = MagicMock()
        mock_result.__getitem__.side_effect = lambda x: MagicMock(__getitem__=lambda y: 180.0 if y == 0 else -1.5)
        mock_calc_ut.return_value = [mock_result]
        
        longitude, speed, retrograde = _calculate_planet_position(swe.MARS, self.test_jd)
        
        assert longitude == 180.0
        assert speed == -1.5
        assert retrograde is True
    
    @patch('services.ephem.swe.calc_ut')
    def test_calculate_planet_position_error(self, mock_calc_ut):
        """Тест обработки ошибки при вычислении позиции планеты"""
        # Мокаем исключение
        mock_calc_ut.side_effect = Exception("Test error")
        
        longitude, speed, retrograde = _calculate_planet_position(swe.SUN, self.test_jd)
        
        # Должны получить значения по умолчанию
        assert longitude == 0.0
        assert speed == 0.0
        assert retrograde is False
    
    @patch('services.ephem.swe.houses')
    def test_calculate_ascendant_success(self, mock_houses):
        """Тест успешного вычисления асцендента"""
        # Мокаем результат Swiss Ephemeris
        mock_result = MagicMock()
        mock_result.__getitem__.return_value = 45.0
        mock_houses.return_value = [mock_result]
        
        ascendant = _calculate_ascendant(self.test_jd, self.test_lat, self.test_lon)
        
        assert ascendant == 45.0
        mock_houses.assert_called_once_with(self.test_jd, self.test_lat, self.test_lon)
    
    @patch('services.ephem.swe.houses')
    def test_calculate_ascendant_error(self, mock_houses):
        """Тест обработки ошибки при вычислении асцендента"""
        # Мокаем исключение
        mock_houses.side_effect = Exception("Test error")
        
        ascendant = _calculate_ascendant(self.test_jd, self.test_lat, self.test_lon)
        
        # Должны получить значение по умолчанию
        assert ascendant == 0.0
    
    @patch('services.ephem._calculate_ascendant')
    def test_calculate_houses_success(self, mock_ascendant):
        """Тест успешного вычисления домов"""
        # Мокаем асцендент
        mock_ascendant.return_value = 45.0
        
        houses = _calculate_houses(self.test_jd, self.test_lat, self.test_lon)
        
        assert len(houses) == 12
        
        # Проверяем первый дом (асцендент)
        assert houses[0]["house"] == 1
        assert houses[0]["longitude"] == 45.0
        assert houses[0]["sign"] == "Телец"
        assert houses[0]["degrees_in_sign"] == 15.0
        
        # Проверяем второй дом
        assert houses[1]["house"] == 2
        assert houses[1]["longitude"] == 75.0
        assert houses[1]["sign"] == "Близнецы"
        assert houses[1]["degrees_in_sign"] == 15.0
    
    @patch('services.ephem._calculate_ascendant')
    def test_calculate_houses_error(self, mock_ascendant):
        """Тест обработки ошибки при вычислении домов"""
        # Мокаем исключение
        mock_ascendant.side_effect = Exception("Test error")
        
        houses = _calculate_houses(self.test_jd, self.test_lat, self.test_lon)
        
        # Должны получить пустой список
        assert houses == []
    
    @patch('builtins.open')
    @patch('services.ephem.yaml.safe_load')
    def test_calculate_aspects_success(self, mock_yaml_load, mock_open):
        """Тест успешного вычисления аспектов"""
        # Мокаем конфигурацию аспектов
        mock_config = {
            "aspects": {
                "conjunction": {"angle": 0, "orb": 10, "name": "Соединение"},
                "opposition": {"angle": 180, "orb": 10, "name": "Оппозиция"}
            }
        }
        mock_yaml_load.return_value = mock_config
        
        # Тестовые данные планет
        planets_data = {
            "Sun": {"longitude": 45.0},
            "Moon": {"longitude": 225.0},  # Оппозиция к Солнцу
            "Mars": {"longitude": 50.0}    # Соединение с Солнцем
        }
        
        aspects = _calculate_aspects(planets_data)
        
        # Должны найти аспекты
        assert len(aspects) > 0
        
        # Проверяем, что найдена оппозиция Солнце-Луна
        sun_moon_aspects = [a for a in aspects if "Sun" in a["planets"] and "Moon" in a["planets"]]
        assert len(sun_moon_aspects) > 0
    
    @patch('builtins.open')
    def test_calculate_aspects_file_error(self, mock_open):
        """Тест обработки ошибки файла конфигурации аспектов"""
        # Мокаем ошибку открытия файла
        mock_open.side_effect = Exception("File not found")
        
        planets_data = {"Sun": {"longitude": 0.0}}
        aspects = _calculate_aspects(planets_data)
        
        # Должны получить пустой список
        assert aspects == []
    
    @patch('services.ephem.swe.calc_ut')
    def test_calculate_moon_phase_success(self, mock_calc_ut):
        """Тест успешного вычисления фазы Луны"""
        # Мокаем результаты Swiss Ephemeris
        mock_sun = MagicMock()
        mock_sun.__getitem__.side_effect = lambda x: MagicMock(__getitem__=lambda y: 0.0 if y == 0 else 0)
        
        mock_moon = MagicMock()
        mock_moon.__getitem__.side_effect = lambda x: MagicMock(__getitem__=lambda y: 90.0 if y == 0 else 0)
        
        mock_calc_ut.side_effect = [mock_sun, mock_moon]
        
        moon_data = _calculate_moon_phase(self.test_jd)
        
        assert "angle" in moon_data
        assert "phase_name" in moon_data
        assert "sun_longitude" in moon_data
        assert "moon_longitude" in moon_data
        
        # Угол между Солнцем (0°) и Луной (90°) должен быть 90°
        assert moon_data["angle"] == 90.0
        assert moon_data["phase_name"] == "Первая четверть"
    
    @patch('services.ephem.swe.calc_ut')
    def test_calculate_moon_phase_error(self, mock_calc_ut):
        """Тест обработки ошибки при вычислении фазы Луны"""
        # Мокаем исключение
        mock_calc_ut.side_effect = Exception("Test error")
        
        moon_data = _calculate_moon_phase(self.test_jd)
        
        # Должны получить данные по умолчанию
        assert moon_data["angle"] == 0.0
        assert moon_data["phase_name"] == "Ошибка"
        assert moon_data["sun_longitude"] == 0.0
        assert moon_data["moon_longitude"] == 0.0
    
    def test_cache_key_uniqueness(self):
        """Тест уникальности ключей кеша"""
        dt1 = datetime(2024, 1, 15, 12, 0, 0)
        dt2 = datetime(2024, 1, 15, 12, 30, 0)  # Разные минуты
        
        key1 = _get_cache_key(dt1, 55.0, 37.0, False)
        key2 = _get_cache_key(dt2, 55.0, 37.0, False)
        
        # Ключи должны быть одинаковыми (округляем до часа)
        assert key1 == key2
        
        # Разные координаты - разные ключи
        key3 = _get_cache_key(dt1, 56.0, 37.0, False)
        assert key1 != key3
        
        # Разные флаги extra - разные ключи
        key4 = _get_cache_key(dt1, 55.0, 37.0, True)
        assert key1 != key4


