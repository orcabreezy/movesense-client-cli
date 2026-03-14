import bleak


class MovesenseClient:
    def __init__(self, device: bleak.BleakClient):
        self.device = device

    async def connect(self) -> bool:
        try:
            await self.device.connect()
            return True
        except Exception:  # Catch specific exceptions here
            return False

    async def disconnect(self) -> bool:
        try:
            await self.device.disconnect()
            return True
        except Exception:  # Catch specific exceptions here
            return False
