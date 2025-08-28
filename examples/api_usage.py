#!/usr/bin/env python3
"""
Примеры использования Ephemeris Decoder API
"""

import requests
import json
from datetime import datetime


class EphemerisAPIClient:
    """Клиент для работы с Ephemeris Decoder API"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def get_planets(self, dt, lat, lon, extra=False):
        """Получает позиции планет"""
        params = {
            "datetime": dt,
            "lat": lat,
            "lon": lon,
            "extra": extra
        }
        
        response = requests.get(f"{self.base_url}/planets", params=params)
        return response.json()
    
    def get_aspects(self, dt, lat, lon):
        """Получает аспекты между планетами"""
        params = {
            "datetime": dt,
            "lat": lat,
            "lon": lon
        }
        
        response = requests.get(f"{self.base_url}/aspects", params=params)
        return response.json()
    
    def get_houses(self, dt, lat, lon):
        """Получает границы домов"""
        params = {
            "datetime": dt,
            "lat": lat,
            "lon": lon
        }
        
        response = requests.get(f"{self.base_url}/houses", params=params)
        return response.json()
    
    def get_moon_phase(self, dt):
        """Получает фазу Луны"""
        params = {"datetime": dt}
        
        response = requests.get(f"{self.base_url}/moon_phase", params=params)
        return response.json()
    
    def health_check(self):
        """Проверяет здоровье сервиса"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()


def print_json(data, title):
    """Красиво выводит JSON данные"""
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    """Основная функция с примерами"""
    print("🌟 Примеры использования Ephemeris Decoder API")
    
    # Создаём клиент
    client = EphemerisAPIClient()
    
    # Тестовые данные
    test_datetime = "2024-01-15T12:00:00"
    test_lat = 55.7558  # Москва
    test_lon = 37.6176
    
    try:
        # Проверяем здоровье сервиса
        print("🔍 Проверка здоровья сервиса...")
        health = client.health_check()
        print_json(health, "Health Check")
        
        # Получаем позиции планет (только основные)
        print("\n🪐 Получение позиций основных планет...")
        planets = client.get_planets(test_datetime, test_lat, test_lon, extra=False)
        print_json(planets, "Основные планеты")
        
        # Получаем позиции планет с дополнительными точками
        print("\n🔮 Получение позиций всех планет и точек...")
        planets_extra = client.get_planets(test_datetime, test_lat, test_lon, extra=True)
        print_json(planets_extra, "Все планеты и точки")
        
        # Получаем аспекты
        print("\n📐 Получение аспектов между планетами...")
        aspects = client.get_aspects(test_datetime, test_lat, test_lon)
        print_json(aspects, "Аспекты")
        
        # Получаем дома
        print("\n🏠 Получение границ домов...")
        houses = client.get_houses(test_datetime, test_lat, test_lon)
        print_json(houses, "Дома")
        
        # Получаем фазу Луны
        print("\n🌙 Получение фазы Луны...")
        moon_phase = client.get_moon_phase(test_datetime)
        print_json(moon_phase, "Фаза Луны")
        
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения к API. Убедитесь, что сервер запущен на http://localhost:8000")
        print("Запустите сервер командой: python run_local.py")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    main()


