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
    return list(filter(lambda svc: svc.uuid == uuid, dev.services))[0]


def get_char_by_uuid(svc, uuid):
    return list(filter(lambda char: char.uuid == uuid, svc.characteristics))[0]
