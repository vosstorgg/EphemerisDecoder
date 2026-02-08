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

class SynastryPerson(BaseModel):
    year: int
    month: int
    day: int
    hour: int = 0
    minute: int = 0
    city: str = ""
    nation: str = ""
    lat: float
    lon: float
    timezone: Optional[str] = None


class SynastryRequest(BaseModel):
    person1: SynastryPerson
    person2: SynastryPerson


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
# ТРАНЗИТЫ
# ============================================================================

@app.get("/transits")
async def transits(
    natal_year: int = Query(..., ge=1900, le=2100, description="Год рождения"),
    natal_month: int = Query(..., ge=1, le=12, description="Месяц рождения"),
    natal_day: int = Query(..., ge=1, le=31, description="День рождения"),
    natal_hour: int = Query(0, ge=0, le=23, description="Час рождения"),
    natal_minute: int = Query(0, ge=0, le=59, description="Минута рождения"),
    natal_city: str = Query("", description="Город рождения"),
    natal_nation: str = Query("", description="Страна рождения"),
    natal_lat: float = Query(..., ge=-90, le=90, description="Широта места рождения"),
    natal_lon: float = Query(..., ge=-180, le=180, description="Долгота места рождения"),
    transit_date: str = Query(..., description="Дата транзита (ISO 8601)"),
    natal_timezone: Optional[str] = Query(None, description="Часовой пояс рождения"),
    transit_timezone: Optional[str] = Query(None, description="Часовой пояс транзита"),
    api_key: str = Depends(require_read_permission)
):
    """Рассчитывает транзиты планет к натальной карте."""
    try:
        is_valid, error_msg = validate_birth_data(
            natal_year, natal_month, natal_day, natal_hour, natal_minute
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        transit_dt = parse_datetime_safe(transit_date)
        tz_str = natal_timezone or get_timezone_by_coordinates(natal_lat, natal_lon)

        natal_result = await calculate_natal_chart(
            year=natal_year,
            month=natal_month,
            day=natal_day,
            hour=natal_hour,
            minute=natal_minute,
            city=natal_city or "Unknown",
            nation=natal_nation or "Unknown",
            lat=natal_lat,
            lon=natal_lon,
            tz_str=tz_str
        )
        if "error" in natal_result:
            raise HTTPException(status_code=500, detail=natal_result["error"])

        transit_planets_result = await get_planets(
            transit_dt, natal_lat, natal_lon, extra=False
        )
        if "error" in transit_planets_result:
            raise HTTPException(status_code=500, detail=transit_planets_result["error"])

        natal_planets = natal_result["planets"]
        transit_planets = transit_planets_result["planets"]
        transits_list = TransitCalculator.calculate_transits(
            natal_planets, transit_planets, transit_dt
        )

        major = [t for t in transits_list if t["is_major"]]
        minor = [t for t in transits_list if not t["is_major"]]
        return {
            "natal_chart": {
                "subject_info": natal_result.get("subject_info"),
                "planets": natal_planets,
            },
            "transit_date": transit_date,
            "transit_planets": transit_planets,
            "transits": transits_list,
            "summary": {
                "total_transits": len(transits_list),
                "major_aspects": len(major),
                "minor_aspects": len(minor),
            }
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Ошибка формата даты: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ПРОГРЕССИИ
# ============================================================================

@app.get("/progressions")
async def progressions(
    birth_year: int = Query(..., ge=1900, le=2100),
    birth_month: int = Query(..., ge=1, le=12),
    birth_day: int = Query(..., ge=1, le=31),
    birth_hour: int = Query(0, ge=0, le=23),
    birth_minute: int = Query(0, ge=0, le=59),
    birth_city: str = Query(""),
    birth_nation: str = Query(""),
    birth_lat: float = Query(..., ge=-90, le=90),
    birth_lon: float = Query(..., ge=-180, le=180),
    progression_date: str = Query(..., description="Дата прогрессии (ISO 8601)"),
    birth_timezone: Optional[str] = Query(None),
    api_key: str = Depends(require_read_permission)
):
    """Вторичные прогрессии (1 день = 1 год)."""
    try:
        is_valid, error_msg = validate_birth_data(
            birth_year, birth_month, birth_day, birth_hour, birth_minute
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        prog_dt = parse_datetime_safe(progression_date)
        birth_dt = datetime(birth_year, birth_month, birth_day, birth_hour, birth_minute)
        tz_str = birth_timezone or get_timezone_by_coordinates(birth_lat, birth_lon)
        natal_result = await calculate_natal_chart(
            year=birth_year, month=birth_month, day=birth_day,
            hour=birth_hour, minute=birth_minute,
            city=birth_city or "Unknown", nation=birth_nation or "Unknown",
            lat=birth_lat, lon=birth_lon, tz_str=tz_str
        )
        if "error" in natal_result:
            raise HTTPException(status_code=500, detail=natal_result["error"])
        natal_planets = natal_result["planets"]
        progressions_list = TransitCalculator.calculate_progressions(
            natal_planets, prog_dt, birth_dt
        )
        return {
            "natal_chart": {"subject_info": natal_result.get("subject_info"), "planets": natal_planets},
            "progressions": progressions_list,
            "summary": {"total_planets": len(progressions_list), "days_since_birth": (prog_dt - birth_dt).days}
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# СИНАСТРИЯ
# ============================================================================

@app.post("/synastry")
async def synastry(request: SynastryRequest, api_key: str = Depends(require_read_permission)):
    """Совместимость двух натальных карт."""
    try:
        p1, p2 = request.person1, request.person2
        tz1 = p1.timezone or get_timezone_by_coordinates(p1.lat, p1.lon)
        tz2 = p2.timezone or get_timezone_by_coordinates(p2.lat, p2.lon)
        natal1 = await calculate_natal_chart(
            p1.year, p1.month, p1.day, p1.hour, p1.minute,
            p1.city or "Unknown", p1.nation or "Unknown", p1.lat, p1.lon, tz1
        )
        natal2 = await calculate_natal_chart(
            p2.year, p2.month, p2.day, p2.hour, p2.minute,
            p2.city or "Unknown", p2.nation or "Unknown", p2.lat, p2.lon, tz2
        )
        if "error" in natal1:
            raise HTTPException(status_code=500, detail=natal1["error"])
        if "error" in natal2:
            raise HTTPException(status_code=500, detail=natal2["error"])
        syn = SynastryCalculator.calculate_synastry(natal1["planets"], natal2["planets"])
        major = [a for a in syn["aspects"] if a["is_major"]]
        return {
            "person1": natal1.get("subject_info"),
            "person2": natal2.get("subject_info"),
            "synastry": syn,
            "summary": {
                "total_aspects": len(syn["aspects"]),
                "major_aspects": len(major),
                "compatibility_score": syn["compatibility_score"],
                "composite_points": len(syn["composite_points"]),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# СИЛА ПЛАНЕТ
# ============================================================================

@app.get("/planetary_strength")
async def planetary_strength(
    year: int = Query(..., ge=1900, le=2100),
    month: int = Query(..., ge=1, le=12),
    day: int = Query(..., ge=1, le=31),
    hour: int = Query(0, ge=0, le=23),
    minute: int = Query(0, ge=0, le=59),
    city: str = Query(""),
    nation: str = Query(""),
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    timezone: Optional[str] = Query(None),
    api_key: str = Depends(require_read_permission)
):
    """Сила и достоинства планет в натальной карте."""
    try:
        is_valid, error_msg = validate_birth_data(year, month, day, hour, minute)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        tz_str = timezone or get_timezone_by_coordinates(lat, lon)
        natal_result = await calculate_natal_chart(
            year, month, day, hour, minute,
            city or "Unknown", nation or "Unknown", lat, lon, tz_str
        )
        if "error" in natal_result:
            raise HTTPException(status_code=500, detail=natal_result["error"])
        planets_data = natal_result["planets"]
        aspects_data = natal_result.get("aspects", [])
        strength_map = {}
        for pname, pinfo in planets_data.items():
            planet_aspects = [
                a for a in aspects_data
                if (a.get("planet1") == pname or a.get("planet2") == pname)
            ]
            strength_map[pname] = {
                "planet_info": pinfo,
                "strength": AstrologicalUtilities.calculate_planetary_strength(
                    pname, pinfo.get("sign", ""), pinfo.get("house", 0), planet_aspects
                )
            }
        scores = [(k, v["strength"]["score"]) for k, v in strength_map.items()]
        strongest = max(scores, key=lambda x: x[1])[0] if scores else None
        weakest = min(scores, key=lambda x: x[1])[0] if scores else None
        return {
            "natal_chart": {"subject_info": natal_result.get("subject_info"), "planets": planets_data},
            "planets_strength": strength_map,
            "summary": {"total_planets": len(strength_map), "strongest_planet": strongest, "weakest_planet": weakest}
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ВОЗВРАЩЕНИЯ
# ============================================================================

@app.get("/solar_return")
async def solar_return(
    birth_year: int = Query(..., ge=1900, le=2100),
    birth_month: int = Query(..., ge=1, le=12),
    birth_day: int = Query(..., ge=1, le=31),
    birth_hour: int = Query(0, ge=0, le=23),
    birth_minute: int = Query(0, ge=0, le=59),
    birth_lat: float = Query(..., ge=-90, le=90),
    birth_lon: float = Query(..., ge=-180, le=180),
    return_year: int = Query(..., ge=1900, le=2100),
    api_key: str = Depends(require_read_permission)
):
    """Солнечное возвращение."""
    try:
        birth_dt = datetime(birth_year, birth_month, birth_day, birth_hour, birth_minute)
        result = ReturnCalculator.calculate_solar_return(birth_dt, return_year, birth_lat, birth_lon)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/lunar_return")
async def lunar_return(
    birth_year: int = Query(..., ge=1900, le=2100),
    birth_month: int = Query(..., ge=1, le=12),
    birth_day: int = Query(..., ge=1, le=31),
    birth_hour: int = Query(0, ge=0, le=23),
    birth_minute: int = Query(0, ge=0, le=59),
    birth_lat: float = Query(..., ge=-90, le=90),
    birth_lon: float = Query(..., ge=-180, le=180),
    return_date: str = Query(..., description="Дата лунного возвращения (ISO 8601)"),
    api_key: str = Depends(require_read_permission)
):
    """Лунное возвращение."""
    try:
        birth_dt = datetime(birth_year, birth_month, birth_day, birth_hour, birth_minute)
        return_dt = parse_datetime_safe(return_date)
        result = ReturnCalculator.calculate_lunar_return(birth_dt, return_dt, birth_lat, birth_lon)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ДИРЕКЦИИ И АРАБСКИЕ ЧАСТИ
# ============================================================================

@app.get("/primary_directions")
async def primary_directions(
    birth_year: int = Query(..., ge=1900, le=2100),
    birth_month: int = Query(..., ge=1, le=12),
    birth_day: int = Query(..., ge=1, le=31),
    birth_hour: int = Query(0, ge=0, le=23),
    birth_minute: int = Query(0, ge=0, le=59),
    birth_city: str = Query(""),
    birth_nation: str = Query(""),
    birth_lat: float = Query(..., ge=-90, le=90),
    birth_lon: float = Query(..., ge=-180, le=180),
    direction_date: str = Query(..., description="Дата дирекции (ISO 8601)"),
    birth_timezone: Optional[str] = Query(None),
    api_key: str = Depends(require_read_permission)
):
    """Первичные дирекции (1° = 1 год)."""
    try:
        is_valid, error_msg = validate_birth_data(birth_year, birth_month, birth_day, birth_hour, birth_minute)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        dir_dt = parse_datetime_safe(direction_date)
        birth_dt = datetime(birth_year, birth_month, birth_day, birth_hour, birth_minute)
        tz_str = birth_timezone or get_timezone_by_coordinates(birth_lat, birth_lon)
        natal_result = await calculate_natal_chart(
            birth_year, birth_month, birth_day, birth_hour, birth_minute,
            birth_city or "Unknown", birth_nation or "Unknown", birth_lat, birth_lon, tz_str
        )
        if "error" in natal_result:
            raise HTTPException(status_code=500, detail=natal_result["error"])
        directions_list = DirectionCalculator.calculate_primary_directions(
            natal_result["planets"], dir_dt, birth_dt
        )
        return {
            "natal_chart": {"subject_info": natal_result.get("subject_info"), "planets": natal_result["planets"]},
            "direction_date": direction_date,
            "directions": directions_list,
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/arabic_parts")
async def arabic_parts(
    birth_year: int = Query(..., ge=1900, le=2100),
    birth_month: int = Query(..., ge=1, le=12),
    birth_day: int = Query(..., ge=1, le=31),
    birth_hour: int = Query(0, ge=0, le=23),
    birth_minute: int = Query(0, ge=0, le=59),
    birth_city: str = Query(""),
    birth_nation: str = Query(""),
    birth_lat: float = Query(..., ge=-90, le=90),
    birth_lon: float = Query(..., ge=-180, le=180),
    birth_timezone: Optional[str] = Query(None),
    api_key: str = Depends(require_read_permission)
):
    """Арабские части (Часть Фортуны, Духа, Брака и др.)."""
    try:
        is_valid, error_msg = validate_birth_data(birth_year, birth_month, birth_day, birth_hour, birth_minute)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        tz_str = birth_timezone or get_timezone_by_coordinates(birth_lat, birth_lon)
        natal_result = await calculate_natal_chart(
            birth_year, birth_month, birth_day, birth_hour, birth_minute,
            birth_city or "Unknown", birth_nation or "Unknown", birth_lat, birth_lon, tz_str
        )
        if "error" in natal_result:
            raise HTTPException(status_code=500, detail=natal_result["error"])
        houses = natal_result.get("houses", [])
        ascendant = houses[0]["longitude"] if houses else 0.0
        parts = ArabicPartsCalculator.calculate_arabic_parts(natal_result["planets"], ascendant)
        return {
            "natal_chart": {"subject_info": natal_result.get("subject_info"), "planets": natal_result["planets"]},
            "arabic_parts": parts,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# АДМИНИСТРИРОВАНИЕ КЛЮЧЕЙ
# ============================================================================

@app.get("/admin/keys")
async def admin_list_keys(api_key: str = Depends(require_admin_permission)):
    """Список ключей и статистика (требует ADMIN)."""
    return key_manager.get_stats()


@app.post("/admin/keys")
async def admin_create_key(
    name: str = Query(..., description="Имя ключа"),
    permissions: str = Query("read", description="read, write или admin (через запятую)"),
    expires_days: Optional[int] = Query(None),
    rate_limit: int = Query(100, ge=0),
    api_key: str = Depends(require_admin_permission)
):
    """Создать API ключ (требует ADMIN)."""
    perm_list = []
    for p in permissions.replace(" ", "").split(","):
        if p == "read":
            perm_list.append(APIKeyPermission.READ)
        elif p == "write":
            perm_list.append(APIKeyPermission.WRITE)
        elif p == "admin":
            perm_list.append(APIKeyPermission.ADMIN)
    raw_key, new_key = key_manager.generate_key(
        name=name, permissions=perm_list or [APIKeyPermission.READ],
        expires_days=expires_days, rate_limit=rate_limit
    )
    return {"key_id": new_key.key_id, "name": new_key.name, "api_key": raw_key, "message": "Сохраните ключ — он показывается один раз."}


@app.delete("/admin/keys/{key_id}")
async def admin_revoke_key(key_id: str, api_key: str = Depends(require_admin_permission)):
    """Отозвать API ключ (требует ADMIN)."""
    if key_manager.revoke_key(key_id):
        return {"message": f"Ключ {key_id} отозван."}
    raise HTTPException(status_code=404, detail="Ключ не найден")

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
