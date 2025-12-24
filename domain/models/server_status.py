from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ServerStatus:
    """наш класс для Модель статуса сервера Minecraft"""
    is_online: bool
    player_count: int
    max_players: int
    tps: float
    memory_used_mb: int
    memory_total_mb: int
    uptime_seconds: int
    last_checked: datetime
    def __post_init__(self):
        """Валидация после создания объекта"""
        if self.player_count < 0:
            raise ValueError("Количество игроков не может быть отрицательным")
        if self.tps < 0:
            raise ValueError("TPS не может быть отрицательным")

    @property
    def player_ratio(self) -> float:
        """сколька чувачков сейчас на сервере(процент заполнености)"""
        if self.max_players == 0:
            return 0.0
        return (self.player_count / self.max_players) * 100

    @property
    def uptime_hours(self) -> float:
        """Аптайм перевели в часы"""
        return self.uptime_seconds / 3600