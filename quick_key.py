#!/usr/bin/env python3
"""
Быстрое создание API ключа
Использование: python quick_key.py "Имя ключа" [read|write|admin] [дни] [лимит]
"""

import sys
import os

# Добавляем путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.auth import APIKeyManager, APIKeyPermission


def quick_create_key(name="Quick Key", perm="read", expires_days=None, rate_limit=1000):
    """Быстрое создание ключа"""

    # Разрешения
    if perm.lower() == "admin":
        permissions = [APIKeyPermission.ADMIN]
    elif perm.lower() == "write":
        permissions = [APIKeyPermission.WRITE]
    else:
        permissions = [APIKeyPermission.READ]

    # Создаем ключ
    manager = APIKeyManager()
    raw_key, api_key = manager.generate_key(
        name=name,
        permissions=permissions,
        expires_days=expires_days,
        rate_limit=rate_limit
    )

    print(f"✅ Ключ создан: {raw_key}")
    print(f"🆔 ID: {api_key.key_id}")
    print(f"🔐 Права: {perm}")
    return raw_key


if __name__ == "__main__":
    args = sys.argv[1:]

    name = args[0] if len(args) > 0 else "Quick Key"
    perm = args[1] if len(args) > 1 else "read"
    expires_days = int(args[2]) if len(args) > 2 else None
    rate_limit = int(args[3]) if len(args) > 3 else 1000

    quick_create_key(name, perm, expires_days, rate_limit)
