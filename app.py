"""
Основное FastAPI приложение для Ephemeris Decoder
"""

from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from contextlib import asynccontextmanager
import uvicorn

from services.ephem import (
    get_planets, get_aspects, get_houses, get_moon_phase,
    initialize_ephemeris, cleanup_ephemeris
)
from services.natal_chart import (
    calculate_natal_chart, validate_birth_data, get_timezone_by_coordinates
)
from utils.auth import APIKeyManager, APIKeyPermission, key_manager
from utils.middleware import (
    AuthenticationMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    require_read_permission
)

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    initialize_ephemeris()
    yield
    # Shutdown
    cleanup_ephemeris()

# Создаём FastAPI приложение
app = FastAPI(
    title="Ephemeris Decoder",
    description="Микросервис для работы со Swiss Ephemeris",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Добавляем security headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# Добавляем rate limiting middleware
app.add_middleware(RateLimitMiddleware, max_requests_per_minute=100)

# Добавляем authentication middleware
app.add_middleware(AuthenticationMiddleware)

# Модели для валидации
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

# Основные эндпоинты
@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": "Ephemeris Decoder API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "planets": "/planets",
            "aspects": "/aspects", 
            "houses": "/houses",
            "moon_phase": "/moon_phase",
            "natal_chart": "/natal_chart"
        }
    }

@app.get("/planets")
async def planets(
    datetime_str: str = Query(..., description="Время в формате ISO 8601 (YYYY-MM-DDTHH:MM:SS)"),
    lat: float = Query(..., ge=-90, le=90, description="Широта в градусах"),
    lon: float = Query(..., ge=-180, le=180, description="Долгота в градусах"),
    extra: bool = Query(False, description="Включить дополнительные точки (узлы, фиктивные планеты)"),
    api_key: str = Depends(require_read_permission)
):
    """
    Получение позиций планет на указанное время и место
    
    - **datetime**: Время в формате ISO 8601
    - **lat**: Широта в градусах (-90 до 90)
    - **lon**: Долгота в градусах (-180 до 180)
    - **extra**: Включить дополнительные точки
    """
    try:
        # Парсим datetime
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        
        # Получаем планеты
        result = await get_planets(dt, lat, lon, extra)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Ошибка валидации: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")

@app.get("/aspects")
async def aspects(
    datetime_str: str = Query(..., description="Время в формате ISO 8601 (YYYY-MM-DDTHH:MM:SS)"),
    lat: float = Query(..., ge=-90, le=90, description="Широта в градусах"),
    lon: float = Query(..., ge=-180, le=180, description="Долгота в градусах"),
    api_key: str = Depends(require_read_permission)
):
    """
    Расчёт аспектов между планетами
    
    - **datetime**: Время в формате ISO 8601
    - **lat**: Широта в градусах (-90 до 90)
    - **lon**: Долгота в градусах (-180 до 180)
    """
    try:
        # Парсим datetime
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        
        # Получаем аспекты
        result = await get_aspects(dt, lat, lon)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Ошибка валидации: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")

@app.get("/houses")
async def houses(
    datetime_str: str = Query(..., description="Время в формате ISO 8601 (YYYY-MM-DDTHH:MM:SS)"),
    lat: float = Query(..., ge=-90, le=90, description="Широта в градусах"),
    lon: float = Query(..., ge=-180, le=180, description="Долгота в градусах"),
    api_key: str = Depends(require_read_permission)
):
    """
    Определение границ домов (Whole Sign)
    
    - **datetime**: Время в формате ISO 8601
    - **lat**: Широта в градусах (-90 до 90)
    - **lon**: Долгота в градусах (-180 до 180)
    """
    try:
        # Парсим datetime
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        
        # Получаем дома
        result = await get_houses(dt, lat, lon)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Ошибка валидации: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")

@app.get("/moon_phase")
async def moon_phase(
    datetime_str: str = Query(..., description="Время в формате ISO 8601 (YYYY-MM-DDTHH:MM:SS)"),
    api_key: str = Depends(require_read_permission)
):
    """
    Расчёт фазы Луны
    
    - **datetime**: Время в формате ISO 8601
    """
    try:
        # Парсим datetime
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        
        # Получаем фазу Луны
        result = await get_moon_phase(dt)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Ошибка валидации: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка: {str(e)}")

