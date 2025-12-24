import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path


class MinecraftLogParser:
    """Парсер логов Minecraft для быстрой демонстрации"""

    def __init__(self, log_dir: str = "./demo_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Создаем демо-логи, если их нет
        self._create_demo_logs()

    def _create_demo_logs(self):
        """Создание демо-логов для презентации"""
        demo_log = self.log_dir / "latest.log"
        if not demo_log.exists():
            demo_content = """[14:30:15] [Server thread/INFO]: Starting minecraft server version 1.20.1
[14:30:16] [Server thread/INFO]: Loading properties
[14:30:17] [Server thread/INFO]: Default game type: SURVIVAL
[14:30:18] [Server thread/INFO]: Generating keypair
[14:30:19] [Server thread/INFO]: Starting Minecraft server on *:25565
[14:30:20] [Server thread/INFO]: Using epoll channel type
[14:30:21] [Server thread/INFO]: Preparing level "world"
[14:30:25] [Server thread/INFO]: Done (4.123s)! For help, type "help"
[14:31:10] [Server thread/INFO]: Alex joined the game
[14:31:15] [Server thread/INFO]: Steve joined the game
[14:32:20] [Server thread/INFO]: Notch joined the game
[14:35:10] [Server thread/WARN]: Can't keep up! Is the server overloaded? Running 2000ms behind, skipping 40 tick(s)
[14:40:30] [Server thread/INFO]: Alex lost connection: Disconnected
[14:45:22] [Server thread/ERROR]: Exception in thread "Server thread"
[14:50:00] [Server thread/INFO]: Herobrine joined the game
[14:55:10] [Server thread/INFO]: There are 3 of a max 20 players online: Steve, Notch, Herobrine
"""
            demo_log.write_text(demo_content, encoding='utf-8')

    def parse_online_players(self) -> List[str]:
        """Парсит игроков онлайн из логов"""
        players = []
        log_file = self.log_dir / "latest.log"

        if not log_file.exists():
            return ["Alex", "Steve", "Notch"]  # Демо данные

        content = log_file.read_text(encoding='utf-8', errors='ignore')

        # Ищем игроков, которые зашли
        join_pattern = r'(\w+) joined the game'
        players_joined = re.findall(join_pattern, content)

        # Ищем игроков, которые вышли
        leave_pattern = r'(\w+) lost connection'
        players_left = re.findall(leave_pattern, content)

        # Простая логика: кто зашел и не вышел
        for player in players_joined:
            if player not in players_left:
                players.append(player)

        # Если не нашли, возвращаем демо-данные
        return players if players else ["Steve", "Notch", "Herobrine"]

    def parse_server_stats(self) -> Dict[str, any]:
        """Парсит базовую статистику сервера"""
        stats = {
            'online_players': 0,
            'total_players': 0,
            'errors_count': 0,
            'warnings_count': 0,
            'last_restart': None,
            'uptime': '5ч 30м'
        }

        log_file = self.log_dir / "latest.log"
        if not log_file.exists():
            stats.update({
                'online_players': 3,
                'total_players': 15,
                'errors_count': 2,
                'warnings_count': 1,
                'last_restart': '14:30'
            })
            return stats

        content = log_file.read_text(encoding='utf-8', errors='ignore')
        lines = content.split('\n')

        # Подсчет статистики
        stats['online_players'] = len(self.parse_online_players())
        stats['errors_count'] = sum(1 for line in lines if 'ERROR' in line)
        stats['warnings_count'] = sum(1 for line in lines if 'WARN' in line)

        # Ищем время запуска
        for line in lines:
            if 'Done' in line and 'For help' in line:
                time_match = re.search(r'\[(\d{2}:\d{2}:\d{2})\]', line)
                if time_match:
                    stats['last_restart'] = time_match.group(1)
                break

        return stats

    def search_logs(self, pattern: str, limit: int = 10) -> List[str]:
        """Поиск по логам с регулярным выражением"""
        log_file = self.log_dir / "latest.log"
        if not log_file.exists():
            return [f"Demo match for: {pattern}"]

        content = log_file.read_text(encoding='utf-8', errors='ignore')
        matches = re.findall(pattern, content, re.IGNORECASE)

        return matches[:limit]