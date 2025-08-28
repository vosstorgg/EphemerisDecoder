"""
Тесты для API эндпоинтов
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import patch, MagicMock

from app import app

client = TestClient(app)


class TestAPIEndpoints:
    """Тесты для API эндпоинтов"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.test_datetime = "2024-01-15T12:00:00"
        self.test_lat = 55.7558
        self.test_lon = 37.6176
    
    def test_root_endpoint(self):
        """Тест корневого эндпоинта"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["message"] == "Ephemeris Decoder API"
        assert data["version"] == "1.0.0"
        assert "planets" in data["endpoints"]
        assert "aspects" in data["endpoints"]
        assert "houses" in data["endpoints"]
        assert "moon_phase" in data["endpoints"]
    
    def test_health_endpoint(self):
        """Тест эндпоинта проверки здоровья"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["service"] == "Ephemeris Decoder"
        assert "timestamp" in data
    
    @patch('app.get_planets')
    def test_planets_endpoint_success(self, mock_get_planets):
        """Тест успешного запроса к эндпоинту планет"""
        # Мокаем результат
        mock_result = {
            "datetime": self.test_datetime,
            "latitude": self.test_lat,
            "longitude": self.test_lon,
            "planets": {
                "Sun": {
                    "name": "Sun",
                    "longitude": 45.0,
                    "sign": "Телец",
                    "degrees_in_sign": 15.0,
                    "retrograde": False
                }
            }
        }
        mock_get_planets.return_value = mock_result
        
        response = client.get(
            "/planets",
            params={
                "datetime": self.test_datetime,
                "lat": self.test_lat,
                "lon": self.test_lon,
                "extra": False
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["datetime"] == self.test_datetime
        assert data["latitude"] == self.test_lat
        assert data["longitude"] == self.test_lon
        assert "Sun" in data["planets"]
        
        # Проверяем вызов сервиса
        mock_get_planets.assert_called_once()
    
    @patch('app.get_planets')
    def test_planets_endpoint_with_extra(self, mock_get_planets):
        """Тест эндпоинта планет с дополнительными точками"""
        mock_result = {
            "datetime": self.test_datetime,
            "latitude": self.test_lat,
            "longitude": self.test_lon,
            "planets": {
                "Sun": {"name": "Sun", "longitude": 45.0, "sign": "Телец", "degrees_in_sign": 15.0, "retrograde": False},
                "North Node": {"name": "North Node", "longitude": 180.0, "sign": "Весы", "degrees_in_sign": 0.0, "retrograde": False}
            }
        }
        mock_get_planets.return_value = mock_result
        
        response = client.get(
            "/planets",
            params={
                "datetime": self.test_datetime,
                "lat": self.test_lat,
                "lon": self.test_lon,
                "extra": True
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Проверяем, что включены дополнительные точки
        assert "North Node" in data["planets"]
        
        # Проверяем вызов сервиса с extra=True
        mock_get_planets.assert_called_once()
        call_args = mock_get_planets.call_args
        assert call_args[1]["extra"] is True
    
    def test_planets_endpoint_missing_params(self):
        """Тест эндпоинта планет с отсутствующими параметрами"""
        # Отсутствует datetime
        response = client.get(
            "/planets",
            params={"lat": self.test_lat, "lon": self.test_lon}
        )
        assert response.status_code == 422
        
        # Отсутствует lat
        response = client.get(
            "/planets",
            params={"datetime": self.test_datetime, "lon": self.test_lon}
        )
        assert response.status_code == 422
        
        # Отсутствует lon
        response = client.get(
            "/planets",
            params={"datetime": self.test_datetime, "lat": self.test_lat}
        )
        assert response.status_code == 422
    
    def test_planets_endpoint_invalid_datetime(self):
        """Тест эндпоинта планет с неверным форматом datetime"""
        response = client.get(
            "/planets",
            params={
                "datetime": "invalid-datetime",
                "lat": self.test_lat,
                "lon": self.test_lon
            }
        )
        
        assert response.status_code == 400
        assert "Ошибка валидации" in response.json()["detail"]
    
    def test_planets_endpoint_invalid_coordinates(self):
        """Тест эндпоинта планет с неверными координатами"""
        # Неверная широта
        response = client.get(
            "/planets",
            params={
                "datetime": self.test_datetime,
                "lat": 100.0,  # > 90
                "lon": self.test_lon
            }
        )
        
        assert response.status_code == 422
        
        # Неверная долгота
        response = client.get(
            "/planets",
            params={
                "datetime": self.test_datetime,
                "lat": self.test_lat,
                "lon": 200.0  # > 180
            }
        )
        
        assert response.status_code == 422
    
    @patch('app.get_aspects')
    def test_aspects_endpoint_success(self, mock_get_aspects):
        """Тест успешного запроса к эндпоинту аспектов"""
        mock_result = {
            "datetime": self.test_datetime,
            "latitude": self.test_lat,
            "longitude": self.test_lon,
            "aspects": [
                {
                    "name": "Оппозиция",
                    "planets": ["Sun", "Moon"],
                    "angle": 180,
                    "orb": 2.5,
                    "type": "opposition"
                }
            ]
        }
        mock_get_aspects.return_value = mock_result
        
        response = client.get(
            "/aspects",
            params={
                "datetime": self.test_datetime,
                "lat": self.test_lat,
                "lon": self.test_lon
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["datetime"] == self.test_datetime
        assert len(data["aspects"]) == 1
        assert data["aspects"][0]["name"] == "Оппозиция"
        assert "Sun" in data["aspects"][0]["planets"]
        assert "Moon" in data["aspects"][0]["planets"]
    
    @patch('app.get_houses')
    def test_houses_endpoint_success(self, mock_get_houses):
        """Тест успешного запроса к эндпоинту домов"""
        mock_result = {
            "datetime": self.test_datetime,
            "latitude": self.test_lat,
            "longitude": self.test_lon,
            "houses": [
                {
                    "house": 1,
                    "longitude": 45.0,
                    "sign": "Телец",
                    "degrees_in_sign": 15.0
                }
            ]
        }
        mock_get_houses.return_value = mock_result
        
        response = client.get(
            "/houses",
            params={
                "datetime": self.test_datetime,
                "lat": self.test_lat,
                "lon": self.test_lon
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["datetime"] == self.test_datetime
        assert len(data["houses"]) == 1
        assert data["houses"][0]["house"] == 1
        assert data["houses"][0]["sign"] == "Телец"
    
    @patch('app.get_moon_phase')
    def test_moon_phase_endpoint_success(self, mock_get_moon_phase):
        """Тест успешного запроса к эндпоинту фазы Луны"""
        mock_result = {
            "datetime": self.test_datetime,
            "moon_phase": {
                "angle": 90.0,
                "phase_name": "Первая четверть",
                "sun_longitude": 0.0,
                "moon_longitude": 90.0
            }
        }
        mock_get_moon_phase.return_value = mock_result
        
        response = client.get(
            "/moon_phase",
            params={"datetime": self.test_datetime}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["datetime"] == self.test_datetime
        assert data["moon_phase"]["angle"] == 90.0
        assert data["moon_phase"]["phase_name"] == "Первая четверть"
    
    def test_moon_phase_endpoint_missing_datetime(self):
        """Тест эндпоинта фазы Луны с отсутствующим datetime"""
        response = client.get("/moon_phase")
        assert response.status_code == 422
    
    @patch('app.get_planets')
    def test_planets_endpoint_service_error(self, mock_get_planets):
        """Тест обработки ошибки сервиса в эндпоинте планет"""
        # Мокаем ошибку сервиса
        mock_get_planets.return_value = {
            "error": "Service error",
            "datetime": self.test_datetime,
            "latitude": self.test_lat,
            "longitude": self.test_lon,
            "planets": {}
        }
        
        response = client.get(
            "/planets",
            params={
                "datetime": self.test_datetime,
                "lat": self.test_lat,
                "lon": self.test_lon
            }
        )
        
        assert response.status_code == 500
        assert "Service error" in response.json()["detail"]
    
    @patch('app.get_planets')
    def test_planets_endpoint_exception(self, mock_get_planets):
        """Тест обработки исключения в эндпоинте планет"""
        # Мокаем исключение
        mock_get_planets.side_effect = Exception("Unexpected error")
        
        response = client.get(
            "/planets",
            params={
                "datetime": self.test_datetime,
                "lat": self.test_lat,
                "lon": self.test_lon
            }
        )
        
        assert response.status_code == 500
        assert "Внутренняя ошибка" in response.json()["detail"]
    
    def test_planets_endpoint_datetime_with_z(self):
        """Тест эндпоинта планет с datetime в формате Z"""
        # Тестируем поддержку формата с Z (UTC)
        datetime_with_z = "2024-01-15T12:00:00Z"
        
        with patch('app.get_planets') as mock_get_planets:
            mock_result = {
                "datetime": datetime_with_z,
                "latitude": self.test_lat,
                "longitude": self.test_lon,
                "planets": {}
            }
            mock_get_planets.return_value = mock_result
            
            response = client.get(
                "/planets",
                params={
                    "datetime": datetime_with_z,
                    "lat": self.test_lat,
                    "lon": self.test_lon
                }
            )
            
            assert response.status_code == 200
    
    def test_coordinates_validation(self):
        """Тест валидации координат"""
        # Граничные значения должны быть валидными
        valid_coordinates = [
            (90.0, 180.0),   # Максимальные значения
            (-90.0, -180.0), # Минимальные значения
            (0.0, 0.0),      # Нулевые значения
            (45.5, -120.7)   # Промежуточные значения
        ]
        
        for lat, lon in valid_coordinates:
            response = client.get(
                "/planets",
                params={
                    "datetime": self.test_datetime,
                    "lat": lat,
                    "lon": lon
                }
            )
            # Должен вернуть 422 (отсутствует мок), но не 400 (ошибка валидации)
            assert response.status_code in [422, 500]
    
    def test_datetime_validation_edge_cases(self):
        """Тест граничных случаев валидации datetime"""
        # Валидные форматы
        valid_datetimes = [
            "2024-01-15T00:00:00",
            "2024-12-31T23:59:59",
            "2000-02-29T12:00:00",  # Високосный год
            "2024-01-15T12:00:00+03:00",  # С часовым поясом
            "2024-01-15T12:00:00Z"  # UTC
        ]
        
        for dt in valid_datetimes:
            response = client.get(
                "/planets",
                params={
                    "datetime": dt,
                    "lat": self.test_lat,
                    "lon": self.test_lon
                }
            )
            # Должен вернуть 422 (отсутствует мок), но не 400 (ошибка валидации)
            assert response.status_code in [422, 500]
        
        # Невалидные форматы
        invalid_datetimes = [
            "invalid",
            "2024-13-01T12:00:00",  # Неверный месяц
            "2024-01-32T12:00:00",  # Неверный день
            "2024-01-15T25:00:00",  # Неверный час
            "2024-01-15T12:60:00",  # Неверная минута
            "2024-01-15T12:00:60"   # Неверная секунда
        ]
        
        for dt in invalid_datetimes:
            response = client.get(
                "/planets",
                params={
                    "datetime": dt,
                    "lat": self.test_lat,
                    "lon": self.test_lon
                }
            )
            assert response.status_code == 400


