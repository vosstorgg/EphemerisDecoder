#!/usr/bin/env python3
"""
Пример использования API для построения натальных карт
"""

import requests
import json
from datetime import datetime

# Конфигурация
BASE_URL = "http://localhost:8000"  # Замените на ваш URL
API_KEY = "your-api-key-here"       # Замените на ваш API ключ

def create_natal_chart(year, month, day, hour, minute, city, nation, lat, lon, timezone=None):
    """
    Создаёт натальную карту через API
    
    Args:
        year: Год рождения
        month: Месяц рождения
        day: День рождения
        hour: Час рождения
        minute: Минута рождения
        city: Город рождения
        nation: Страна рождения
        lat: Широта места рождения
        lon: Долгота места рождения
        timezone: Часовой пояс (опционально)
    
    Returns:
        dict: Данные натальной карты или None в случае ошибки
    """
    url = f"{BASE_URL}/natal_chart"
    headers = {
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "minute": minute,
        "city": city,
        "nation": nation,
        "lat": lat,
        "lon": lon
    }
    
    if timezone:
        payload["timezone"] = timezone
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка API {response.status_code}: {response.text}")
            return None
            
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return None

def display_natal_chart_summary(chart_data):
    """
    Выводит краткое описание натальной карты
    
    Args:
        chart_data: Данные натальной карты от API
    """
    if not chart_data:
        print("Нет данных для отображения")
        return
    
    subject_info = chart_data.get("subject_info", {})
    planets = chart_data.get("planets", {})
    houses = chart_data.get("houses", [])
    aspects = chart_data.get("aspects", [])
    statistics = chart_data.get("statistics", {})
    
    print("=" * 60)
    print("🌟 НАТАЛЬНАЯ КАРТА")
    print("=" * 60)
    
    # Информация о рождении
    print(f"📅 Дата рождения: {subject_info.get('birth_date', 'Неизвестно')}")
    print(f"🕐 Время рождения: {subject_info.get('birth_time', 'Неизвестно')}")
    print(f"📍 Место: {subject_info.get('location', 'Неизвестно')}")
    print(f"🌍 Координаты: {subject_info.get('coordinates', 'Неизвестно')}")
    print()
    
    # Планеты
    print("🪐 ПЛАНЕТЫ:")
    print("-" * 40)
    for planet_name, planet_info in planets.items():
        symbol = planet_info.get("symbol", "")
        sign = planet_info.get("sign", "")
        sign_symbol = planet_info.get("sign_symbol", "")
        degrees = planet_info.get("degrees_in_sign", 0)
        house = planet_info.get("house", 0)
        retrograde = " ℞" if planet_info.get("retrograde", False) else ""
        
        print(f"{symbol} {planet_name:12} в {sign_symbol} {sign:12} {degrees:6.2f}° (Дом {house}){retrograde}")
    
    print()
    
    # Статистика по элементам
    if statistics:
        elements = statistics.get("elements_distribution", {})
        qualities = statistics.get("qualities_distribution", {})
        
        print("📊 СТАТИСТИКА:")
        print("-" * 40)
        print("Элементы:")
        for element, count in elements.items():
            print(f"  {element:8}: {count} планет")
        
        print("Качества:")
        for quality, count in qualities.items():
            print(f"  {quality:8}: {count} планет")
        
        print()
    
    # Мажорные аспекты
    major_aspects = [a for a in aspects if a.get("is_major", False)]
    if major_aspects:
        print(f"🔗 МАЖОРНЫЕ АСПЕКТЫ ({len(major_aspects)}):")
        print("-" * 40)
        for aspect in major_aspects[:10]:  # Показываем первые 10
            planet1 = aspect.get("planet1", "")
            planet2 = aspect.get("planet2", "")
            aspect_name = aspect.get("aspect", "")
            orb = aspect.get("orb", 0)
            
            print(f"{planet1:12} {aspect_name:12} {planet2:12} (орб: {orb:.2f}°)")
        
        if len(major_aspects) > 10:
            print(f"... и ещё {len(major_aspects) - 10} аспектов")

def display_chart_data_structure(chart_data):
    """
    Показывает структуру данных для построения круговой диаграммы
    
    Args:
        chart_data: Данные натальной карты от API
    """
    if not chart_data:
        print("Нет данных для отображения")
        return
    
    chart_visual_data = chart_data.get("chart_data", {})
    
    print("\n" + "=" * 60)
    print("🎯 ДАННЫЕ ДЛЯ ПОСТРОЕНИЯ КРУГОВОЙ ДИАГРАММЫ")
    print("=" * 60)
    
    # Внешний круг зодиака
    inner_circle = chart_visual_data.get("inner_circle", [])
    print(f"🔸 Внешний круг зодиака: {len(inner_circle)} знаков")
    if inner_circle:
        print("   Знаки:", ", ".join([f"{s['symbol']} {s['name']}" for s in inner_circle[:4]]), "...")
    
    # Круг домов
    houses_circle = chart_visual_data.get("houses_circle", [])
    print(f"🔸 Круг домов: {len(houses_circle)} домов")
    if houses_circle:
        print(f"   Первый дом начинается с {houses_circle[0].get('start_angle', 0):.1f}°")
    
    # Планеты на круге
    planets_circle = chart_visual_data.get("planets_circle", [])
    print(f"🔸 Планеты на круге: {len(planets_circle)} планет")
    if planets_circle:
        first_planet = planets_circle[0]
        print(f"   Первая планета: {first_planet.get('symbol', '')} {first_planet.get('name', '')} на {first_planet.get('angle', 0):.1f}°")
    
    # Линии аспектов
    aspect_lines = chart_visual_data.get("aspects_lines", [])
    print(f"🔸 Линии аспектов: {len(aspect_lines)} линий")
    if aspect_lines:
        print("   Типы аспектов:", ", ".join(set([a.get('aspect_type', '') for a in aspect_lines])))
    
    print("\n💡 Эти данные можно использовать для построения натальной карты")
    print("   с помощью библиотек визуализации (matplotlib, plotly, d3.js и др.)")

def main():
    """Основная функция для демонстрации"""
    print("🚀 Пример использования API натальных карт")
    print()
    
    # Пример данных (Джон Леннон)
    year = 1940
    month = 10
    day = 9
    hour = 18
    minute = 30
    city = "Ливерпуль"
    nation = "Великобритания"
    lat = 53.4084
    lon = -2.9916
    timezone = "+00:00"
    
    print(f"📋 Создаём натальную карту")
    print(f"📅 Дата: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}")
    print(f"📍 Место: {city}, {nation}")
    print()
    
    # Создаём натальную карту
    chart_data = create_natal_chart(
        year=year, 
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        city=city,
        nation=nation,
        lat=lat,
        lon=lon,
        timezone=timezone
    )
    
    if chart_data:
        # Показываем краткое описание
        display_natal_chart_summary(chart_data)
        
        # Показываем структуру данных для построения диаграммы
        display_chart_data_structure(chart_data)
        
        # Сохраняем данные в файл для дальнейшего использования
        with open("natal_chart_example.json", "w", encoding="utf-8") as f:
            json.dump(chart_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Полные данные сохранены в файл 'natal_chart_example.json'")
        
    else:
        print("❌ Не удалось получить данные натальной карты")
        print("   Проверьте:")
        print("   1. Работает ли API сервер")
        print("   2. Правильный ли API ключ")
        print("   3. Доступность библиотеки kerykeion")

if __name__ == "__main__":
    main()
