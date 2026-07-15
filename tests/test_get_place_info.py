"""
Юнит-тесты для тула get_place_info.

Мокаем get_place_info.requests.get, чтобы не было реальных HTTP-запросов.
"""

from unittest.mock import patch, MagicMock
import pytest
import get_place_info


class TestGetPlaceInfo:
    """Тесты для get_place_info: успех, ошибка API, таймаут."""

    @patch("get_place_info.requests.get")
    def test_get_place_info_success(self, mock_get):
        """Успешный reverse геокодинг — возвращает city, country, full_address."""
        # ═══ Arrange ═══
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "address": {
                "city": "Москва",
                "suburb": "Тверской район",
                "state": "Москва",
                "country": "Россия",
            },
            "display_name": "Москва, Россия",
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # ═══ Act ═══
        result = get_place_info.get_place_info.invoke(
            {"lat": 55.7558, "lon": 37.6173}
        )

        # ═══ Assert ═══
        assert "error" not in result, f"Не ожидали ошибку: {result}"
        assert result["city"] == "Москва"
        assert result["district"] == "Тверской район"
        assert result["state"] == "Москва"
        assert result["country"] == "Россия"
        assert result["full_address"] == "Москва, Россия"

    @patch("get_place_info.requests.get")
    def test_get_place_info_api_error(self, mock_get):
        """API возвращает {'error': '...'} — пробрасываем ошибку."""
        # ═══ Arrange ═══
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "rate limit exceeded"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # ═══ Act ═══
        result = get_place_info.get_place_info.invoke(
            {"lat": 55.7558, "lon": 37.6173}
        )

        # ═══ Assert ═══
        assert "error" in result
        assert result["error"] == "rate limit exceeded"

    @patch("get_place_info.requests.get")
    def test_get_place_info_timeout(self, mock_get):
        """Таймаут при запросе — возвращает ошибку."""
        # ═══ Arrange ═══
        mock_get.side_effect = __import__("requests").exceptions.Timeout(
            "Connection timed out"
        )

        # ═══ Act ═══
        result = get_place_info.get_place_info.invoke(
            {"lat": 55.7558, "lon": 37.6173}
        )

        # ═══ Assert ═══
        assert "error" in result
        assert "Ошибка запроса к Nominatim" in result["error"]
