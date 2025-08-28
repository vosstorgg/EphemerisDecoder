#!/usr/bin/env python3
"""
Примеры использования Ephemeris Decoder API с аутентификацией
"""

import requests
import json
from datetime import datetime


class EphemerisAPIClient:
    """Клиент для работы с Ephemeris Decoder API с аутентификацией"""

    def __init__(self, base_url="http://localhost:8000", api_key=None):
        """
        Инициализация клиента

        Args:
            base_url: URL API сервера
            api_key: API ключ для аутентификации
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()

        # Устанавливаем API ключ в заголовки по умолчанию
        if self.api_key:
            self.session.headers.update({"X-API-Key": self.api_key})
    
    def get_planets(self, dt, lat, lon, extra=False):
        """Получает позиции планет"""
        params = {
            "datetime": dt,
            "lat": lat,
            "lon": lon,
            "extra": extra
        }

        response = self.session.get(f"{self.base_url}/planets", params=params)
        response.raise_for_status()
        return response.json()

    def get_aspects(self, dt, lat, lon):
        """Получает аспекты между планетами"""
        params = {
            "datetime": dt,
            "lat": lat,
            "lon": lon
        }

        response = self.session.get(f"{self.base_url}/aspects", params=params)
        response.raise_for_status()
        return response.json()

    def get_houses(self, dt, lat, lon):
        """Получает границы домов"""
        params = {
            "datetime": dt,
            "lat": lat,
            "lon": lon
        }

        response = self.session.get(f"{self.base_url}/houses", params=params)
        response.raise_for_status()
        return response.json()

    def get_moon_phase(self, dt):
        """Получает фазу Луны"""
        params = {"datetime": dt}

        response = self.session.get(f"{self.base_url}/moon_phase", params=params)
        response.raise_for_status()
        return response.json()

    def health_check(self):
        """Проверяет здоровье сервиса"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    # Административные методы (требуют ADMIN прав)
    def create_api_key(self, name, permissions="read", expires_days=None, rate_limit=100):
        """Создает новый API ключ (требует ADMIN прав)"""
        params = {
            "name": name,
            "permissions": permissions,
            "rate_limit": rate_limit
        }
        if expires_days:
            params["expires_days"] = expires_days

        response = self.session.post(f"{self.base_url}/admin/keys", params=params)
        response.raise_for_status()
        return response.json()

    def list_api_keys(self):
        """Получает список всех API ключей (требует ADMIN прав)"""
        response = self.session.get(f"{self.base_url}/admin/keys")
        response.raise_for_status()
        return response.json()

    def revoke_api_key(self, key_id):
        """Отзывает API ключ (требует ADMIN прав)"""
        response = self.session.delete(f"{self.base_url}/admin/keys/{key_id}")
        response.raise_for_status()
        return response.json()

    def set_api_key(self, api_key):
        """Устанавливает новый API ключ для сессии"""
        self.api_key = api_key
        self.session.headers.update({"X-API-Key": self.api_key})


def print_json(data, title):
    """Красиво выводит JSON данные"""
    print(f"\n{'='*50}")
    print(f" {title}")
    print(f"{'='*50}")
    print(json.dumps(data, indent=2, ensure_ascii=False))


def main():
    """Основная функция с примерами аутентификации и использования API"""
    print("🌟 Примеры использования Ephemeris Decoder API с аутентификацией")

    # Шаг 1: Получение демо-ключа
    print("\n🔑 Шаг 1: Генерация демо-API ключа...")
    try:
        # Импортируем функцию генерации демо-ключа
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        from utils.auth import generate_demo_key

        demo_key = generate_demo_key()
        print(f"✅ Демо-ключ сгенерирован: {demo_key[:20]}...")

        # Создаём клиент с API ключом
        client = EphemerisAPIClient(api_key=demo_key)

    except ImportError:
        print("⚠️  Демо-ключ не найден. Используйте существующий ключ или создайте новый.")
        print("Для генерации демо-ключа запустите: python utils/auth.py")

        # Просим пользователя ввести API ключ
        demo_key = input("Введите ваш API ключ: ").strip()
        if not demo_key:
            print("❌ API ключ не указан. Выход.")
            return

        client = EphemerisAPIClient(api_key=demo_key)

    # Тестовые данные
    test_datetime = "2024-01-15T12:00:00"
    test_lat = 55.7558  # Москва
    test_lon = 37.6176

    try:
        # Проверяем здоровье сервиса
        print("\n🔍 Проверка здоровья сервиса...")
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

        # Пример административных функций (если есть ADMIN права)
        print("\n👑 Пример административных функций...")
        try:
            keys_stats = client.list_api_keys()
            print_json(keys_stats, "Статистика API ключей")

            print("\n✅ Все функции API успешно протестированы!")

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print("ℹ️  У текущего ключа нет административных прав.")
                print("Для тестирования админ-функций используйте ключ с ADMIN правами.")
            else:
                print(f"❌ Ошибка при доступе к админ-функциям: {e}")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            print("❌ Ошибка аутентификации: Неверный API ключ")
            print("Убедитесь, что используете правильный API ключ.")
        elif e.response.status_code == 429:
            print("❌ Превышен лимит запросов")
            print("Попробуйте позже или используйте другой API ключ.")
        else:
            print(f"❌ HTTP ошибка: {e.response.status_code} - {e.response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Ошибка подключения к API.")
        print("Убедитесь, что сервер запущен на http://localhost:8000")
        print("Запустите сервер командой: python run_local.py")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()


def demo_admin_functions():
    """Демонстрация административных функций"""
    print("👑 Демонстрация административных функций")
    print("=" * 50)

    # Запрашиваем админ-ключ
    admin_key = input("Введите API ключ с ADMIN правами: ").strip()
    if not admin_key:
        print("❌ Админ-ключ не указан.")
        return

    client = EphemerisAPIClient(api_key=admin_key)

    try:
        # Получаем статистику ключей
        print("\n📊 Получение статистики API ключей...")
        stats = client.list_api_keys()
        print_json(stats, "Статистика ключей")

        # Создаем новый ключ
        print("\n🔑 Создание нового API ключа...")
        new_key_response = client.create_api_key(
            name="Test App",
            permissions="read,write",
            expires_days=7,
            rate_limit=500
        )
        print_json(new_key_response, "Новый API ключ")

        # Сохраняем новый ключ для тестирования
        if "api_key" in new_key_response:
            new_key = new_key_response["api_key"]
            print(f"\n💡 Новый ключ: {new_key}")
            print("Используйте его для тестирования API!")

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 403:
            print("❌ Недостаточно прав для выполнения административных функций")
        else:
            print(f"❌ Ошибка: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--admin":
        demo_admin_functions()
    else:
        main()
        print("\n" + "="*50)
        print("💡 Для тестирования административных функций запустите:")
        print("   python examples/api_usage.py --admin")


