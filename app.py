"""
Оптимизированное FastAPI приложение для Ephemeris Decoder
"""

from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Query, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from contextlib import asynccontextmanager
import uvicorn
import asyncio
from functools import lru_cache

# Импорты сервисов
from services.ephem import (
    get_planets, get_aspects, get_houses, get_moon_phase,
    initialize_ephemeris, cleanup_ephemeris
)
from services.natal_chart import (
    calculate_natal_chart, validate_birth_data, get_timezone_by_coordinates
)
from services.astrology_calculations import (
    TransitCalculator, SynastryCalculator, ReturnCalculator,
    DirectionCalculator, ArabicPartsCalculator, AstrologicalUtilities
)

# Импорты утилит
from utils.auth import APIKeyManager, APIKeyPermission, key_manager
from utils.middleware import (
    AuthenticationMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    require_read_permission,
    require_admin_permission
)

# ============================================================================
# КОНФИГУРАЦИЯ И ИНИЦИАЛИЗАЦИЯ
# ============================================================================

# Конфигурация приложения
APP_CONFIG = {
    "title": "Ephemeris Decoder",
    "description": "Высокопроизводительный микросервис для астрологических расчетов",
    "version": "2.0.0",
    "docs_url": "/docs",
    "redoc_url": "/redoc",
    "rate_limit": 200,  # Увеличено с 100 до 200
    "cache_ttl": 3600,   # 1 час кеширования
}

# Кеш для часто запрашиваемых данных
_response_cache: Dict[str, Any] = {}
_cache_timestamps: Dict[str, datetime] = {}

# ============================================================================
# МОДЕЛИ ДАННЫХ
# ============================================================================

