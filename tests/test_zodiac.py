"""
Тесты для утилит зодиака
"""

import pytest
from utils.zodiac import (
    degrees_to_sign_and_degrees,
    normalize_angle,
    calculate_orb,
    ZODIAC_SIGNS,
    ZODIAC_DEGREES
)


class TestZodiacUtils:
    """Тесты для функций зодиака"""
    
    def test_zodiac_constants(self):
        """Тест констант зодиака"""
        assert len(ZODIAC_SIGNS) == 12
        assert ZODIAC_DEGREES == 30
        assert ZODIAC_SIGNS[0] == "Овен"
        assert ZODIAC_SIGNS[11] == "Рыбы"
    
    def test_degrees_to_sign_and_degrees_basic(self):
        """Тест базового преобразования градусов в знак"""
        # Овен (0-29.99 градуса)
        sign, degrees = degrees_to_sign_and_degrees(0)
        assert sign == "Овен"
        assert degrees == 0.0
        
        sign, degrees = degrees_to_sign_and_degrees(15)
        assert sign == "Овен"
        assert degrees == 15.0
        
        sign, degrees = degrees_to_sign_and_degrees(29.99)
        assert sign == "Овен"
        assert degrees == 29.99
        
        # Телец (30-59.99 градуса)
        sign, degrees = degrees_to_sign_and_degrees(30)
        assert sign == "Телец"
        assert degrees == 0.0
        
        sign, degrees = degrees_to_sign_and_degrees(45)
        assert sign == "Телец"
        assert degrees == 15.0
    
    def test_degrees_to_sign_and_degrees_boundaries(self):
        """Тест граничных значений знаков"""
        # Граница между Овном и Тельцом
        sign, degrees = degrees_to_sign_and_degrees(30)
        assert sign == "Телец"
        assert degrees == 0.0
        
        # Граница между Рыбами и Овном
        sign, degrees = degrees_to_sign_and_degrees(360)
        assert sign == "Овен"
        assert degrees == 0.0
        
        sign, degrees = degrees_to_sign_and_degrees(359.99)
        assert sign == "Рыбы"
        assert degrees == 29.99
    
    def test_degrees_to_sign_and_degrees_negative(self):
        """Тест отрицательных градусов"""
        # -30 градусов = 330 градусов = Рыбы
        sign, degrees = degrees_to_sign_and_degrees(-30)
        assert sign == "Рыбы"
        assert degrees == 0.0
        
        # -90 градусов = 270 градусов = Козерог
        sign, degrees = degrees_to_sign_and_degrees(-90)
        assert sign == "Козерог"
        assert degrees == 0.0
    
    def test_degrees_to_sign_and_degrees_large_values(self):
        """Тест больших значений градусов"""
        # 720 градусов = 0 градусов = Овен
        sign, degrees = degrees_to_sign_and_degrees(720)
        assert sign == "Овен"
        assert degrees == 0.0
        
        # 1234.56 градусов = 154.56 градусов = Дева
        sign, degrees = degrees_to_sign_and_degrees(1234.56)
        assert sign == "Дева"
        assert degrees == 4.56
    
    def test_normalize_angle(self):
        """Тест нормализации углов"""
        assert normalize_angle(0) == 0
        assert normalize_angle(360) == 0
        assert normalize_angle(720) == 0
        assert normalize_angle(-90) == 270
        assert normalize_angle(450) == 90
        assert normalize_angle(180) == 180
    
    def test_calculate_orb(self):
        """Тест вычисления орбиса"""
        # Простые случаи
        assert calculate_orb(0, 10) == 10
        assert calculate_orb(10, 0) == 10
        assert calculate_orb(180, 190) == 10
        
        # Граничные случаи
        assert calculate_orb(0, 180) == 180
        assert calculate_orb(0, 360) == 0
        assert calculate_orb(0, 359) == 1
        
        # Большие углы
        assert calculate_orb(350, 10) == 20
        assert calculate_orb(10, 350) == 20
        
        # Одинаковые углы
        assert calculate_orb(45, 45) == 0
        assert calculate_orb(180, 180) == 0
    
    def test_all_zodiac_signs(self):
        """Тест всех знаков зодиака"""
        expected_signs = [
            "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева",
            "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
        ]
        
        for i, expected_sign in enumerate(expected_signs):
            start_degree = i * 30
            sign, degrees = degrees_to_sign_and_degrees(start_degree)
            assert sign == expected_sign
            assert degrees == 0.0
            
            # Проверяем середину знака
            mid_degree = start_degree + 15
            sign, degrees = degrees_to_sign_and_degrees(mid_degree)
            assert sign == expected_sign
            assert degrees == 15.0


