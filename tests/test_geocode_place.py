"""
Юнит-тесты для тула geocode_place.

Мокаем geocode_place.requests.get, чтобы не было реальных HTTP-запросов.
"""

from unittest.mock import patch, MagicMock
import pytest
import geocode_place


class TestGeocodePlace:
    """Тесты для geocode_place: успех, не найдено, таймаут."""

    @patch("geocode_place.requests.get")
    def test_geocode_place_success(self, mock_get):
        """Успешное геокодирование — возвращает координаты и метаданные."""
        # ═══ Arrange ═══
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {
                "lat": "55.7558",
                "lon": "37.6173",
                "display_name": "Москва, Россия",
                "type": "city",
                "importance": 0.7,
            }
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # ═══ Act ═══
        result = geocode_place.geocode_place.invoke({"query": "Москва"})

        # ═══ Assert ═══
        assert "error" not in result, f"Не ожидали ошибку: {result}"
        assert result["lat"] == 55.7558
        assert result["lon"] == 37.6173
        assert result["display_name"] == "Москва, Россия"
        assert result["type"] == "city"
        assert result["importance"] == 0.7

        # Проверяем, что запрос был сделан с правильными параметрами
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == geocode_place.NOMINATIM_URL

    @patch("geocode_place.requests.get")
    def test_geocode_place_not_found(self, mock_get):
        """Пустой результат от Nominatim — возвращает ошибку."""
        # ═══ Arrange ═══
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # ═══ Act ═══
        query = "НесуществующееМесто12345"
        result = geocode_place.geocode_place.invoke({"query": query})

        # ═══ Assert ═══
        assert "error" in result
        assert "не найдено" in result["error"]
        assert query in result["error"]

    @patch("geocode_place.requests.get")
    def test_geocode_place_timeout(self, mock_get):
        """Таймаут при запросе — возвращает ошибку с сообщением."""
        # ═══ Arrange ═══
        mock_get.side_effect = __import__("requests").exceptions.Timeout(
            "Connection timed out"
        )

        # ═══ Act ═══
        result = geocode_place.geocode_place.invoke({"query": "Москва"})

        # ═══ Assert ═══
        assert "error" in result
        assert "тайм" in result["error"].lower() or "Ошибка запроса" in result["error"]