@app.post("/natal_chart")
async def natal_chart(
    request: NatalChartRequest,
    api_key: str = Depends(require_read_permission)
):
    """
    Расчёт натальной карты на основе данных о рождении
    
    Принимает данные о рождении и возвращает полную натальную карту 
    с данными для построения круговой диаграммы.
    
    - **year**: Год рождения (1900-текущий)
    - **month**: Месяц рождения (1-12)
    - **day**: День рождения (1-31)
    - **hour**: Час рождения (0-23)
    - **minute**: Минута рождения (0-59)
    - **city**: Город рождения
    - **nation**: Страна рождения
    - **lat**: Широта места рождения (-90 до 90)
    - **lon**: Долгота места рождения (-180 до 180)
    - **timezone**: Часовой пояс (опционально, будет вычислен автоматически)
    """
    try:
        # Валидируем данные рождения
        is_valid, error_msg = validate_birth_data(
            request.year, request.month, request.day, 
            request.hour, request.minute
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Ошибка валидации данных рождения: {error_msg}")
        
        # Определяем часовой пояс, если не указан
        timezone = request.timezone
        if not timezone:
            timezone = get_timezone_by_coordinates(request.lat, request.lon)
        
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

# API эндпоинты для управления ключами (требуют ADMIN прав)
from utils.middleware import require_admin_permission

@app.post("/admin/keys")
async def create_api_key(
    name: str = Query(..., description="Имя ключа"),
    permissions: str = Query("read", description="Разрешения через запятую (read,write,admin)"),
    expires_days: Optional[int] = Query(None, description="Дни до истечения (None - бессрочный)"),
    rate_limit: int = Query(100, description="Лимит запросов в час"),
    api_key: str = Depends(require_admin_permission)
):
    """
    Создать новый API ключ (требует ADMIN прав)

    - **name**: Человеко-читаемое имя ключа
    - **permissions**: Разрешения через запятую
    - **expires_days**: Дни до истечения (опционально)
    - **rate_limit**: Максимум запросов в час
    """
    try:
        # Парсим разрешения
        perm_list = []
        for perm in permissions.split(","):
            perm = perm.strip().lower()
            if perm == "read":
                perm_list.append(APIKeyPermission.READ)
            elif perm == "write":
                perm_list.append(APIKeyPermission.WRITE)
            elif perm == "admin":
                perm_list.append(APIKeyPermission.ADMIN)

        if not perm_list:
            perm_list = [APIKeyPermission.READ]

        # Генерируем ключ
        raw_key, api_key_obj = key_manager.generate_key(
            name=name,
            permissions=perm_list,
            expires_days=expires_days,
            rate_limit=rate_limit
        )

        return {
            "message": "API key created successfully",
            "key_id": api_key_obj.key_id,
            "api_key": raw_key,  # ВАЖНО: возвращаем сырой ключ только при создании!
            "name": api_key_obj.name,
            "permissions": [p.value for p in api_key_obj.permissions],
            "expires_at": api_key_obj.expires_at.isoformat() if api_key_obj.expires_at else None,
            "rate_limit": api_key_obj.rate_limit,
            "warning": "Save this API key securely - it won't be shown again!"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create API key: {str(e)}")

@app.get("/admin/keys")
async def list_api_keys(api_key: str = Depends(require_admin_permission)):
    """Получить список всех API ключей (требует ADMIN прав)"""
    try:
        stats = key_manager.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get keys: {str(e)}")

@app.delete("/admin/keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    api_key: str = Depends(require_admin_permission)
):
    """Отозвать API ключ (требует ADMIN прав)"""
    try:
        success = key_manager.revoke_key(key_id)
        if success:
            return {"message": f"API key {key_id} revoked successfully"}
        else:
            raise HTTPException(status_code=404, detail=f"API key {key_id} not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to revoke key: {str(e)}")

@app.get("/admin/keys/{key_id}")
async def get_api_key(
    key_id: str,
    api_key: str = Depends(require_admin_permission)
):
    """Получить информацию о конкретном API ключе (требует ADMIN прав)"""
    try:
        key_obj = key_manager.get_key_by_id(key_id)
        if not key_obj:
            raise HTTPException(status_code=404, detail=f"API key {key_id} not found")

        return {
            "key_id": key_obj.key_id,
            "name": key_obj.name,
            "permissions": [p.value for p in key_obj.permissions],
            "is_active": key_obj.is_active,
            "created_at": key_obj.created_at.isoformat(),
            "expires_at": key_obj.expires_at.isoformat() if key_obj.expires_at else None,
            "usage_count": key_obj.usage_count,
            "rate_limit": key_obj.rate_limit,
            "is_expired": key_obj.is_expired()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get key: {str(e)}")

# Эндпоинт для проверки здоровья
@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Ephemeris Decoder",
        "api_keys_count": len(key_manager.list_keys()),
        "authentication": "enabled"
    }

# Обработка ошибок
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Обработчик ошибок валидации"""
    raise HTTPException(status_code=400, detail=str(exc))

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Общий обработчик ошибок"""
    raise HTTPException(status_code=500, detail="Внутренняя ошибка сервера")

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


