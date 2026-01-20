import os

import bleak.uuids


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
