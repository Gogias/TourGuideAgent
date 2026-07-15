"""
Юнит-тесты для тула route_link (get_route_link).

Тул не делает HTTP-запросов — только форматирование строки.
Тесты чисто на корректность формирования URL.
"""

from unittest.mock import patch
import pytest
import route_link


class TestRouteLink:
    """Тесты для get_route_link: разные виды транспорта."""

    def test_route_link_default_transport(self):
        """
        Маршрут по умолчанию (пешком).
        Проверяем rtt=pd и координаты в rtext.
        """
        # ═══ Act ═══
        result = route_link.get_route_link.invoke({
            "from_lat": 55.75,
            "from_lon": 37.61,
            "to_lat": 55.80,
            "to_lon": 37.70,
        })

        # ═══ Assert ═══
        assert "yandex.ru/maps/" in result
        assert "rtt=pd" in result, "По умолчанию должен быть пеший маршрут (pd)"
        assert "rtext=55.75,37.61~55.8,37.7" in result
        assert "пешком" in result

    def test_route_link_auto(self):
        """Маршрут на автомобиле — rtt=auto."""
        # ═══ Act ═══
        result = route_link.get_route_link.invoke({
            "from_lat": 55.75,
            "from_lon": 37.61,
            "to_lat": 55.80,
            "to_lon": 37.70,
            "transport": "авто",
        })

        # ═══ Assert ═══
        assert "rtt=auto" in result
        assert "автомобиле" in result

    def test_route_link_public_transport(self):
        """Маршрут на общественном транспорте — rtt=mt."""
        # ═══ Act ═══
        result = route_link.get_route_link.invoke({
            "from_lat": 55.75,
            "from_lon": 37.61,
            "to_lat": 55.80,
            "to_lon": 37.70,
            "transport": "транспорт",
        })

        # ═══ Assert ═══
        assert "rtt=mt" in result
        assert "общественном транспорте" in result
