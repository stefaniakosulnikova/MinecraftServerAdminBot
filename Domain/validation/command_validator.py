import re
from typing import List, Tuple, Optional
from enum import Enum


class CommandType(Enum):
    """Типы команд Minecraft"""
    SERVER_MANAGEMENT = "server_management"  # stop, restart, save-all
    PLAYER_MANAGEMENT = "player_management"  # kick, ban, op, deop
    SERVER_INFO = "server_info"  # list, status
    WHITELIST = "whitelist"  # whitelist add/remove
    OTHER = "other"


class CommandValidator:
    """Валидатор команд Minecraft"""

    # Разрешенные команды с их типами
    ALLOWED_COMMANDS = {
        "stop": CommandType.SERVER_MANAGEMENT, # остановить сервер
        "restart": CommandType.SERVER_MANAGEMENT, # перезагрузить сервер
        "save-all": CommandType.SERVER_MANAGEMENT, # сохранить мир
        "kick": CommandType.PLAYER_MANAGEMENT, # кикнуть игрока
        "ban": CommandType.PLAYER_MANAGEMENT,   # забанить игрока
        "pardon": CommandType.PLAYER_MANAGEMENT, # разбанить игрока
        "op": CommandType.PLAYER_MANAGEMENT,  # дать операторские права
        "deop": CommandType.PLAYER_MANAGEMENT, # забрать операторские права
        "list": CommandType.SERVER_INFO, # список игроков
        "status": CommandType.SERVER_INFO,  # статус сервера
        "say": CommandType.OTHER, #сказать от имени сервера
    }

    # Опасные команды, требующие подтверждения
    DANGEROUS_COMMANDS = {"stop", "restart", "ban", "op", "deop"}

    # Паттерны для валидации аргументов
    PLAYER_NAME_PATTERN = r'^[a-zA-Z0-9_]{3,16}$'
    REASON_PATTERN = r'^[a-zA-Z0-9_\-\.\s]{1,100}$'

    def validate_command(self, raw_command: str) -> Tuple[bool, str, Optional[str]]:
        """
        Валидация команды

        Returns:
            Tuple[bool, str, Optional[str]]: (валидна, очищенная команда, сообщение об ошибке)
        """
        if not raw_command or not raw_command.strip():
            return False, "", "Команда не может быть пустой"

        command = raw_command.strip().lower()

        # Извлекаем базовую команду (первое слово)
        parts = command.split()
        if not parts:
            return False, "", "Неверный формат команды"

        base_command = parts[0]

        # Проверяем разрешена ли команда
        if base_command not in self.ALLOWED_COMMANDS:
            return False, command, f"Команда '{base_command}' не разрешена"

        # Валидация аргументов в зависимости от команды
        error = self._validate_arguments(base_command, parts[1:])
        if error:
            return False, command, error

        return True, command, None

    def _validate_arguments(self, command: str, args: List[str]) -> Optional[str]:
        """Валидация аргументов команды"""
        if command == "kick" and len(args) >= 1:
            if not re.match(self.PLAYER_NAME_PATTERN, args[0]):
                return f"Некорректное имя игрока: {args[0]}"
            if len(args) > 1:
                reason = " ".join(args[1:])
                if not re.match(self.REASON_PATTERN, reason):
                    return "Некорректная причина кика"

        elif command == "ban" and len(args) >= 1:
            if not re.match(self.PLAYER_NAME_PATTERN, args[0]):
                return f"Некорректное имя игрока: {args[0]}"

        elif command in ["op", "deop"] and len(args) == 1:
            if not re.match(self.PLAYER_NAME_PATTERN, args[0]):
                return f"Некорректное имя игрока: {args[0]}"

        elif command == "whitelist" and len(args) >= 2:
            if args[0] not in ["add", "remove"]:
                return f"Некорректная операция whitelist: {args[0]}"
            if not re.match(self.PLAYER_NAME_PATTERN, args[1]):
                return f"Некорректное имя игрока: {args[1]}"

        return None

    def is_dangerous_command(self, command: str) -> bool:
        """Проверяет, является ли команда опасной"""
        base_command = command.split()[0] if command else ""
        return base_command in self.DANGEROUS_COMMANDS

    def get_command_type(self, command: str) -> Optional[CommandType]:
        """Возвращает тип команды"""
        base_command = command.split()[0] if command else ""
        return self.ALLOWED_COMMANDS.get(base_command)