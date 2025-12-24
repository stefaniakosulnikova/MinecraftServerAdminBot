from infrastructure.adapters.rcon_client import RconClientAdapter
from loggers.app_logger import MinecraftBotLogger

class ExecuteCommand:
    def __init__(self, rcon_client, logger: MinecraftBotLogger):
        self.rcon_client = rcon_client
        self.logger = logger

    async def execute(self, *, user_id: int, creds, command: str):
        if isinstance(creds, RconClientAdapter):
            success, message = await creds.send_command(command)
        else:
            # Создаем клиент на лету
            host, port, password = creds
            client = RconClientAdapter(host, port, password)
            success, message = await client.send_command(command)

        self.logger.log_command(command, user_id, success)
        return success, message
