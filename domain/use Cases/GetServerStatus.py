class GetServerStatus:
    def __init__(self, rcon_client):
        self.rcon_client = rcon_client

    def execute(self):
        success, result = self.rcon_client.send_command("list")
        if success:
            return result
        else:
            return "Ошибка при получении статуса."
