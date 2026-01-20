import asyncio

import bleak

from data_collector import (
    BluetoothDataCollector,
    deserialize_ecg7_packet,
    deserialize_ecg8_packet,
    deserialize_imu7_packet,
    deserialize_imu8_packet,
    ecg_header_string,
    imu_header_string,
    write_to_file,
    write_to_file_binary,
)
from definitions import (
    activity_svc_uuid_128,
    config_8_uuid_128,
    ecg_interval_7_uuid_128,
    ecg_intervals,
    ecg_voltage_7_uuid_128,
    ecg_voltage_8_uuid_128,
    hr_svc_uuid_128,
    imu_interval_7_uuid_128,
    imu_intervals,
    imu_meas_7_uuid_128,
    imu_meas_8_uuid_128,
    recorded_uuid_128,
)
from menu import AsyncMenu, Menu
from movesense_config_field import MovesenseConfigField
from utils import get_char_by_uuid, get_svc_by_uuid, parse_uint16


def list_device_services(device: bleak.BleakClient) -> str:
    output = "\n"
    services = device.services

    for service in services:
        characteristics = service.characteristics
        output += f"service: {service.uuid}\n"
        output += "characteristics:\n"
        for characteristic in characteristics:
            output += f" - {characteristic.uuid} - {characteristic.properties}\n"
        output += ("-" * (len(service.uuid) + 2 + len("service"))) + "\n"

    return output


def get_movesense_firmware_version(device: bleak.BleakClient) -> int | None:
    services = device.services
    for svc in services:
        if svc.uuid != activity_svc_uuid_128:
            continue
        characteristics = svc.characteristics
        if characteristics[0].uuid == ecg_voltage_7_uuid_128:
            return 7

        if characteristics[0].uuid == ecg_voltage_8_uuid_128:
            return 8
        return None
    return None


async def movesense_control_menu_v8(device: bleak.BleakClient) -> AsyncMenu:
    activity_service = get_svc_by_uuid(device, activity_svc_uuid_128)
    hr_service = get_svc_by_uuid(device, hr_svc_uuid_128)

    ecg_voltage = get_char_by_uuid(activity_service, ecg_voltage_8_uuid_128)
    imu_meas = get_char_by_uuid(activity_service, imu_meas_8_uuid_128)
    configuration = get_char_by_uuid(activity_service, config_8_uuid_128)
    recorded_data = get_char_by_uuid(activity_service, recorded_uuid_128)

    config_field = MovesenseConfigField(device, configuration.uuid)
    await config_field.initialize()

    ecg_writer = BluetoothDataCollector(
        device=device,
        char_uuid=ecg_voltage.uuid,
        deserializer=deserialize_ecg8_packet,
        header=ecg_header_string,
    )
    imu_writer = BluetoothDataCollector(
        device=device,
        char_uuid=imu_meas.uuid,
        deserializer=deserialize_imu8_packet,
        header=imu_header_string,
    )

    async def config_printer() -> str:
        return str(config_field)

    async def sync_time():
        await config_field.synchronize_now()

    async def toggle_recording() -> str:
        if config_field.is_recording_now():
            await config_field.stop_recording()
            return "local recording stopped"

        await config_field.start_recording()
        return "local recording started"

    def config_field_updater(ecg, imu):
        async def function():
            await config_field.update_recording_mode(ecg, imu)

        return function

    def edit_recording_config():
        return AsyncMenu(
            name="configure recording mode",
            action_string="(0) nothing, (1) ecg-only, (2) imu-only, (3) both",
            actions={
                "0": config_field_updater(False, False),
                "1": config_field_updater(True, False),
                "2": config_field_updater(False, True),
                "3": config_field_updater(True, True),
            },
            is_single=True,
        )

    async def start_datatransfer():
        binary_data = []
        await device.start_notify(
            recorded_data, callback=lambda _, b: binary_data.append(b)
        )
        await config_field.transfer_data_now()

        while True:
            await asyncio.sleep(0.5)
            await config_field.initialize()
            if not config_field.transfer_operation:
                break
            # Time indicator

        write_to_file_binary(binary_data, extension="bin", subfolder="data")
        await device.stop_notify(recorded_data)

    async def delete_data():
        await config_field.delete_data_now()

    async def refresh() -> str:
        await config_field.initialize()
        return str(config_field)

    return AsyncMenu(
        name="movesense controls (v0.8.0)",
        actions={
            "get config": refresh,
            "sync time": sync_time,
            "recording toggle": toggle_recording,
            "ecg": toggle_menu_generator(ecg_writer, "ecg"),
            "imu": toggle_menu_generator(imu_writer, "imu"),
            "modify recording configuration": edit_recording_config,
            "transfer data": start_datatransfer,
            "delete data": delete_data,
        },
    )


def toggle_menu_generator(writer: BluetoothDataCollector, meas_type: str):
    async def toggle_func():
        if writer.is_running:
            csv = await writer.finish()
            return Menu(
                name=f"stopped {meas_type} recording, save to file?",
                actions={
                    "yes": lambda: write_to_file(csv, "csv", "data"),
                    "no": lambda: None,
                },
                is_single=True,
            )
        await writer.start()
        return f"started {meas_type}"

    return toggle_func


