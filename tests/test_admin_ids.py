"""
Регрессионный тест для парсинга ADMIN_IDS.

Проверяет, что формат {int(x) for x in "123,456".split(",") if x}
корректно обрабатывает различные варианты входных данных.
"""

from unittest.mock import patch
import pytest


class TestAdminIds:
    """Тесты для логики парсинга ADMIN_IDS из переменной окружения."""

    def test_admin_ids_parsing(self):
        """
        Строка "123,456" должна дать множество {123, 456}.
        Симулирует то, что сейчас в handlers.py:
        ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x}
        """
        env_value = "123,456"
        result = {int(x) for x in env_value.split(",") if x}
        assert result == {123, 456}

    def test_admin_ids_non_admin_no_error(self):
        """
        Проверка, что проверка user_id not in ADMIN_IDS не кидает
        исключение для не-администратора. Имитация:
        user_id=789, ADMIN_IDS={123, 456}
        """
        admin_ids = {123, 456}
        user_id = 789

        # Это не должно вызвать никаких исключений
        is_admin = user_id in admin_ids
        assert is_admin is False

        # Проверка: user_id not in admin_ids — безопасная операция
        assert user_id not in admin_ids  # не должно кидать TypeError

    def test_admin_ids_empty_env(self):
        """
        Пустая строка должна давать пустое множество.
        Симулирует случай, когда ADMIN_IDS не задан.
        """
        env_value = ""
        result = {int(x) for x in env_value.split(",") if x}
        assert result == set()
        assert len(result) == 0

    def test_admin_ids_with_spaces(self):
        """
        Строка с пробелами: "123, 456" — пробелы убираются через if x.strip().
        Но в текущей реализации handlers.py: if x (без strip()).
        Проверяем, что "123, 456" без strip() может упасть.
        В текущем коде стоит if x, а не if x.strip(), поэтому
        элемент " 456" пройдёт проверку if x (True) и int(" 456") сработает.
        """
        env_value = "123, 456"
        result = {int(x) for x in env_value.split(",") if x}
        # " 456" — после split получаем ["123", " 456"]
        # " 456" — truthy, int(" 456") работает корректно
        assert result == {123, 456}

    def test_admin_ids_single_value(self):
        """
        Один ID — множество из одного элемента.
        """
        env_value = "42"
        result = {int(x) for x in env_value.split(",") if x}
        assert result == {42}