class DateTimeQuery(BaseModel):
    datetime: str

    @field_validator('datetime')
    @classmethod
    def validate_datetime(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('Неверный формат datetime. Используйте ISO 8601 (YYYY-MM-DDTHH:MM:SS)')

class CoordinatesQuery(BaseModel):
    lat: float
    lon: float

    @field_validator('lat')
    @classmethod
    def validate_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Широта должна быть в диапазоне от -90 до 90 градусов')
        return v

    @field_validator('lon')
    @classmethod
    def validate_lon(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Долгота должна быть в диапазоне от -180 до 180 градусов')
        return v

class NatalChartRequest(BaseModel):
    year: int
    month: int
    day: int
    hour: int
    minute: int
    city: str
    nation: str
    lat: float
    lon: float
    timezone: Optional[str] = None

    @field_validator('year')
    @classmethod
    def validate_year(cls, v):
        current_year = datetime.now().year
        if not 1900 <= v <= current_year:
            raise ValueError(f'Год должен быть между 1900 и {current_year}')
        return v

    @field_validator('month')
    @classmethod
    def validate_month(cls, v):
        if not 1 <= v <= 12:
            raise ValueError('Месяц должен быть между 1 и 12')
        return v

    @field_validator('day')
    @classmethod
    def validate_day(cls, v):
        if not 1 <= v <= 31:
            raise ValueError('День должен быть между 1 и 31')
        return v

    @field_validator('hour')
    @classmethod
    def validate_hour(cls, v):
        if not 0 <= v <= 23:
            raise ValueError('Час должен быть между 0 и 23')
        return v

    @field_validator('minute')
    @classmethod
    def validate_minute(cls, v):
        if not 0 <= v <= 59:
            raise ValueError('Минута должна быть между 0 и 59')
        return v

    @field_validator('lat')
    @classmethod
    def validate_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Широта должна быть в диапазоне от -90 до 90 градусов')
        return v

    @field_validator('lon')
    @classmethod
    def validate_lon(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Долгота должна быть в диапазоне от -180 до 180 градусов')
        return v

    @field_validator('city')
    @classmethod
    def validate_city(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('Город не может быть пустым')
        if len(v) > 100:
            raise ValueError('Название города не может быть длиннее 100 символов')
        return v.strip()

    @field_validator('nation')
    @classmethod
    def validate_nation(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('Страна не может быть пустой')
        if len(v) > 100:
            raise ValueError('Название страны не может быть длиннее 100 символов')
        return v.strip()

# ============================================================================
# УТИЛИТЫ И КЕШИРОВАНИЕ
# ============================================================================

def get_cache_key(endpoint: str, **params) -> str:
    """Генерирует ключ кеша для эндпоинта"""
    # Сортируем параметры для стабильности ключа
    sorted_params = sorted(params.items())
    param_str = "&".join([f"{k}={v}" for k, v in sorted_params])
    return f"{endpoint}:{param_str}"

def is_cache_valid(cache_key: str) -> bool:
    """Проверяет валидность кеша"""
    if cache_key not in _cache_timestamps:
        return False
    cache_time = _cache_timestamps[cache_key]
    age = (datetime.now() - cache_time).total_seconds()
    return age < APP_CONFIG["cache_ttl"]

def get_cached_response(cache_key: str) -> Optional[Dict]:
    """Получает кешированный ответ"""
    if is_cache_valid(cache_key):
        return _response_cache.get(cache_key)
    return None

def cache_response(cache_key: str, response: Dict):
    """Кеширует ответ"""
    _response_cache[cache_key] = response
    _cache_timestamps[cache_key] = datetime.now()

@lru_cache(maxsize=1000)
def parse_datetime_safe(datetime_str: str) -> datetime:
    """Безопасный парсинг datetime с кешированием"""
    return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))

# ============================================================================
# ОБРАБОТЧИКИ ОШИБОК
# ============================================================================

async def validation_error_handler(request: Request, exc: ValueError):
    """Обработчик ошибок валидации"""
    return JSONResponse(
        status_code=400,
        content={
            "error": "validation_error",
            "message": str(exc),
            "details": "Проверьте правильность входных данных"
        }
    )

async def general_error_handler(request: Request, exc: Exception):
    """Общий обработчик ошибок"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_error",
            "message": "Внутренняя ошибка сервера",
            "details": "Попробуйте позже или обратитесь к администратору"
        }
    )

# ============================================================================
# LIFESPAN И ИНИЦИАЛИЗАЦИЯ
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    print("🚀 Запуск Ephemeris Decoder v2.0.0")
    initialize_ephemeris()
    print("✅ Swiss Ephemeris инициализирован")
    print("✅ Кеширование активировано")
    print("✅ Аутентификация включена")
    yield
    # Shutdown
    print("🔄 Очистка ресурсов...")
    cleanup_ephemeris()
    print("✅ Ресурсы освобождены")

# ============================================================================
# СОЗДАНИЕ ПРИЛОЖЕНИЯ
# ============================================================================

app = FastAPI(
    title=APP_CONFIG["title"],
    description=APP_CONFIG["description"],
    version=APP_CONFIG["version"],
    docs_url=APP_CONFIG["docs_url"],
    redoc_url=APP_CONFIG["redoc_url"],
    lifespan=lifespan
)

# Добавляем middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests_per_minute=APP_CONFIG["rate_limit"])
app.add_middleware(AuthenticationMiddleware, excluded_paths=["/docs", "/redoc", "/openapi.json", "/health", "/"])

# Регистрируем обработчики ошибок
app.add_exception_handler(ValueError, validation_error_handler)
app.add_exception_handler(Exception, general_error_handler)

# ============================================================================
# ОСНОВНЫЕ ЭНДПОИНТЫ
# ============================================================================

@app.get("/", include_in_schema=True)
async def root():
    """Корневой эндпоинт с информацией о API"""
    return {
        "message": "Ephemeris Decoder API v2.0.0",
        "version": APP_CONFIG["version"],
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "basic": ["/planets", "/aspects", "/houses", "/moon_phase"],
            "natal": ["/natal_chart"],
            "advanced": ["/transits", "/progressions", "/synastry", "/planetary_strength"],
            "returns": ["/solar_return", "/lunar_return"],
            "directions": ["/primary_directions"],
            "parts": ["/arabic_parts"],
            "admin": ["/admin/keys"]
        },
        "features": {
            "caching": "enabled",
            "authentication": "required",
            "rate_limiting": f"{APP_CONFIG['rate_limit']}/min",
            "swiss_ephemeris": "active"
        }
    }

@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Ephemeris Decoder API v2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": APP_CONFIG["title"],
        "version": APP_CONFIG["version"],
        "api_keys_count": len(key_manager.list_keys()),
        "cache_size": len(_response_cache),
        "features": {
            "authentication": "enabled",
            "caching": "enabled",
            "rate_limiting": "enabled"
        }
    }

# ============================================================================
# БАЗОВЫЕ АСТРОЛОГИЧЕСКИЕ ЭНДПОИНТЫ
# ============================================================================

@app.get("/planets")
async def planets(
    datetime_str: str = Query(..., description="Время в формате ISO 8601"),
    lat: float = Query(..., ge=-90, le=90, description="Широта в градусах"),
    lon: float = Query(..., ge=-180, le=180, description="Долгота в градусах"),
    extra: bool = Query(False, description="Включить дополнительные точки"),
    api_key: str = Depends(require_read_permission)
):
    """Получение позиций планет с кешированием"""
    cache_key = get_cache_key("planets", datetime_str=datetime_str, lat=lat, lon=lon, extra=extra)
    
    # Проверяем кеш
    cached = get_cached_response(cache_key)
    if cached:
        return cached
    
    try:
        dt = parse_datetime_safe(datetime_str)
        result = await get_planets(dt, lat, lon, extra)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Кешируем результат
        cache_response(cache_key, result)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Ошибка валидации: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")

@app.get("/aspects")
async def aspects(
    datetime_str: str = Query(..., description="Время в формате ISO 8601"),
    lat: float = Query(..., ge=-90, le=90, description="Широта в градусах"),
    lon: float = Query(..., ge=-180, le=180, description="Долгота в градусах"),
    api_key: str = Depends(require_read_permission)
):
    """Расчёт аспектов между планетами с кешированием"""
    cache_key = get_cache_key("aspects", datetime_str=datetime_str, lat=lat, lon=lon)
    
    cached = get_cached_response(cache_key)
    if cached:
        return cached
    
    try:
        dt = parse_datetime_safe(datetime_str)
        result = await get_aspects(dt, lat, lon)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        cache_response(cache_key, result)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Ошибка валидации: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")

@app.get("/houses")
async def houses(
    datetime_str: str = Query(..., description="Время в формате ISO 8601"),
    lat: float = Query(..., ge=-90, le=90, description="Широта в градусах"),
    lon: float = Query(..., ge=-180, le=180, description="Долгота в градусах"),
    api_key: str = Depends(require_read_permission)
):
    """Определение границ домов с кешированием"""
    cache_key = get_cache_key("houses", datetime_str=datetime_str, lat=lat, lon=lon)
    
    cached = get_cached_response(cache_key)
    if cached:
        return cached
    
    try:
        dt = parse_datetime_safe(datetime_str)
        result = await get_houses(dt, lat, lon)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        cache_response(cache_key, result)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Ошибка валидации: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")

@app.get("/moon_phase")
async def moon_phase(
    datetime_str: str = Query(..., description="Время в формате ISO 8601"),
    api_key: str = Depends(require_read_permission)
):
    """Расчёт фазы Луны с кешированием"""
    cache_key = get_cache_key("moon_phase", datetime_str=datetime_str)
    
    cached = get_cached_response(cache_key)
    if cached:
        return cached
    
    try:
        dt = parse_datetime_safe(datetime_str)
        result = await get_moon_phase(dt)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        cache_response(cache_key, result)
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Ошибка валидации: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")

# ============================================================================
# НАТАЛЬНАЯ КАРТА
# ============================================================================

@app.post("/natal_chart")
async def natal_chart(
    request: NatalChartRequest,
    api_key: str = Depends(require_read_permission)
):
    """Расчёт натальной карты с оптимизированной обработкой"""
    try:
        # Валидируем данные рождения
        is_valid, error_msg = validate_birth_data(
            request.year, request.month, request.day, 
            request.hour, request.minute
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Ошибка валидации данных рождения: {error_msg}")
        
        # Определяем часовой пояс
        timezone = request.timezone or get_timezone_by_coordinates(request.lat, request.lon)
        
        # Рассчитываем натальную карту
        result = await calculate_natal_chart(
            year=request.year,
            month=request.month,
            day=request.day,
            hour=request.hour,
            minute=request.minute,
            city=request.city,
            nation=request.nation,
            lat=request.lat,
            lon=request.lon,
            tz_str=timezone
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Ошибка валидации: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")

# ============================================================================
# ЗАПУСК ПРИЛОЖЕНИЯ
# ============================================================================

if __name__ == "__main__":
    import os
    
    # Получаем порт из переменной окружения или используем 8000 по умолчанию
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Отключаем reload для продакшена
        log_level="info",
        workers=1  # Один воркер для лучшей производительности кеша
    )