def movesense_control_menu_v7(device: bleak.BleakClient) -> AsyncMenu:
    activity_service = get_svc_by_uuid(device, activity_svc_uuid_128)
    hr_service = get_svc_by_uuid(device, hr_svc_uuid_128)

    ecg_voltage = get_char_by_uuid(activity_service, ecg_voltage_7_uuid_128)
    imu_meas = get_char_by_uuid(activity_service, imu_meas_7_uuid_128)
    ecg_interval = get_char_by_uuid(activity_service, ecg_interval_7_uuid_128)
    imu_interval = get_char_by_uuid(activity_service, imu_interval_7_uuid_128)

    ecg_writer = BluetoothDataCollector(
        device=device,
        char_uuid=ecg_voltage.uuid,
        deserializer=deserialize_ecg7_packet,
        header=ecg_header_string,
    )
    imu_writer = BluetoothDataCollector(
        device=device,
        char_uuid=imu_meas.uuid,
        deserializer=deserialize_imu7_packet,
        header=imu_header_string,
    )
    hr_writer = None

    async def print_config():
        ecg_interval_value = parse_uint16(await device.read_gatt_char(ecg_interval))
        imu_interval_value = parse_uint16(await device.read_gatt_char(imu_interval))
        return f"ecg-interval: {ecg_interval_value}, imu-interval: {imu_interval_value}"

    return AsyncMenu(
        name="movesense controls (v0.7.0)",
        action_string="(p)rint cfg, [toggle: (e)cg, (i)mu, (h)r], (u)pdate value",
        actions={
            "p": print_config,
            "e": toggle_menu_generator(ecg_writer, "ecg"),
            "i": toggle_menu_generator(imu_writer, "imu"),
            "h": lambda: "not implemented yet",
            "u": lambda: AsyncMenu(
                name="select type",
                actions={
                    "0 ecg": lambda: AsyncMenu(
                        name="select new ecg interval",
                        action_string=f"available values: {ecg_intervals}",
                        actions={
                            str(i): lambda: device.write_gatt_char(
                                ecg_interval, i.to_bytes(2, "little")
                            )
                            for i in ecg_intervals
                        },
                        is_single=True,
                    ),
                    "1 imu": lambda: AsyncMenu(
                        name="select new imu interval",
                        action_string=f"available values: {imu_intervals}",
                        actions={
                            str(i): lambda: device.write_gatt_char(
                                imu_interval, i.to_bytes(2, "little")
                            )
                            for i in imu_intervals
                        },
                        is_single=True,
                    ),
                },
                is_single=True,
            ),
        },
    )


def choose_device_menu(devices: list) -> int | None:
    if len(devices) == 0:
        print("discovered no devices")
        return None

    idx = 0

    def index_setter(i):
        nonlocal idx
        idx = i

    Menu(
        name="choose device",
        actions={str(i): lambda: index_setter(i) for i in range(len(devices))},
        action_string="\n"
        + "\n".join(f"({i}) {devices[i].name}" for i in range(len(devices)))
        + f"\n\nenter device index [0..{len(devices)}]",
        is_single=True,
    ).loop()

    return idx


async def ble_scan(scan_duration: int = 5) -> list:
    scanner = bleak.BleakScanner()
    print(f"scanning for {scan_duration} seconds")
    await scanner.start()
    await asyncio.sleep(scan_duration)
    await scanner.stop()

    return scanner.discovered_devices


async def connect_to(device: bleak.BleakClient) -> bool:
    try:
        await device.connect()
        return True
    except:
        return False


async def disconnect_from(device: bleak.BleakClient) -> bool:
    try:
        await device.disconnect()
        return True
    except:
        return False


async def main_async() -> None:
    # Scanning and connection process
    devices = await ble_scan()
    if devices is None:
        print("error: no scan results")
        return

    dev_id = choose_device_menu(devices)

    if dev_id is None:
        print("device id is invalid")
        return

    device = bleak.BleakClient(devices[dev_id])

    if device.name is None:
        print("error on reading device name")
        return

    print(f"connecting to {device.name}")
    if not await connect_to(device):
        print(f"error connecting to {device.name}")
        return

    # Device Interaction
    async def choose_movesense_menu():
        firmwave_version = get_movesense_firmware_version(device)
        if firmwave_version == 8:
            return await movesense_control_menu_v8(device)
        elif firmwave_version == 7:
            return movesense_control_menu_v7(device)

        return f"device is not Movesense, fv: {firmwave_version}"

    await AsyncMenu(
        name=f"{device.name}",
        actions={
            "list device attributes": lambda: list_device_services(device),
            "movesense control": choose_movesense_menu,
        },
    ).loop()

    print(f"disconnecting from {device.name}")
    if not await disconnect_from(device):
        print(f"error disconneting from {device.name}, terminating now")

    print("disconnect successful - program finished")
    return


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
