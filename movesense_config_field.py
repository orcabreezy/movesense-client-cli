import asyncio
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
        self.synced_time = 0

    async def initialize(self):
        bytes: bytearray = await self.device.read_gatt_char(self.char)

        self.ecg_interval = int(bytes[0])
        self.imu_interval = int(bytes[1])
        self.ecg_recording_mode = bool(bytes[2])
        self.imu_recording_mode = bool(bytes[3])
        self.recording_state = bool(bytes[4])
        self.transfer_operation = bool(bytes[5])
        self.delete_operation = bool(bytes[6])
        self.synced_time = int.from_bytes(bytes[8:], "little")

    # TODO prettify
    def __str__(self) -> str:
        return str(self._build_bytes())

    def _build_bytes(self) -> bytearray:
        cfg_field = bytearray(b"\x00" * 16)
        cfg_field[0] = self.ecg_interval
        cfg_field[1] = self.imu_interval
        cfg_field[2] = self.ecg_recording_mode
        cfg_field[3] = self.imu_recording_mode
        cfg_field[4] = self.recording_state
        cfg_field[5] = self.transfer_operation
        cfg_field[6] = self.delete_operation
        cfg_field[8:] = self.synced_time.to_bytes(8, "little")

        return cfg_field

    async def _send(self):
        await self.device.write_gatt_char(self.char, data=self._build_bytes())

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
        self.synced_time = int(time.time() * 1e6)
        await self._send()
