#!/usr/bin/env python3
"""
Быстрое тестирование аутентификации Ephemeris Decoder API
"""

import requests
import sys
import os

def test_api_authentication():
    """Тестирует аутентификацию API"""
    print("🧪 Быстрое тестирование аутентификации Ephemeris Decoder API")
    print("=" * 60)

    base_url = "http://localhost:8000"

    # Тест 1: Запрос без ключа
    print("\n1️⃣  Тест: Запрос без API ключа")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"   Статус: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ Ожидаемо: Доступ запрещен без ключа")
        else:
            print("   ⚠️  Неожиданный ответ")
    except requests.exceptions.ConnectionError:
        print("   ❌ Сервер не запущен. Запустите: python run_local.py")
        return False

    # Тест 2: Получение демо-ключа
    print("\n2️⃣  Тест: Генерация демо-ключа")
    try:
        # Импортируем функцию генерации ключа
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from utils.auth import generate_demo_key

        demo_key = generate_demo_key()
        print(f"   ✅ Ключ сгенерирован: {demo_key[:20]}...")
    except Exception as e:
        print(f"   ❌ Ошибка генерации ключа: {e}")
        return False

    # Тест 3: Запрос с правильным ключом
    print("\n3️⃣  Тест: Запрос с правильным API ключом")
    try:
        headers = {"X-API-Key": demo_key}
        response = requests.get(f"{base_url}/health", headers=headers)
        print(f"   Статус: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("   ✅ Успешная аутентификация!"            print(f"   📊 API ключей: {data.get('api_keys_count', 'N/A')}")
        else:
            print(f"   ❌ Ошибка: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Ошибка запроса: {e}")
        return False

    # Тест 4: Запрос с неправильным ключом
    print("\n4️⃣  Тест: Запрос с неправильным API ключом")
    try:
        headers = {"X-API-Key": "invalid_key_123"}
        response = requests.get(f"{base_url}/health", headers=headers)
        print(f"   Статус: {response.status_code}")

        if response.status_code == 401:
            print("   ✅ Ожидаемо: Доступ запрещен с неправильным ключом")
        else:
            print("   ⚠️  Неожиданный ответ")
    except Exception as e:
        print(f"   ❌ Ошибка запроса: {e}")

    # Тест 5: Запрос к защищенному эндпоинту
    print("\n5️⃣  Тест: Запрос к защищенному эндпоинту (планеты)")
    try:
        headers = {"X-API-Key": demo_key}
        params = {
            "datetime": "2024-01-15T12:00:00",
            "lat": 55.7558,
            "lon": 37.6176
        }
        response = requests.get(f"{base_url}/planets", headers=headers, params=params)
        print(f"   Статус: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            planets_count = len(data.get("planets", {}))
            print(f"   ✅ Успешно получены позиции {planets_count} планет!")
        else:
            print(f"   ❌ Ошибка: {response.text}")
    except Exception as e:
        print(f"   ❌ Ошибка запроса: {e}")

    print("\n" + "=" * 60)
    print("🎉 Тестирование завершено!")
    print("\n💡 Полезные команды:")
    print("   • Просмотр документации: http://localhost:8000/docs")
    print("   • Создание нового ключа: python generate_demo_key.py")
    print("   • Запуск тестов: python run_tests.py")
    print("   • Примеры использования: python examples/api_usage.py")

    return True


if __name__ == "__main__":
    success = test_api_authentication()
    if not success:
        sys.exit(1)
