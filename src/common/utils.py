import asyncio
import os
import sys


async def async_print(text: str) -> None:
    loop = asyncio.get_running_loop()
    sys.stdout.write(text)
    await loop.run_in_executor(None, sys.stdout.flush)


async def async_input(prompt: str) -> str:
    await async_print(prompt)
    return (await asyncio.to_thread(sys.stdin.readline))[:-1]


def clear_screen() -> str:
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

    return ""


def parse_uint16(bytes) -> int:
    return int.from_bytes(bytes, "little")


def get_svc_by_uuid(dev: bleak.BleakClient, uuid):
    services = list(filter(lambda svc: svc.uuid == uuid, dev.services))
    if services:
        return services[0]
    return None


def get_char_by_uuid(svc, uuid):
    characteristics = list(filter(lambda char: char.uuid == uuid, svc.characteristics))
    if characteristics:
        return characteristics[0]
    return None


class BinaryAggregator:
    def __init__(self):
        self.data = []

    def aggregate(self, binary_data):
        self.data += binary_data

    def conclude(self):
        return self.data
        self.data = []
