import random
import string
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


def get_random_string(len: int = 10):
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(len))


def write_to_file(
    file_content: str, extension: str, subfolder: str, name: str = ""
) -> None:
    if name == "":
        name = get_random_string()
    name = f"./{subfolder}/{name}.{extension}"
    with open(name, "w") as file:
        file.write(file_content)


ecg_header_string = "timestamp, ecg_voltage"
imu_header_string = (
    "timestamp, acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, mag_x, mag_y, mag_z"
)


def deserialize_ecg7_packet(packet, interval=4):
    return deserialize_ecg_packet(packet, 4, interval)


def deserialize_ecg8_packet(packet, interval=4):
    return deserialize_ecg_packet(packet, 8, interval)


def deserialize_imu7_packet(packet, interval=20):
    return deserialize_imu_packet(packet, 4, interval)


def deserialize_imu8_packet(packet, interval=20):
    return deserialize_imu_packet(packet, 8, interval)


# TODO remove hard code
def deserialize_ecg_packet(
    packet: bytes, timestamp_size: int, interval: int = 4
) -> str:
    timestamp = int.from_bytes(packet[:timestamp_size], "little")
    packet = packet[timestamp_size:]
    values = []
    for i in range(16):
        values.append(int.from_bytes(packet[2 * i : 2 * i + 2], "little", signed=True))
    output = ""
    for i in range(16):
        output += f"\n{timestamp + i * interval}, {values[i]}"

    return output


# TODO remove hard code
def deserialize_imu_packet(
    packet: bytes, timestamp_size: int, interval: int = 20
) -> str:
    timestamp = int.from_bytes(packet[:timestamp_size], "little")
    packet = packet[timestamp_size:]
    values = []
    for i in range(8):

        def get_packet(base: int) -> list[int]:
            return [
                int.from_bytes(
                    packet[18 * i + base : 18 * i + base + 1], "little", signed=True
                ),
                int.from_bytes(
                    packet[18 * i + base + 2 : 18 * i + base + 3],
                    "little",
                    signed=True,
                ),
                int.from_bytes(
                    packet[18 * i + base + 4 : 18 * i + base + 5],
                    "little",
                    signed=True,
                ),
            ]

        accs = get_packet(0)
        gyrs = get_packet(6)
        mags = get_packet(12)
        combined = accs + gyrs + mags
        values.append(", ".join(str(c) for c in combined))

    output = ""
    for i in range(8):
        output += f"{timestamp + i * interval}, {values[i]}\n"

    return output
