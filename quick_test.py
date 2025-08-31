#!/usr/bin/env python3
"""
Быстрый тест одного эндпоинта для проверки работоспособности
"""
import requests
import sys
import os
import json

def quick_test(base_url, api_key):
    """Быстрая проверка API"""
    url = f"{base_url}/planets"
    headers = {"X-API-Key": api_key}
    params = {
        "datetime_str": "2024-01-15T12:00:00",
        "lat": 55.7558,
        "lon": 37.6176
    }
    
    print(f"🧪 Быстрый тест: {url}")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API работает! Получено {len(data.get('planets', []))} планет")
            return True
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Ошибка: {e}")
        return False

def test_natal_chart(base_url, api_key):
    """Тестирование натальной карты"""
    url = f"{base_url}/natal_chart"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Тестовые данные для натальной карты
    payload = {
        "year": 1990,
        "month": 6,
        "day": 15,
        "hour": 14,
        "minute": 30,
        "city": "Москва",
        "nation": "Россия",
        "lat": 55.7558,
        "lon": 37.6176,
        "timezone": "UTC"
    }
    
    print(f"🌟 Тест натальной карты: {url}")
    print(f"📋 Данные: {payload['year']}-{payload['month']:02d}-{payload['day']:02d}")
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # Проверяем основные разделы ответа
            planets_count = len(data.get('planets', {}))
            houses_count = len(data.get('houses', []))
            aspects_count = len(data.get('aspects', []))
            
            print(f"✅ Натальная карта рассчитана успешно!")
            print(f"   📍 Планет: {planets_count}")
            print(f"   🏠 Домов: {houses_count}")
            print(f"   🔗 Аспектов: {aspects_count}")
            
            # Проверяем наличие данных для построения круга
            chart_data = data.get('chart_data', {})
            if chart_data:
                print(f"   🎯 Данные для построения карты: ✅")
                print(f"       - Круг зодиака: {len(chart_data.get('inner_circle', []))} знаков")
                print(f"       - Круг домов: {len(chart_data.get('houses_circle', []))} домов") 
                print(f"       - Планеты: {len(chart_data.get('planets_circle', []))} планет")
                print(f"       - Линии аспектов: {len(chart_data.get('aspects_lines', []))} линий")
            else:
                print(f"   🎯 Данные для построения карты: ❌")
            
            # Показываем статистику
            stats = data.get('statistics', {})
            if stats:
                print(f"   📊 Статистика:")
                elements = stats.get('elements_distribution', {})
                for element, count in elements.items():
                    print(f"       - {element}: {count}")
            
            return True
        else:
            print(f"❌ Ошибка {response.status_code}: {response.text}")
            return False
            
    except Exception as e:
        print(f"💥 Ошибка: {e}")
        return False

def comprehensive_test(base_url, api_key):
    """Комплексный тест всех функций"""
    print("🚀 Запуск комплексного тестирования...")
    print("=" * 50)
    
    success_count = 0
    total_tests = 2
    
    # Тест основного API
    if quick_test(base_url, api_key):
        success_count += 1
    
    print()
    
    # Тест натальной карты
    if test_natal_chart(base_url, api_key):
        success_count += 1
    
    print()
    print("=" * 50)
    print(f"📊 Результаты: {success_count}/{total_tests} тестов прошли успешно")
    
    if success_count == total_tests:
        print("🎉 Все тесты прошли успешно!")
        return True
    else:
        print("⚠️  Некоторые тесты завершились с ошибками")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Использование: python quick_test.py <URL_приложения> [режим]")
        print("Пример: python quick_test.py https://your-app.railway.app")
        print("Пример: python quick_test.py https://your-app.railway.app natal")
        print("Пример: python quick_test.py https://your-app.railway.app full")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    mode = sys.argv[2] if len(sys.argv) > 2 else "quick"
    api_key = os.getenv("API_KEY", "YOUR_API_KEY_HERE")  # Используйте переменную окружения или замените
    
    if mode == "natal":
        success = test_natal_chart(base_url, api_key)
    elif mode == "full":
        success = comprehensive_test(base_url, api_key)
    else:
        success = quick_test(base_url, api_key)
    
    sys.exit(0 if success else 1)
