#!/usr/bin/env python3
"""
Скрипт для создания API ключей Ephemeris Decoder
Используйте этот скрипт для генерации новых API ключей
"""

import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.auth import APIKeyManager, APIKeyPermission, generate_demo_key


def create_production_key():
    """Создает ключ для продакшена"""
    print("🔑 Создание API ключа для продакшена")
    print("=" * 50)

    # Получаем параметры от пользователя
    name = input("Введите имя ключа (например, 'MyApp'): ").strip()
    if not name:
        name = "Production Key"

    # Выбор разрешений
    print("\nВыберите разрешения:")
    print("1. READ - только чтение данных")
    print("2. WRITE - чтение и запись")
    print("3. ADMIN - полный доступ + управление ключами")

    while True:
        choice = input("Ваш выбор (1-3): ").strip()
        if choice == "1":
            permissions = [APIKeyPermission.READ]
            break
        elif choice == "2":
            permissions = [APIKeyPermission.WRITE]
            break
        elif choice == "3":
            permissions = [APIKeyPermission.ADMIN]
            break
        else:
            print("Пожалуйста, выберите 1, 2 или 3")

    # Срок действия
    expires_input = input("Дни до истечения (Enter для бессрочного): ").strip()
    expires_days = int(expires_input) if expires_input.isdigit() else None

    # Лимит запросов
    rate_limit_input = input("Лимит запросов в час (Enter для 1000): ").strip()
    rate_limit = int(rate_limit_input) if rate_limit_input.isdigit() else 1000

    # Создаем ключ
    try:
        manager = APIKeyManager()
        raw_key, api_key = manager.generate_key(
            name=name,
            permissions=permissions,
            expires_days=expires_days,
            rate_limit=rate_limit
        )

        print("
✅ API ключ успешно создан!"        print("=" * 50)
        print(f"🔑 API ключ: {raw_key}")
        print(f"🆔 ID ключа: {api_key.key_id}")
        print(f"📝 Имя: {api_key.name}")
        print(f"🔐 Разрешения: {', '.join([p.value for p in api_key.permissions])}")
        print(f"⏰ Истекает: {'Не истекает' if not api_key.expires_at else api_key.expires_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"📊 Лимит запросов: {api_key.rate_limit} в час")

        print("
💡 Использование ключа:"        print(f"   curl -H \"X-API-Key: {raw_key[:20]}...\" \\")
        print("        \"https://your-app.com/planets?datetime=2024-01-15T12:00:00&lat=55.7558&lon=37.6176\""

        print("
⚠️  ВАЖНО:"        print("   • Сохраните этот ключ в безопасном месте!")
        print("   • Никогда не коммитьте ключ в репозиторий!")
        print("   • Регулярно меняйте ключи для безопасности!"
        return raw_key

    except Exception as e:
        print(f"❌ Ошибка при создании ключа: {e}")
        return None


def create_demo_key():
    """Создает демо-ключ для тестирования"""
    print("🎯 Создание демо-API ключа для тестирования")
    print("=" * 50)

    try:
        demo_key = generate_demo_key()

        print("✅ Демо-ключ успешно создан!"        print("=" * 50)
        print(f"🔑 API ключ: {demo_key}")

        print("
💡 Использование:"        print(f"   curl -H \"X-API-Key: {demo_key[:20]}...\" \\")
        print("        \"http://localhost:8000/planets?datetime=2024-01-15T12:00:00&lat=55.7558&lon=37.6176\""

        print("
⚠️  Демо-ключ имеет ограничения:"        print("   • Только READ разрешения")
        print("   • 1000 запросов в час")
        print("   • Истекает через 30 дней"
        return demo_key

    except Exception as e:
        print(f"❌ Ошибка при создании демо-ключа: {e}")
        return None


def main():
    """Основная функция"""
    print("🚀 Ephemeris Decoder - Генератор API ключей")
    print("=" * 60)

    print("Выберите тип ключа:")
    print("1. Демо-ключ (для тестирования)")
    print("2. Продакшн-ключ (с настройками)")
    print("3. Выход")

    choice = input("Ваш выбор (1-3): ").strip()

    if choice == "1":
        create_demo_key()
    elif choice == "2":
        create_production_key()
    elif choice == "3":
        print("👋 До свидания!")
        return
    else:
        print("❌ Неверный выбор")


if __name__ == "__main__":
    main()
