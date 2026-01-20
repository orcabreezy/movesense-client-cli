import time
from dataclasses import dataclass

from bleak import BleakClient


class MovesenseConfigField:
    def __init__(self, device: BleakClient, char_uuid):
        self.ecg_interval = 2
        self.imu_interval = 10
        self.ecg_recording_mode = False
        self.imu_recording_mode = False
        self.recording_state = False
        self.transfer_operation = False
        self.delete_operation = False

        self.device = device
        self.char = char_uuid
        self.synched_time = 0

    async def initialize(self):
        bytes: bytearray = await self.device.read_gatt_char(self.char)

        self.ecg_interval = bytes[0]
        self.imu_interval = bool(bytes[1])
        self.ecg_recording_mode = bool(bytes[2])
        self.imu_recording_mode = bool(bytes[3])
        self.recording_state = bool(bytes[4])
        self.transfer_operation = bool(bytes[5])
        self.delete_operation = bool(bytes[6])
        self.synched_time = int.from_bytes(bytes[7:], "little")

    async def _compare_check(self) -> None:
        bytes: bytearray = await self.device.read_gatt_char(self.char)

        error_vector = [
            self.ecg_interval == bytes[0],
            self.imu_interval == bool(bytes[1]),
            self.ecg_recording_mode == bool(bytes[2]),
            self.imu_recording_mode == bool(bytes[3]),
            self.recording_state == bool(bytes[4]),
            self.transfer_operation == bool(bytes[5]),
            self.delete_operation == bool(bytes[6]),
            self.synched_time == int.from_bytes(bytes[7:], "little"),
        ]
        if False in error_vector:
            raise AssertionError(
                f"compare check not successful: {error_vector}, excpected: {self.__str__()} got: {bytes}"
            )

    def __str__(self) -> str:
        return str(self._build_bytes())

    def _build_bytes(self) -> bytes:
        cfg_field = (
            self.ecg_interval.to_bytes(1)
            + self.imu_interval.to_bytes(1)
            + self.ecg_recording_mode.to_bytes(1)
            + self.imu_recording_mode.to_bytes(1)
            + self.recording_state.to_bytes(1)
            + self.transfer_operation.to_bytes(1)
            + self.delete_operation.to_bytes(1)
            + (0).to_bytes(1)
            + self.synched_time.to_bytes(8, "little")
        )

        return cfg_field

    async def _send(self):
        await self.device.write_gatt_char(self.char, self._build_bytes())
        await self._compare_check()

    def is_recording_now(self) -> bool:
        return self.recording_state

    async def update_intervals(self, ecg_interval=None, imu_interval=None):
        if ecg_interval is not None:
            self.ecg_interval = ecg_interval
        if imu_interval is not None:
            self.imu_interval = imu_interval
        await self._send()

    async def update_recording_mode(self, ecg_mode=None, imu_mode=None):
        if ecg_mode is not None:
            self.ecg_recording_mode = ecg_mode
        if imu_mode is not None:
            self.imu_recording_mode = imu_mode

        await self._send()

    async def start_recording(self):
        self.recording_state = True
        await self._send()

    async def stop_recording(self):
        self.recording_state = False
        await self._send()

    async def transfer_data_now(self):
        self.transfer_operation = True
        await self._send()
        self.transfer_operation = False

    async def delete_data_now(self):
        self.delete_operation = True
        await self._send()
        self.delete_opertaion = False

    async def synchronize_now(self):
        self.synched_time = int(time.time() * 1e6)
        await self._send()
