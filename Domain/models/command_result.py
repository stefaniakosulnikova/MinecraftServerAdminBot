from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class CommandStatus(Enum):
    """Статусы выполнения команды"""
    SUCCESS = "success"
    FAILED = "failed"
    SERVER_ERROR = "server_error"
    TIMEOUT = "timeout"
    VALIDATION_ERROR = "validation_error"



@dataclass
class CommandResult:
    "Просто храним результат команды"
    success: bool
    command: str
    message: str
    status: CommandStatus
    timestamp: datetime
