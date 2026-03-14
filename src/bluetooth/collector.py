
from dataclasses import dataclass
from typing import Callable

import bleak


@dataclass
class BluetoothDataCollector:
    device: bleak.BleakClient
    char_uuid: str
    deserializer: Callable[[bytes], str]
    header: str
    # Accicentally visible as argument
    is_running: bool = False

    # No Saftey regarding running state
    async def start(self):
        self.packets = []
        self.is_running = True
        await self.device.start_notify(
            self.char_uuid, lambda _, bytes: self.packets.append(bytes)
        )

    async def finish(self) -> str:
        await self.device.stop_notify(self.char_uuid)
        output = self.header + ""
        output += "".join(self.deserializer(packet) for packet in self.packets)

        self.is_running = False
        return output






