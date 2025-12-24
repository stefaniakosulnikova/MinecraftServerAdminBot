import unittest
from domain.command_validator import CommandValidator, CommandType


class TestCommandValidator(unittest.TestCase):
    def setUp(self):
        self.validator = CommandValidator()

    # Тесты для validate_command
    def test_validate_command_empty_string(self):
        """Тест валидации пустой команды"""
        result = self.validator.validate_command("")
        self.assertFalse(result[0])
        self.assertEqual(result[2], "Команда не может быть пустой")

    def test_validate_command_whitespace(self):
        """Тест валидации команды из пробелов"""
        result = self.validator.validate_command("   ")
        self.assertFalse(result[0])
        self.assertEqual(result[2], "Команда не может быть пустой")

    def test_validate_command_allowed(self):
        """Тест валидации разрешенной команды"""
        commands = ["stop", "restart", "save-all", "list", "say hello",
                    "time set day", "weather clear", "gamemode creative",
                    "kick player", "ban player"]

        for cmd in commands:
            with self.subTest(command=cmd):
                result = self.validator.validate_command(cmd)
                self.assertTrue(result[0], f"Команда '{cmd}' должна быть разрешена")
                self.assertIsNone(result[2])

    def test_validate_command_not_allowed(self):
        """Тест валидации неразрешенной команды"""
        not_allowed_commands = ["op player", "deop player", "give diamond", "tp player"]

        for cmd in not_allowed_commands:
            with self.subTest(command=cmd):
                result = self.validator.validate_command(cmd)
                self.assertFalse(result[0])
                self.assertIn("не разрешена", result[2])

    def test_validate_command_preserves_case_but_normalizes(self):
        """Тест что команда нормализуется к нижнему регистру"""
        result = self.validator.validate_command("STOP")
        self.assertTrue(result[0])
        self.assertEqual(result[1], "stop")

    def test_validate_command_with_args(self):
        """Тест валидации команды с аргументами"""
        result = self.validator.validate_command("say Hello world!")
        self.assertTrue(result[0])
        self.assertEqual(result[1], "say hello world!")

    # Тесты для is_dangerous_command
    def test_is_dangerous_command_true(self):
        """Тест определения опасных команд"""
        dangerous_commands = ["stop", "restart", "ban player", "kick player", "op admin", "deop admin"]

        for cmd in dangerous_commands:
            with self.subTest(command=cmd):
                self.assertTrue(self.validator.is_dangerous_command(cmd),
                                f"Команда '{cmd}' должна быть опасной")

    def test_is_dangerous_command_false(self):
        """Тест что безопасные команды не считаются опасными"""
        safe_commands = ["list", "save-all", "say hello", "weather clear", ""]

        for cmd in safe_commands:
            with self.subTest(command=cmd):
                self.assertFalse(self.validator.is_dangerous_command(cmd),
                                 f"Команда '{cmd}' не должна быть опасной")

    def test_is_dangerous_command_empty(self):
        """Тест пустой команды"""
        self.assertFalse(self.validator.is_dangerous_command(""))

    # Тесты для get_command_type
    def test_get_command_type_valid(self):
        """Тест определения типа команды"""
        test_cases = [
            ("stop", CommandType.SERVER_MANAGEMENT),
            ("restart", CommandType.SERVER_MANAGEMENT),
            ("save-all", CommandType.SERVER_MANAGEMENT),
            ("list", CommandType.SERVER_INFO),
            ("say", CommandType.OTHER),
            ("time", CommandType.WORLD_MANAGEMENT),
            ("weather", CommandType.WORLD_MANAGEMENT),
            ("gamemode", CommandType.PLAYER_MANAGEMENT),
            ("kick", CommandType.PLAYER_MANAGEMENT),
            ("ban", CommandType.PLAYER_MANAGEMENT),
        ]

        for cmd, expected_type in test_cases:
            with self.subTest(command=cmd):
                result = self.validator.get_command_type(cmd)
                self.assertEqual(result, expected_type)

    def test_get_command_type_invalid(self):
        """Тест определения типа несуществующей команды"""
        self.assertIsNone(self.validator.get_command_type("nonexistent"))
        self.assertIsNone(self.validator.get_command_type(""))

    def test_get_command_type_with_args(self):
        """Тест определения типа команды с аргументами"""
        self.assertEqual(
            self.validator.get_command_type("gamemode creative player"),
            CommandType.PLAYER_MANAGEMENT
        )

    # Интеграционные тесты
    def test_validate_and_type_consistency(self):
        """Тест согласованности валидации и определения типа"""
        valid_command = "stop"
        is_valid, normalized, _ = self.validator.validate_command(valid_command)

        self.assertTrue(is_valid)
        command_type = self.validator.get_command_type(normalized)
        self.assertEqual(command_type, CommandType.SERVER_MANAGEMENT)


if __name__ == '__main__':
    unittest.main()