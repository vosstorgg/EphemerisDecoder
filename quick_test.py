#!/usr/bin/env python3
"""
Быстрый тест одного эндпоинта для проверки работоспособности
"""
import requests
import sys
import os

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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Использование: python quick_test.py <URL_приложения>")
        print("Пример: python quick_test.py https://your-app.railway.app")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    api_key = os.getenv("API_KEY", "YOUR_API_KEY_HERE")  # Используйте переменную окружения или замените
    
    success = quick_test(base_url, api_key)
    sys.exit(0 if success else 1)
