from dataclasses import dataclass

@dataclass(frozen=True)
class RconCredentials:
    host: str
    port: int
    password: str
