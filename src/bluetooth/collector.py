from dataclasses import dataclass
from typing import Callable

import bleak

from src.common.file_io import write_to_file
from src.movesense.data_chunk import DataChunk, add_interval_if_known


@dataclass
class BluetoothDataCollector:
    device: bleak.BleakClient
    char_uuid: str
    deserializer: Callable[[bytes], DataChunk]
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

        def _emergency_save():
            print("device disconnected, emergency saved file")

            write_to_file(self._contents_to_file(), "csv", "data", name=self.char_uuid)

        self.calls_on_disconnect.append(_emergency_save)

    def _contents_to_file(self) -> str:
        chunks = [self.deserializer(packet) for packet in self.packets]
        chunks = add_interval_if_known(chunks)
        output = self.header + ""
        output += "".join(c.to_csv_chunk() for c in chunks)
        return output

    async def finish(self) -> str:
        await self.device.stop_notify(self.char_uuid)
        self.is_running = False
        return self._contents_to_file()
