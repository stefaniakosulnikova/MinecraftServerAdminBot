from Domain.logging.app_logger import AppLogger

class ExecuteCommand:
    def __init__(self, rcon_client, logger: AppLogger):
        self.rcon_client = rcon_client
        self.logger = logger

    def execute(self, *, user_id: int, creds, command: str):
        success, message = self.rcon_client.send_command(creds, command)
        self.logger.log_command(command, str(user_id), creds)

        return success, message
