#!/usr/bin/env python3
"""
Скрипт для проверки работоспособности Ephemeris Decoder API на продакшене
"""
import requests
import json
from datetime import datetime, timezone
import sys
import os

# Конфигурация
API_KEY = os.getenv("API_KEY", "YOUR_API_KEY_HERE")  # Используйте переменную окружения или замените
BASE_URL = "https://ephemerisdecoder.up.railway.app"  # ЗАМЕНИТЕ НА ВАШЕ РЕАЛЬНОЕ URL

# Заголовки для аутентификации
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_endpoint(url, description):
    """Тестирует один эндпоинт"""
    print(f"\n🧪 Тестируем: {description}")
    print(f"📡 URL: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        
        print(f"📊 Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Успешно!")
            print(f"📦 Размер ответа: {len(json.dumps(data))} символов")
            
            # Показываем краткую информацию о данных
            if "planets" in data:
                print(f"🪐 Планет получено: {len(data['planets'])}")
            elif "aspects" in data:
                print(f"🔗 Аспектов получено: {len(data['aspects'])}")
            elif "houses" in data:
                print(f"🏠 Домов получено: {len(data['houses'])}")
            elif "phase" in data:
                print(f"🌙 Фаза луны: {data['phase']['name']} ({data['phase']['illumination']:.1f}%)")
            
            return True
        else:
            print(f"❌ Ошибка HTTP {response.status_code}")
            try:
                error_data = response.json()
                print(f"💬 Ответ: {error_data}")
            except:
                print(f"💬 Ответ: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Таймаут запроса (30 сек)")
        return False
    except requests.exceptions.ConnectionError:
        print("🌐 Ошибка подключения")
        return False
    except Exception as e:
        print(f"💥 Неожиданная ошибка: {e}")
        return False

def main():
    print("🚀 ПРОВЕРКА EPHEMERIS DECODER API НА ПРОДАКШЕНЕ")
    print("=" * 60)
    
    # Проверяем конфигурацию
    if "YOUR_API_KEY_HERE" in API_KEY:
        print("⚠️  ВНИМАНИЕ! Установите API ключ!")
        print("   Способ 1: Установите переменную окружения: set API_KEY=ваш_ключ")
        print("   Способ 2: Замените API_KEY в коде на ваш реальный ключ")
        return
    
    if "your-railway-app-url" in BASE_URL:
        print("⚠️  ВНИМАНИЕ! Замените BASE_URL на реальный URL вашего приложения на Railway!")
        print("   Найдите URL в Railway Dashboard -> Ваш проект -> Settings -> Domains")
        return
    
    # Параметры для тестирования (Москва, текущее время)
    test_datetime = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    lat, lon = 55.7558, 37.6176  # Москва
    
    # Базовые параметры
    base_params = f"datetime_str={test_datetime}&lat={lat}&lon={lon}"
    
    tests = [
        # Основные эндпоинты
        (f"{BASE_URL}/planets?{base_params}", "Планеты (основные)"),
        (f"{BASE_URL}/planets?{base_params}&extra=true", "Планеты (с дополнительными точками)"),
        (f"{BASE_URL}/aspects?{base_params}", "Аспекты"),
        (f"{BASE_URL}/houses?{base_params}", "Дома"),
        (f"{BASE_URL}/moon_phase?{base_params}", "Фаза Луны"),
        
        # Тест на производительность (кеширование)
        (f"{BASE_URL}/planets?{base_params}", "Планеты (повторный запрос - тест кеша)"),
    ]
    
    # Выполняем тесты
    successful = 0
    total = len(tests)
    
    for url, description in tests:
        if test_endpoint(url, description):
            successful += 1
    
    # Итоговый отчет
    print("\n" + "=" * 60)
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print(f"✅ Успешных тестов: {successful}/{total}")
    print(f"❌ Неудачных тестов: {total - successful}/{total}")
    
    if successful == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО! API работает корректно!")
    elif successful > 0:
        print("⚠️  Некоторые тесты не прошли. Проверьте логи выше.")
    else:
        print("💥 ВСЕ ТЕСТЫ ПРОВАЛИЛИСЬ! Проверьте:")
        print("   1. Правильность URL приложения")
        print("   2. Статус деплоя на Railway")
        print("   3. Логи приложения на Railway")
    
    # Дополнительные советы
    print("\n💡 ПОЛЕЗНЫЕ СОВЕТЫ:")
    print("   • Логи Railway: Dashboard -> Ваш проект -> Deployments -> View Logs")
    print("   • Проверить статус: Dashboard -> Ваш проект (зеленый = работает)")
    print(f"   • Ваш API ключ активен с лимитом 100,000 запросов/час")
    print("   • При ошибках 401/403 проверьте правильность API ключа")

if __name__ == "__main__":
    main()
