"""
Основное FastAPI приложение для Ephemeris Decoder
"""

from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import uvicorn

from services.ephem import (
    get_planets, get_aspects, get_houses, get_moon_phase,
    initialize_ephemeris, cleanup_ephemeris
)

# Создаём FastAPI приложение
app = FastAPI(
    title="Ephemeris Decoder",
    description="Микросервис для работы со Swiss Ephemeris",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Добавляем CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели для валидации
class DateTimeQuery(BaseModel):
    datetime: str
    
    @validator('datetime')
    def validate_datetime(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('Неверный формат datetime. Используйте ISO 8601 (YYYY-MM-DDTHH:MM:SS)')

class CoordinatesQuery(BaseModel):
    lat: float
    lon: float
    
    @validator('lat')
    def validate_lat(cls, v):
        if not -90 <= v <= 90:
            raise ValueError('Широта должна быть в диапазоне от -90 до 90 градусов')
        return v
    
    @validator('lon')
    def validate_lon(cls, v):
        if not -180 <= v <= 180:
            raise ValueError('Долгота должна быть в диапазоне от -180 до 180 градусов')
        return v

# События жизненного цикла
@app.on_event("startup")
async def startup_event():
    """Инициализация при старте"""
    initialize_ephemeris()

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка при завершении"""
    cleanup_ephemeris()

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
            "moon_phase": "/moon_phase"
        }
    }

@app.get("/planets")
async def planets(
    datetime_str: str = Query(..., description="Время в формате ISO 8601 (YYYY-MM-DDTHH:MM:SS)"),
    lat: float = Query(..., ge=-90, le=90, description="Широта в градусах"),
    lon: float = Query(..., ge=-180, le=180, description="Долгота в градусах"),
    extra: bool = Query(False, description="Включить дополнительные точки (узлы, фиктивные планеты)")
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
    lon: float = Query(..., ge=-180, le=180, description="Долгота в градусах")
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
    lon: float = Query(..., ge=-180, le=180, description="Долгота в градусах")
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
    datetime_str: str = Query(..., description="Время в формате ISO 8601 (YYYY-MM-DDTHH:MM:SS)")
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

# Эндпоинт для проверки здоровья
@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Ephemeris Decoder"
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


