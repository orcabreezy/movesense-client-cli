from dataclasses import dataclass
from typing import Callable

import bleak

from src.common.file_io import write_to_file
from src.common.utils import async_print


@dataclass
class BluetoothDataCollector:
    device: bleak.BleakClient
    char_uuid: str
    deserializer: Callable[[bytes], str]
    header: str
    calls_on_disconnect: list[Callable]
    # Accicentally visible as argument
    is_running: bool = False

    async def start(self):
        self.packets = []
        self.is_running = True
        await self.device.start_notify(
            self.char_uuid, lambda _, bytes: self.packets.append(bytes)
        )

        def emergency_save():
            print("device disconnected, emergency saved file")

            output = self.header + ""
            output += "".join(self.deserializer(packet) for packet in self.packets)
            write_to_file(output, "csv", "data")

        self.calls_on_disconnect.append(emergency_save)

    async def finish(self) -> str:
        await self.device.stop_notify(self.char_uuid)
        output = self.header + ""
        output += "".join(self.deserializer(packet) for packet in self.packets)

        self.is_running = False
        return output
