#!/usr/bin/env python3
"""
Скрипт для локального запуска Ephemeris Decoder
"""

import os
import sys
import subprocess


def check_dependencies():
    """Проверяет наличие необходимых зависимостей"""
    print("🔍 Проверка зависимостей...")
    
    required_packages = [
        "fastapi",
        "uvicorn",
        "pyswisseph",
        "pyyaml",
        "pydantic"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Отсутствуют пакеты: {', '.join(missing_packages)}")
        print("Установите их командой: pip install -r requirements.txt")
        return False
    
    print("✅ Все зависимости установлены")
    return True


def run_app():
    """Запускает приложение"""
    print("\n🚀 Запуск Ephemeris Decoder...")
    print("=" * 50)
    
    # Проверяем, что мы в корневой директории проекта
    if not os.path.exists("app.py"):
        print("❌ Ошибка: Запустите скрипт из корневой директории проекта")
        sys.exit(1)
    
    # Проверяем зависимости
    if not check_dependencies():
        sys.exit(1)
    
    print("\n🌐 Приложение будет доступно по адресу: http://localhost:8000")
    print("📚 Документация API: http://localhost:8000/docs")
    print("🔍 Альтернативная документация: http://localhost:8000/redoc")
    print("💚 Проверка здоровья: http://localhost:8000/health")
    print("\n⏹️  Для остановки нажмите Ctrl+C")
    print("=" * 50)
    
    try:
        # Запускаем приложение
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n\n🛑 Приложение остановлено")
    except Exception as e:
        print(f"\n❌ Ошибка при запуске: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_app()


