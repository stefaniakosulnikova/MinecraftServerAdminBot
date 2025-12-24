import re
from typing import List, Tuple, Optional
from enum import Enum


class CommandType(Enum):
    """Типы команд Minecraft"""
    SERVER_MANAGEMENT = "server_management"
    PLAYER_MANAGEMENT = "player_management"
    SERVER_INFO = "server_info"
    WORLD_MANAGEMENT = "world_management"
    OTHER = "other"


class CommandValidator:
    """Валидатор команд Minecraft"""

    ALLOWED_COMMANDS = {
        "stop": CommandType.SERVER_MANAGEMENT,
        "restart": CommandType.SERVER_MANAGEMENT,
        "save-all": CommandType.SERVER_MANAGEMENT,
        "list": CommandType.SERVER_INFO,
        "say": CommandType.OTHER,
        "time": CommandType.WORLD_MANAGEMENT,
        "weather": CommandType.WORLD_MANAGEMENT,
        "gamemode": CommandType.PLAYER_MANAGEMENT,
        "kick": CommandType.PLAYER_MANAGEMENT,
        "ban": CommandType.PLAYER_MANAGEMENT,
    }

    DANGEROUS_COMMANDS = {"stop", "restart", "ban", "kick", "op", "deop"}

    def validate_command(self, raw_command: str) -> Tuple[bool, str, Optional[str]]:
        """Валидация команды"""
        if not raw_command or not raw_command.strip():
            return False, "", "Команда не может быть пустой"

        command = raw_command.strip().lower()
        parts = command.split()

        if not parts:
            return False, "", "Неверный формат команды"

        base_command = parts[0]

        if base_command not in self.ALLOWED_COMMANDS:
            return False, command, f"Команда '{base_command}' не разрешена"

        return True, command, None

    def is_dangerous_command(self, command: str) -> bool:
        """Проверяет, является ли команда опасной"""
        base_command = command.split()[0] if command else ""
        return base_command in self.DANGEROUS_COMMANDS

    def get_command_type(self, command: str) -> Optional[CommandType]:
        """Возвращает тип команды"""
        base_command = command.split()[0] if command else ""
        return self.ALLOWED_COMMANDS.get(base_command)