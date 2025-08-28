"""
Модуль аутентификации для Ephemeris Decoder API
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import yaml
from pydantic import BaseModel, Field
from enum import Enum


class APIKeyPermission(Enum):
    """Разрешения для API ключей"""
    READ = "read"           # Только чтение данных
    WRITE = "write"         # Чтение и запись
    ADMIN = "admin"         # Полный доступ + управление ключами


class APIKey(BaseModel):
    """Модель API ключа"""
    key_id: str = Field(..., description="Уникальный идентификатор ключа")
    name: str = Field(..., description="Человеко-читаемое имя ключа")
    key_hash: str = Field(..., description="Хеш ключа для безопасного хранения")
    permissions: List[APIKeyPermission] = Field(default_factory=lambda: [APIKeyPermission.READ],
                                                description="Разрешения ключа")
    created_at: datetime = Field(default_factory=datetime.now, description="Время создания")
    expires_at: Optional[datetime] = Field(None, description="Время истечения")
    is_active: bool = Field(True, description="Активен ли ключ")
    rate_limit: int = Field(100, description="Максимальное количество запросов в час")
    usage_count: int = Field(0, description="Количество использований")

    def is_expired(self) -> bool:
        """Проверяет, истек ли срок действия ключа"""
        if self.expires_at is None:
            return False
        return datetime.now() > self.expires_at

    def has_permission(self, permission: APIKeyPermission) -> bool:
        """Проверяет, имеет ли ключ указанное разрешение"""
        return permission in self.permissions or APIKeyPermission.ADMIN in self.permissions

    def can_make_request(self) -> bool:
        """Проверяет, может ли ключ сделать запрос (активен, не истек, в пределах лимита)"""
        return (
            self.is_active and
            not self.is_expired() and
            self.usage_count < self.rate_limit
        )

    def increment_usage(self):
        """Увеличивает счетчик использования"""
        self.usage_count += 1


class APIKeyManager:
    """Менеджер API ключей"""

    def __init__(self, config_path: str = "config/api_keys.yaml"):
        self.config_path = config_path
        self.keys: Dict[str, APIKey] = {}
        self._load_keys()

    def _load_keys(self):
        """Загружает ключи из конфигурационного файла"""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f) or {}

            for key_data in config.get("api_keys", []):
                key = APIKey(**key_data)
                self.keys[key.key_id] = key

        except FileNotFoundError:
            # Создаем конфигурационный файл если он не существует
            self._create_default_config()
        except Exception as e:
            print(f"Ошибка загрузки API ключей: {e}")
            self._create_default_config()

    def _create_default_config(self):
        """Создает конфигурацию по умолчанию с демо-ключом"""
        demo_key = self.generate_key("demo_key", [APIKeyPermission.READ])
        config = {
            "api_keys": [demo_key.dict()],
            "notes": [
                "Это демо-конфигурация API ключей",
                "Для продакшена замените демо-ключ на реальные",
                "Используйте generate_key() для создания новых ключей"
            ]
        }

        # Сохраняем конфигурацию
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

        print(f"Создан конфигурационный файл: {self.config_path}")
        print(f"Демо-ключ: {demo_key.key_id}")

    def _save_keys(self):
        """Сохраняет ключи в конфигурационный файл"""
        config = {
            "api_keys": [key.dict() for key in self.keys.values()],
            "notes": [
                "Конфигурация API ключей Ephemeris Decoder",
                "Обновлено: " + datetime.now().isoformat()
            ]
        }

        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    def generate_key(self, name: str, permissions: List[APIKeyPermission] = None,
                    expires_days: int = None, rate_limit: int = 100) -> tuple[str, APIKey]:
        """
        Генерирует новый API ключ

        Args:
            name: Имя ключа
            permissions: Список разрешений
            expires_days: Количество дней до истечения (None - бессрочный)
            rate_limit: Лимит запросов в час

        Returns:
            tuple: (сырой ключ, объект APIKey)
        """
        if permissions is None:
            permissions = [APIKeyPermission.READ]

        # Генерируем уникальный ID и ключ
        key_id = secrets.token_hex(8)
        raw_key = secrets.token_hex(32)

        # Создаем хеш ключа для безопасного хранения
        key_hash = self._hash_key(raw_key)

        # Вычисляем дату истечения
        expires_at = None
        if expires_days:
            expires_at = datetime.now() + timedelta(days=expires_days)

        # Создаем объект ключа
        api_key = APIKey(
            key_id=key_id,
            name=name,
            key_hash=key_hash,
            permissions=permissions,
            expires_at=expires_at,
            rate_limit=rate_limit
        )

        # Сохраняем ключ
        self.keys[key_id] = api_key
        self._save_keys()

        return raw_key, api_key

    def _hash_key(self, raw_key: str) -> str:
        """Создает хеш ключа для безопасного хранения"""
        return hashlib.sha256(raw_key.encode()).hexdigest()

    def verify_key(self, raw_key: str) -> Optional[APIKey]:
        """
        Проверяет API ключ

        Args:
            raw_key: Сырой API ключ

        Returns:
            APIKey или None если ключ недействителен
        """
        key_hash = self._hash_key(raw_key)

        # Ищем ключ по хешу
        for key in self.keys.values():
            if key.key_hash == key_hash:
                if key.can_make_request():
                    key.increment_usage()
                    self._save_keys()  # Сохраняем обновленную статистику
                    return key
                break

        return None

    def get_key_by_id(self, key_id: str) -> Optional[APIKey]:
        """Получает ключ по ID"""
        return self.keys.get(key_id)

    def revoke_key(self, key_id: str) -> bool:
        """Отзывает API ключ"""
        if key_id in self.keys:
            self.keys[key_id].is_active = False
            self._save_keys()
            return True
        return False

    def list_keys(self) -> List[APIKey]:
        """Возвращает список всех ключей"""
        return list(self.keys.values())

    def get_stats(self) -> Dict:
        """Возвращает статистику использования ключей"""
        total_keys = len(self.keys)
        active_keys = len([k for k in self.keys.values() if k.is_active])
        expired_keys = len([k for k in self.keys.values() if k.is_expired()])
        total_usage = sum(k.usage_count for k in self.keys.values())

        return {
            "total_keys": total_keys,
            "active_keys": active_keys,
            "expired_keys": expired_keys,
            "total_usage": total_usage,
            "keys": [
                {
                    "key_id": k.key_id,
                    "name": k.name,
                    "permissions": [p.value for p in k.permissions],
                    "is_active": k.is_active,
                    "usage_count": k.usage_count,
                    "rate_limit": k.rate_limit,
                    "expires_at": k.expires_at.isoformat() if k.expires_at else None
                }
                for k in self.keys.values()
            ]
        }


# Глобальный менеджер ключей
key_manager = APIKeyManager()


def authenticate_api_key(raw_key: str) -> Optional[APIKey]:
    """
    Аутентифицирует API ключ

    Args:
        raw_key: Сырой API ключ из заголовка

    Returns:
        APIKey или None если аутентификация не удалась
    """
    return key_manager.verify_key(raw_key)


def require_permission(api_key: APIKey, permission: APIKeyPermission) -> bool:
    """
    Проверяет, имеет ли ключ необходимое разрешение

    Args:
        api_key: Объект API ключа
        permission: Требуемое разрешение

    Returns:
        True если разрешение есть, иначе False
    """
    return api_key.has_permission(permission)


def generate_demo_key() -> str:
    """Генерирует демо-ключ для тестирования"""
    raw_key, api_key = key_manager.generate_key(
        name="demo_key",
        permissions=[APIKeyPermission.READ],
        expires_days=30,
        rate_limit=1000
    )
    return raw_key


if __name__ == "__main__":
    # Пример использования
    print("🚀 Генерация демо-ключа...")

    demo_key = generate_demo_key()
    print(f"📝 Демо-ключ: {demo_key}")
    print(f"🔑 ID ключа: {key_manager.keys[list(key_manager.keys.keys())[0]].key_id}")

    # Проверка ключа
    verified_key = authenticate_api_key(demo_key)
    if verified_key:
        print(f"✅ Ключ верифицирован: {verified_key.name}")
        print(f"🔐 Разрешения: {[p.value for p in verified_key.permissions]}")
    else:
        print("❌ Ошибка верификации ключа")
