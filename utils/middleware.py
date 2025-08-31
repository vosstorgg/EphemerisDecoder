"""
Middleware для аутентификации Ephemeris Decoder API
"""

from fastapi import Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, List
import time

from utils.auth import authenticate_api_key, APIKey, APIKeyPermission, require_permission, key_manager


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware для аутентификации API ключей"""

    def __init__(self, app, excluded_paths: List[str] = None):
        super().__init__(app)
        self.excluded_paths = excluded_paths or ["/docs", "/redoc", "/openapi.json", "/health"]

    async def dispatch(self, request: Request, call_next):
        """Обрабатывает входящий запрос"""
        start_time = time.time()

        # Пропускаем исключенные пути
        if request.url.path in self.excluded_paths:
            response = await call_next(request)
            return response

        # Извлекаем API ключ из заголовка
        api_key = self._extract_api_key(request)

        if not api_key:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "API key required",
                    "message": "Please provide X-API-Key header with valid API key",
                    "docs": "/docs"
                }
            )

        # Перезагружаем конфигурацию ключей перед аутентификацией
        key_manager._load_keys()
        
        # Аутентифицируем ключ
        authenticated_key = authenticate_api_key(api_key)

        if not authenticated_key:
            return JSONResponse(
                status_code=401,
                content={
                    "error": "Invalid API key",
                    "message": "The provided API key is invalid or expired",
                    "docs": "/docs"
                }
            )

        # Проверяем лимиты использования
        if not authenticated_key.can_make_request():
            if authenticated_key.is_expired():
                error_msg = "API key has expired"
            elif not authenticated_key.is_active:
                error_msg = "API key is deactivated"
            else:
                error_msg = "Rate limit exceeded"

            return JSONResponse(
                status_code=429,
                content={
                    "error": "API key limit reached",
                    "message": error_msg,
                    "docs": "/docs"
                }
            )

        # Добавляем информацию о ключе в request state
        request.state.api_key = authenticated_key
        request.state.key_id = authenticated_key.key_id
        request.state.permissions = authenticated_key.permissions

        # Выполняем запрос
        response = await call_next(request)

        # Добавляем информацию о использовании в заголовки ответа
        response.headers["X-API-Key-ID"] = authenticated_key.key_id
        response.headers["X-API-Key-Usage"] = str(authenticated_key.usage_count)
        response.headers["X-API-Key-Limit"] = str(authenticated_key.rate_limit)

        # Логируем время выполнения
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        return response

    def _extract_api_key(self, request: Request) -> Optional[str]:
        """Извлекает API ключ из запроса"""
        # Проверяем заголовок X-API-Key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key.strip()

        # Проверяем параметр запроса api_key
        api_key = request.query_params.get("api_key")
        if api_key:
            return api_key.strip()

        # Проверяем Authorization header (Bearer token format)
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            return auth_header[7:].strip()

        return None


def get_current_api_key(request: Request) -> APIKey:
    """Dependency для получения текущего API ключа"""
    if not hasattr(request.state, 'api_key'):
        raise HTTPException(
            status_code=401,
            detail="API key not found in request"
        )
    return request.state.api_key


def require_read_permission(api_key: APIKey = Depends(get_current_api_key)) -> APIKey:
    """Dependency для проверки разрешения на чтение"""
    if not require_permission(api_key, APIKeyPermission.READ):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions: READ permission required"
        )
    return api_key


def require_write_permission(api_key: APIKey = Depends(get_current_api_key)) -> APIKey:
    """Dependency для проверки разрешения на запись"""
    if not require_permission(api_key, APIKeyPermission.WRITE):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions: WRITE permission required"
        )
    return api_key


def require_admin_permission(api_key: APIKey = Depends(get_current_api_key)) -> APIKey:
    """Dependency для проверки административных разрешений"""
    if not require_permission(api_key, APIKeyPermission.ADMIN):
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions: ADMIN permission required"
        )
    return api_key


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware для дополнительного контроля rate limiting"""

    def __init__(self, app, max_requests_per_minute: int = 60):
        super().__init__(app)
        self.max_requests_per_minute = max_requests_per_minute
        self.requests = {}

    async def dispatch(self, request: Request, call_next):
        """Обрабатывает запрос с дополнительным rate limiting"""
        # Получаем IP адрес клиента
        client_ip = self._get_client_ip(request)

        # Проверяем rate limit
        current_time = time.time()
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Очищаем старые запросы (старше 1 минуты)
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < 60
        ]

        # Проверяем лимит
        if len(self.requests[client_ip]) >= self.max_requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too many requests",
                    "message": f"Rate limit exceeded: {self.max_requests_per_minute} requests per minute",
                    "retry_after": 60
                }
            )

        # Добавляем текущий запрос
        self.requests[client_ip].append(current_time)

        # Выполняем запрос
        response = await call_next(request)
        return response

    def _get_client_ip(self, request: Request) -> str:
        """Получает IP адрес клиента"""
        # Проверяем заголовки прокси
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        # Проверяем заголовок X-Real-IP
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Используем client IP из request
        return request.client.host if request.client else "unknown"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware для добавления security headers"""

    async def dispatch(self, request: Request, call_next):
        """Добавляет security headers к ответу"""
        response = await call_next(request)

        # Добавляем security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

        # Добавляем информацию о сервере
        response.headers["Server"] = "EphemerisDecoder/1.0"

        return response
