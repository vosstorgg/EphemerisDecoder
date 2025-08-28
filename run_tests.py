#!/usr/bin/env python3
"""
Скрипт для запуска тестов Ephemeris Decoder
"""

import subprocess
import sys
import os


def run_tests():
    """Запускает тесты"""
    print("🚀 Запуск тестов Ephemeris Decoder...")
    print("=" * 50)
    
    # Проверяем, что мы в корневой директории проекта
    if not os.path.exists("app.py"):
        print("❌ Ошибка: Запустите скрипт из корневой директории проекта")
        sys.exit(1)
    
    # Проверяем наличие pytest
    try:
        import pytest
    except ImportError:
        print("❌ Ошибка: pytest не установлен. Установите: pip install pytest")
        sys.exit(1)
    
    # Запускаем тесты
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short",
            "--color=yes"
        ], capture_output=False)
        
        if result.returncode == 0:
            print("\n✅ Все тесты прошли успешно!")
        else:
            print(f"\n❌ Тесты завершились с ошибкой (код: {result.returncode})")
            sys.exit(result.returncode)
            
    except Exception as e:
        print(f"❌ Ошибка при запуске тестов: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_tests()


