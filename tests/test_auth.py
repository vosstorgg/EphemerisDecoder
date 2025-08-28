"""
Тесты для системы аутентификации
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import os
import tempfile
import yaml

from utils.auth import (
    APIKey,
    APIKeyManager,
    APIKeyPermission,
    authenticate_api_key,
    require_permission,
    generate_demo_key
)


class TestAPIKey:
    """Тесты для модели API ключа"""

    def test_api_key_creation(self):
        """Тест создания API ключа"""
        api_key = APIKey(
            key_id="test_key_001",
            name="Test Key",
            key_hash="testhash123",
            permissions=[APIKeyPermission.READ],
            rate_limit=100
        )

        assert api_key.key_id == "test_key_001"
        assert api_key.name == "Test Key"
        assert api_key.permissions == [APIKeyPermission.READ]
        assert api_key.rate_limit == 100
        assert api_key.usage_count == 0
        assert api_key.is_active == True
        assert api_key.expires_at is None

    def test_api_key_is_expired_no_expiry(self):
        """Тест проверки истечения срока (без срока)"""
        api_key = APIKey(
            key_id="test_key",
            name="Test",
            key_hash="hash",
            permissions=[APIKeyPermission.READ]
        )

        assert api_key.is_expired() == False

    def test_api_key_is_expired_with_expiry(self):
        """Тест проверки истечения срока"""
        # Ключ истек
        expired_time = datetime.now() - timedelta(days=1)
        expired_key = APIKey(
            key_id="expired_key",
            name="Expired",
            key_hash="hash",
            permissions=[APIKeyPermission.READ],
            expires_at=expired_time
        )

        # Ключ действующий
        future_time = datetime.now() + timedelta(days=1)
        active_key = APIKey(
            key_id="active_key",
            name="Active",
            key_hash="hash",
            permissions=[APIKeyPermission.READ],
            expires_at=future_time
        )

        assert expired_key.is_expired() == True
        assert active_key.is_expired() == False

    def test_api_key_has_permission(self):
        """Тест проверки разрешений"""
        read_key = APIKey(
            key_id="read_key",
            name="Read Only",
            key_hash="hash",
            permissions=[APIKeyPermission.READ]
        )

        admin_key = APIKey(
            key_id="admin_key",
            name="Admin",
            key_hash="hash",
            permissions=[APIKeyPermission.ADMIN]
        )

        # READ ключ имеет READ разрешение
        assert read_key.has_permission(APIKeyPermission.READ) == True

        # READ ключ НЕ имеет WRITE разрешение
        assert read_key.has_permission(APIKeyPermission.WRITE) == False

        # ADMIN ключ имеет все разрешения
        assert admin_key.has_permission(APIKeyPermission.READ) == True
        assert admin_key.has_permission(APIKeyPermission.WRITE) == True
        assert admin_key.has_permission(APIKeyPermission.ADMIN) == True

    def test_api_key_can_make_request(self):
        """Тест проверки возможности сделать запрос"""
        # Активный ключ без лимита
        active_key = APIKey(
            key_id="active",
            name="Active",
            key_hash="hash",
            permissions=[APIKeyPermission.READ],
            is_active=True,
            rate_limit=10,
            usage_count=5
        )

        # Неактивный ключ
        inactive_key = APIKey(
            key_id="inactive",
            name="Inactive",
            key_hash="hash",
            permissions=[APIKeyPermission.READ],
            is_active=False
        )

        # Ключ с превышенным лимитом
        limit_exceeded_key = APIKey(
            key_id="limit",
            name="Limit",
            key_hash="hash",
            permissions=[APIKeyPermission.READ],
            is_active=True,
            rate_limit=10,
            usage_count=10
        )

        assert active_key.can_make_request() == True
        assert inactive_key.can_make_request() == False
        assert limit_exceeded_key.can_make_request() == False

    def test_api_key_increment_usage(self):
        """Тест увеличения счетчика использования"""
        api_key = APIKey(
            key_id="test",
            name="Test",
            key_hash="hash",
            permissions=[APIKeyPermission.READ],
            usage_count=5
        )

        api_key.increment_usage()
        assert api_key.usage_count == 6

        api_key.increment_usage()
        assert api_key.usage_count == 7


class TestAPIKeyManager:
    """Тесты для менеджера API ключей"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        # Создаем временный файл для тестирования
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml')
        self.temp_file.close()

        # Создаем тестовый менеджер
        self.manager = APIKeyManager(config_path=self.temp_file.name)

    def teardown_method(self):
        """Очистка после каждого теста"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    def test_generate_key(self):
        """Тест генерации нового ключа"""
        raw_key, api_key = self.manager.generate_key(
            name="Test Key",
            permissions=[APIKeyPermission.READ, APIKeyPermission.WRITE],
            expires_days=7,
            rate_limit=200
        )

        # Проверяем сырой ключ
        assert len(raw_key) == 64  # 32 байта в hex = 64 символа
        assert all(c in '0123456789abcdef' for c in raw_key)

        # Проверяем объект ключа
        assert api_key.name == "Test Key"
        assert APIKeyPermission.READ in api_key.permissions
        assert APIKeyPermission.WRITE in api_key.permissions
        assert api_key.rate_limit == 200
        assert api_key.expires_at is not None
        assert api_key.is_active == True

        # Проверяем, что ключ сохранен в менеджере
        assert api_key.key_id in self.manager.keys

    def test_verify_key_success(self):
        """Тест успешной верификации ключа"""
        # Создаем ключ
        raw_key, api_key = self.manager.generate_key("Test Key")

        # Верифицируем
        verified_key = self.manager.verify_key(raw_key)

        assert verified_key is not None
        assert verified_key.key_id == api_key.key_id
        assert verified_key.usage_count == 1  # Увеличен на 1

    def test_verify_key_failure(self):
        """Тест неудачной верификации ключа"""
        # Пытаемся верифицировать несуществующий ключ
        verified_key = self.manager.verify_key("nonexistentkey")
        assert verified_key is None

    def test_revoke_key(self):
        """Тест отзыва ключа"""
        # Создаем ключ
        raw_key, api_key = self.manager.generate_key("Test Key")

        # Проверяем, что ключ активен
        assert api_key.is_active == True

        # Отзываем ключ
        success = self.manager.revoke_key(api_key.key_id)
        assert success == True

        # Проверяем, что ключ неактивен
        updated_key = self.manager.get_key_by_id(api_key.key_id)
        assert updated_key.is_active == False

    def test_revoke_nonexistent_key(self):
        """Тест отзыва несуществующего ключа"""
        success = self.manager.revoke_key("nonexistent")
        assert success == False

    def test_get_stats(self):
        """Тест получения статистики"""
        # Создаем несколько ключей
        self.manager.generate_key("Key 1", permissions=[APIKeyPermission.READ])
        self.manager.generate_key("Key 2", permissions=[APIKeyPermission.WRITE])
        self.manager.generate_key("Key 3", permissions=[APIKeyPermission.ADMIN])

        stats = self.manager.get_stats()

        assert stats["total_keys"] == 3
        assert stats["active_keys"] == 3
        assert stats["expired_keys"] == 0
        assert len(stats["keys"]) == 3

        # Проверяем детали ключей
        key_details = stats["keys"][0]
        assert "key_id" in key_details
        assert "name" in key_details
        assert "permissions" in key_details
        assert "usage_count" in key_details

    def test_list_keys(self):
        """Тест получения списка ключей"""
        # Создаем ключи
        self.manager.generate_key("Key 1")
        self.manager.generate_key("Key 2")

        keys = self.manager.list_keys()
        assert len(keys) == 2
        assert all(isinstance(key, APIKey) for key in keys)

    def test_config_file_operations(self):
        """Тест операций с конфигурационным файлом"""
        # Создаем ключ
        raw_key, api_key = self.manager.generate_key("Test Key")

        # Создаем новый менеджер с тем же файлом
        new_manager = APIKeyManager(config_path=self.temp_file.name)

        # Проверяем, что ключ загружен
        loaded_key = new_manager.get_key_by_id(api_key.key_id)
        assert loaded_key is not None
        assert loaded_key.name == "Test Key"


class TestAuthenticationFunctions:
    """Тесты для функций аутентификации"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        # Создаем временный файл
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml')
        self.temp_file.close()

        # Создаем тестовый менеджер
        self.test_manager = APIKeyManager(config_path=self.temp_file.name)
        self.raw_key, self.api_key = self.test_manager.generate_key("Test Key")

    def teardown_method(self):
        """Очистка после каждого теста"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

    @patch('utils.auth.key_manager', None)
    def test_authenticate_api_key_success(self):
        """Тест успешной аутентификации"""
        # Мокаем глобальный менеджер
        with patch('utils.auth.key_manager', self.test_manager):
            authenticated_key = authenticate_api_key(self.raw_key)

            assert authenticated_key is not None
            assert authenticated_key.key_id == self.api_key.key_id

    @patch('utils.auth.key_manager', None)
    def test_authenticate_api_key_failure(self):
        """Тест неудачной аутентификации"""
        # Мокаем глобальный менеджер
        with patch('utils.auth.key_manager', self.test_manager):
            authenticated_key = authenticate_api_key("invalid_key")

            assert authenticated_key is None

    def test_require_permission_success(self):
        """Тест успешной проверки разрешения"""
        # Ключ с READ разрешением
        read_key = APIKey(
            key_id="read",
            name="Read",
            key_hash="hash",
            permissions=[APIKeyPermission.READ]
        )

        # Ключ с ADMIN разрешением
        admin_key = APIKey(
            key_id="admin",
            name="Admin",
            key_hash="hash",
            permissions=[APIKeyPermission.ADMIN]
        )

        # READ ключ имеет READ разрешение
        assert require_permission(read_key, APIKeyPermission.READ) == True

        # ADMIN ключ имеет все разрешения
        assert require_permission(admin_key, APIKeyPermission.READ) == True
        assert require_permission(admin_key, APIKeyPermission.WRITE) == True
        assert require_permission(admin_key, APIKeyPermission.ADMIN) == True

    def test_require_permission_failure(self):
        """Тест неудачной проверки разрешения"""
        # Ключ только с READ разрешением
        read_key = APIKey(
            key_id="read",
            name="Read",
            key_hash="hash",
            permissions=[APIKeyPermission.READ]
        )

        # READ ключ НЕ имеет WRITE разрешение
        assert require_permission(read_key, APIKeyPermission.WRITE) == False
        assert require_permission(read_key, APIKeyPermission.ADMIN) == False

    def test_generate_demo_key(self):
        """Тест генерации демо-ключа"""
        # Мокаем менеджер для тестирования
        with patch('utils.auth.key_manager', self.test_manager):
            demo_key = generate_demo_key()

            assert len(demo_key) == 64
            assert all(c in '0123456789abcdef' for c in demo_key)


class TestAPIKeyHashing:
    """Тесты для хеширования ключей"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.manager = APIKeyManager()

    def test_hash_consistency(self):
        """Тест консистентности хеширования"""
        test_key = "test_key_123"

        # Один и тот же ключ должен давать один и тот же хеш
        hash1 = self.manager._hash_key(test_key)
        hash2 = self.manager._hash_key(test_key)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex = 64 символа

    def test_hash_uniqueness(self):
        """Тест уникальности хешей"""
        key1 = "key1"
        key2 = "key2"

        hash1 = self.manager._hash_key(key1)
        hash2 = self.manager._hash_key(key2)

        assert hash1 != hash2

    def test_hash_format(self):
        """Тест формата хеша"""
        test_key = "test_key"
        hash_result = self.manager._hash_key(test_key)

        # Проверяем, что это валидный hex
        assert all(c in '0123456789abcdef' for c in hash_result)
        assert len(hash_result) == 64
