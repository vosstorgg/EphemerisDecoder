#!/usr/bin/env python3
"""
Скрипт для генерации демо-API ключа
"""

import sys
import os

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.auth import generate_demo_key, key_manager


def main():
    """Основная функция генерации демо-ключа"""
    print("🚀 Генерация демо-API ключа для Ephemeris Decoder")
    print("=" * 60)

    try:
        # Генерируем демо-ключ
        demo_key = generate_demo_key()

        print("✅ Демо-ключ успешно сгенерирован!")
        print()
        print("🔑 Ваш API ключ:")
        print(f"   {demo_key}")
        print()
        print("📋 Использование ключа:")
        print("   1. В HTTP заголовке: X-API-Key: ваш_ключ")
        print("   2. В параметре запроса: ?api_key=ваш_ключ")
        print("   3. В Authorization header: Bearer ваш_ключ")
        print()
        print("🌐 Примеры запросов:")
        print(f"   curl -H \"X-API-Key: {demo_key[:20]}...\" \\")
        print("        \"http://localhost:8000/planets?datetime=2024-01-15T12:00:00&lat=55.7558&lon=37.6176\"")
        print()
        print("⚠️  ВАЖНО:")
        print("   • Сохраните этот ключ в безопасном месте")
        print("   • Для продакшена используйте ключ с ограниченными правами")
        print("   • Регулярно меняйте ключи для безопасности")
        print()
        print("📊 Информация о ключе:")
        keys = key_manager.list_keys()
        if keys:
            demo_api_key = keys[-1]  # Последний созданный ключ
            print(f"   ID ключа: {demo_api_key.key_id}")
            print(f"   Название: {demo_api_key.name}")
            print(f"   Разрешения: {', '.join([p.value for p in demo_api_key.permissions])}")
            print(f"   Лимит запросов: {demo_api_key.rate_limit} в час")
            print(f"   Истекает: {'Не истекает' if not demo_api_key.expires_at else demo_api_key.expires_at.strftime('%Y-%m-%d')}")

        print()
        print("🎯 Следующие шаги:")
        print("   1. Запустите сервер: python run_local.py")
        print("   2. Откройте документацию: http://localhost:8000/docs")
        print("   3. Протестируйте API с вашим ключом")

    except Exception as e:
        print(f"❌ Ошибка при генерации ключа: {e}")
        print()
        print("💡 Убедитесь, что:")
        print("   • Все зависимости установлены (pip install -r requirements.txt)")
        print("   • У вас есть права на запись в директорию config/")
        sys.exit(1)


if __name__ == "__main__":
    main()
