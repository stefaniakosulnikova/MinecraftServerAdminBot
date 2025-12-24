import unittest
from datetime import datetime, timedelta
from domain.server_status import ServerStatus


class TestServerStatus(unittest.TestCase):

    def setUp(self):
        self.test_datetime = datetime(2024, 1, 1, 12, 0, 0)

    def test_valid_creation(self):
        """Тест создания валидного объекта ServerStatus"""
        status = ServerStatus(
            is_online=True,
            player_count=5,
            max_players=20,
            tps=19.5,
            memory_used_mb=2048,
            memory_total_mb=4096,
            uptime_seconds=3600,
            last_checked=self.test_datetime
        )

        self.assertTrue(status.is_online)
        self.assertEqual(status.player_count, 5)
        self.assertEqual(status.max_players, 20)
        self.assertEqual(status.tps, 19.5)
        self.assertEqual(status.memory_used_mb, 2048)
        self.assertEqual(status.memory_total_mb, 4096)
        self.assertEqual(status.uptime_seconds, 3600)
        self.assertEqual(status.last_checked, self.test_datetime)

    def test_negative_player_count_validation(self):
        """Тест валидации отрицательного количества игроков"""
        with self.assertRaises(ValueError) as context:
            ServerStatus(
                is_online=True,
                player_count=-1,
                max_players=20,
                tps=19.5,
                memory_used_mb=2048,
                memory_total_mb=4096,
                uptime_seconds=3600,
                last_checked=self.test_datetime
            )

        self.assertIn("Количество игроков не может быть отрицательным", str(context.exception))

    def test_negative_tps_validation(self):
        """Тест валидации отрицательного TPS"""
        with self.assertRaises(ValueError) as context:
            ServerStatus(
                is_online=True,
                player_count=5,
                max_players=20,
                tps=-1.0,
                memory_used_mb=2048,
                memory_total_mb=4096,
                uptime_seconds=3600,
                last_checked=self.test_datetime
            )

        self.assertIn("TPS не может быть отрицательным", str(context.exception))

    def test_player_ratio_calculation(self):
        """Тест расчета процента заполненности сервера"""
        test_cases = [
            (5, 20, 25.0),  # 5/20 = 25%
            (10, 10, 100.0),  # 10/10 = 100%
            (0, 20, 0.0),  # 0/20 = 0%
            (15, 20, 75.0),  # 15/20 = 75%
            (0, 0, 0.0),  # 0/0 = 0% (специальный случай)
        ]

        for players, max_players, expected_ratio in test_cases:
            with self.subTest(players=players, max_players=max_players):
                status = ServerStatus(
                    is_online=True,
                    player_count=players,
                    max_players=max_players,
                    tps=19.5,
                    memory_used_mb=2048,
                    memory_total_mb=4096,
                    uptime_seconds=3600,
                    last_checked=self.test_datetime
                )

                self.assertAlmostEqual(status.player_ratio, expected_ratio, places=2)

    def test_uptime_hours_calculation(self):
        """Тест конвертации аптайма из секунд в часы"""
        test_cases = [
            (3600, 1.0),  # 1 час
            (7200, 2.0),  # 2 часа
            (1800, 0.5),  # 30 минут = 0.5 часа
            (0, 0.0),  # 0 секунд
            (4500, 1.25),  # 1 час 15 минут
        ]

        for seconds, expected_hours in test_cases:
            with self.subTest(seconds=seconds):
                status = ServerStatus(
                    is_online=True,
                    player_count=5,
                    max_players=20,
                    tps=19.5,
                    memory_used_mb=2048,
                    memory_total_mb=4096,
                    uptime_seconds=seconds,
                    last_checked=self.test_datetime
                )

                self.assertAlmostEqual(status.uptime_hours, expected_hours, places=2)

    def test_offline_server(self):
        """Тест создания объекта для оффлайн сервера"""
        status = ServerStatus(
            is_online=False,
            player_count=0,
            max_players=20,
            tps=0.0,
            memory_used_mb=0,
            memory_total_mb=4096,
            uptime_seconds=0,
            last_checked=self.test_datetime
        )

        self.assertFalse(status.is_online)
        self.assertEqual(status.player_ratio, 0.0)
        self.assertEqual(status.uptime_hours, 0.0)

    def test_equality_comparison(self):
        """Тест сравнения объектов ServerStatus"""
        status1 = ServerStatus(
            is_online=True,
            player_count=5,
            max_players=20,
            tps=19.5,
            memory_used_mb=2048,
            memory_total_mb=4096,
            uptime_seconds=3600,
            last_checked=self.test_datetime
        )

        status2 = ServerStatus(
            is_online=True,
            player_count=5,
            max_players=20,
            tps=19.5,
            memory_used_mb=2048,
            memory_total_mb=4096,
            uptime_seconds=3600,
            last_checked=self.test_datetime
        )

        # dataclass должен реализовывать __eq__ автоматически
        self.assertEqual(status1, status2)

    def test_memory_usage_properties(self):
        """Тест свойств связанных с памятью"""
        status = ServerStatus(
            is_online=True,
            player_count=5,
            max_players=20,
            tps=19.5,
            memory_used_mb=2048,
            memory_total_mb=4096,
            uptime_seconds=3600,
            last_checked=self.test_datetime
        )

        memory_usage_ratio = status.memory_used_mb / status.memory_total_mb
        self.assertAlmostEqual(memory_usage_ratio, 0.5, places=2)


if __name__ == '__main__':
    unittest.main()