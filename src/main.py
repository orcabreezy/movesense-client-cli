import asyncio
from calendar import c
from pathlib import UnsupportedOperation
from sqlite3 import Binary

import bleak
from bleak.assigned_numbers import CharacteristicPropertyName
from bleak.exc import BleakCharacteristicNotFoundError

from src.movesense import sbem_parser

from .bluetooth.collector import BluetoothDataCollector
from .cli.menu import AsyncMenu, Menu
from .common.definitions import (
    ACTIVITY_SVC_UUID_128,
    ECG_INTERVALS,
    HR_SVC_UUID_128,
    IMU_INTERVALS,
    MovesenseV7,
    MovesenseV8,
)
from .common.file_io import write_to_file, write_to_file_binary
from .common.utils import (
    BinaryAggregator,
    get_char_by_uuid,
    get_svc_by_uuid,
    parse_uint16,
)
from .movesense.client import MovesenseClient
from .movesense.config import MovesenseConfigField
from .movesense.protocol import (
    deserialize_ecg7_packet,
    deserialize_ecg8_packet,
    deserialize_imu7_packet,
    deserialize_imu8_packet,
    ecg_header_string,
    imu_header_string,
)

# TODO assignment routine
# TODO async func return routine


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
    activity_service = get_svc_by_uuid(device, ACTIVITY_SVC_UUID_128)
    if not activity_service:
        return None

    characteristics = activity_service.characteristics
    if not characteristics:
        return None

    if characteristics[0].uuid == MovesenseV7.ECG_VOLTAGE_UUID_128:
        return 7

    if characteristics[0].uuid == MovesenseV8.ECG_VOLTAGE_UUID_128:
        return 8
    return None


async def movesense_control_menu_v8(
    device: bleak.BleakClient, calls_on_disconnect=[]
) -> AsyncMenu | str:
    activity_service = get_svc_by_uuid(device, ACTIVITY_SVC_UUID_128)
    if not activity_service:
        return "Error: Activity service not found for v8 device."
    hr_service = get_svc_by_uuid(
        device, HR_SVC_UUID_128
    )  # This one is not used in v8 menu, so can be None

    ecg_voltage = get_char_by_uuid(activity_service, MovesenseV8.ECG_VOLTAGE_UUID_128)
    if not ecg_voltage:
        return "Error: ECG voltage characteristic not found for v8 device."
    imu_meas = get_char_by_uuid(activity_service, MovesenseV8.IMU_MEAS_UUID_128)
    if not imu_meas:
        return "Error: IMU measurement characteristic not found for v8 device."
    configuration = get_char_by_uuid(activity_service, MovesenseV8.CONFIG_UUID_128)
    if not configuration:
        return "Error: Configuration characteristic not found for v8 device."
    recorded_data = get_char_by_uuid(activity_service, MovesenseV8.RECORDED_UUID_128)
    if not recorded_data:
        return "Error: Recorded data characteristic not found for v8 device."

    async def start_datatransfer():

        async def consume_recorded_data(_, binstring):
            binary_data.append(binstring)

        await device.start_notify(recorded_data, callback=consume_recorded_data)
        binary_data = []
        await config_field.transfer_data_now()
        while True:
            await asyncio.sleep(0.5)
            await config_field.initialize()
            if not config_field.transfer_operation:
                break
            # TODO Time indicator
        file = write_to_file_binary(binary_data, extension="bin", subfolder="data")
        await device.stop_notify(recorded_data)
        try:
            sbem_parser.parse_sbem_file(file)
        except Exception as e:
            print(f"Error parsing SBEM file: {e}")

    config_field = MovesenseConfigField(device, configuration.uuid)
    await config_field.initialize()

    ecg_writer = BluetoothDataCollector(
        device=device,
        char_uuid=ecg_voltage.uuid,
        deserializer=deserialize_ecg8_packet,
        header=ecg_header_string,
        calls_on_disconnect=calls_on_disconnect,
    )
    imu_writer = BluetoothDataCollector(
        device=device,
        char_uuid=imu_meas.uuid,
        deserializer=deserialize_imu8_packet,
        header=imu_header_string,
        calls_on_disconnect=calls_on_disconnect,
    )

    async def config_printer() -> str:
        return str(config_field)

    async def set_intervals() -> AsyncMenu:
        def update_ecg(interval):
            async def update_func():
                await config_field.update_intervals(ecg_interval=interval)

            return update_func

        def update_imu(interval):
            async def update_func():
                await config_field.update_intervals(imu_interval=interval)

            return update_func

        return AsyncMenu(
            name="choose sensor type",
            actions={
                "0 ecg": lambda: AsyncMenu(
                    name="ecg interval",
                    actions={
                        str(interval): update_ecg(interval)
                        for interval in ECG_INTERVALS
                    },
                    is_single=True,
                ),
                "1 imu": lambda: AsyncMenu(
                    name="imu interval",
                    actions={
                        str(interval): update_imu(interval)
                        for interval in IMU_INTERVALS
                    },
                ),
            },
            is_single=True,
        )

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
            "u intervals": set_intervals,
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


async def movesense_control_menu_v7(device: bleak.BleakClient) -> AsyncMenu | str:
    activity_service = get_svc_by_uuid(device, ACTIVITY_SVC_UUID_128)
    if not activity_service:
        return "Error: Activity service not found for v7 device."
    hr_service = get_svc_by_uuid(device, HR_SVC_UUID_128)  # Not used in v7 menu

    ecg_voltage = get_char_by_uuid(activity_service, MovesenseV7.ECG_VOLTAGE_UUID_128)
    if not ecg_voltage:
        return "Error: ECG voltage characteristic not found for v7 device."
    imu_meas = get_char_by_uuid(activity_service, MovesenseV7.IMU_MEAS_UUID_128)
    if not imu_meas:
        return "Error: IMU measurement characteristic not found for v7 device."
    ecg_interval = get_char_by_uuid(activity_service, MovesenseV7.ECG_INTERVAL_UUID_128)
    if not ecg_interval:
        return "Error: ECG interval characteristic not found for v7 device."
    imu_interval = get_char_by_uuid(activity_service, MovesenseV7.IMU_INTERVAL_UUID_128)
    if not imu_interval:
        return "Error: IMU interval characteristic not found for v7 device."

    ecg_writer = BluetoothDataCollector(
        device=device,
        char_uuid=ecg_voltage.uuid,
        deserializer=deserialize_ecg7_packet,
        header=ecg_header_string,
        calls_on_disconnect=calls_on_disconnect,
    )
    imu_writer = BluetoothDataCollector(
        device=device,
        char_uuid=imu_meas.uuid,
        deserializer=deserialize_imu7_packet,
        header=imu_header_string,
        calls_on_disconnect=calls_on_disconnect,
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
                        action_string=f"available values: {ECG_INTERVALS}",
                        actions={
                            str(i): lambda: device.write_gatt_char(
                                ecg_interval, i.to_bytes(2, "little")
                            )
                            for i in ECG_INTERVALS
                        },
                        is_single=True,
                    ),
                    "1 imu": lambda: AsyncMenu(
                        name="select new imu interval",
                        action_string=f"available values: {IMU_INTERVALS}",
                        actions={
                            str(i): lambda: device.write_gatt_char(
                                imu_interval, i.to_bytes(2, "little")
                            )
                            for i in IMU_INTERVALS
                        },
                        is_single=True,
                    ),
                },
                is_single=True,
            ),
        },
    )


async def choose_device_menu(devices: list) -> int | None:
    if len(devices) == 0:
        print("discovered no devices")
        return None

    idx = None

    def index_setter(i):
        nonlocal idx

        def function():
            nonlocal idx
            idx = i

        # dafuq?
        return function

    actions = {str(i): index_setter(i) for i in range(len(devices))}
    actions.update({"r": index_setter(-1)})

    await AsyncMenu(
        name="choose device",
        actions=actions,
        action_string="\n"
        + "\n".join(f"({i}) {devices[i].name}" for i in range(len(devices)))
        + "\n(r)escan"
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


async def main_async() -> None:
    # Scanning and connection process
    subscriptionManagement = {}
    calls_on_sudden_disconnect = []

    # callback, that goes through all registered callbacks
    # in 'calls_on_sudden_disconnect'
    def on_disconnect(device: bleak.BleakClient):
        for f in calls_on_sudden_disconnect:
            f()

    while True:
        devices = [dev for dev in await ble_scan(2)]
        if devices is None:
            print("error: no scan results")
            return
        dev_id = await choose_device_menu(devices)

        if dev_id is None:
            print("quitting app")
            return
        elif dev_id < 0:
            continue
        else:
            break

    device = bleak.BleakClient(devices[dev_id], disconnected_callback=on_disconnect)
    client = MovesenseClient(device)

    print(f"connecting to {device.name} which was {devices[dev_id]}")
    if not await client.connect():
        print(f"error connecting to {device.name}")
        return

    # Device Interaction
    async def choose_movesense_menu():
        firmwave_version = get_movesense_firmware_version(client.device)
        if firmwave_version == 8:
            return await movesense_control_menu_v8(
                client.device, calls_on_sudden_disconnect
            )
        elif firmwave_version == 7:
            return await movesense_control_menu_v7(client.device)

        return f"device is not Movesense, fv: {firmwave_version}"

    async def service_action():
        def characteristic_menu(service):
            characteristics = service.characteristics

            def action_menu(char):
                def return_function():
                    # TODO: add checks if chars support properties at all
                    async def read() -> str:
                        result = await device.read_gatt_char(char)
                        # TODO as hex
                        return f"{result} with len {len(result)}"

                    async def write(bin_string) -> str:
                        binary = bytes.fromhex(bin_string)
                        await device.write_gatt_char(char, binary)
                        return f"wrote value {bin_string} with len {len(binary)}"

                    async def subscribe():
                        if char.uuid in subscriptionManagement.keys():
                            return "Already subscribed"

                        data_aggregator = BinaryAggregator()
                        subscriptionManagement[char.uuid] = data_aggregator

                        await device.start_notify(
                            char, lambda _, data: data_aggregator.aggregate(data)
                        )

                        return "Subscribed now"

                    async def unsubscribe():
                        if char.uuid not in subscriptionManagement.keys():
                            return "Not subscribed yet"

                        await device.stop_notify(char)
                        data_aggregator: BinaryAggregator = subscriptionManagement.pop(
                            char.uuid
                        )
                        return (
                            "finished data aggregation, aggregated "
                            + str(len(data_aggregator.data))
                            + " bytes: "
                            + str(data_aggregator.data)
                        )

                    return AsyncMenu(
                        name=f"Action Menu for {char.uuid}",
                        action_string="\n"
                        + "\n(r)ead"
                        + "\n(w)rite: arg"
                        + "\n(s)usbscribe"
                        + "\n(u)nsubscribe",
                        actions={
                            "read": read,
                            "write": write,
                            "subscribe": subscribe,
                            "unsubscribe": unsubscribe,
                        },
                    )

                return return_function

            async def return_function():
                return AsyncMenu(
                    name=f"Characteristic Menu for {service.uuid}",
                    action_string="\n"
                    + "\n".join(
                        f"({i}) {characteristics[i].uuid}"
                        for i in range(len(characteristics))
                    ),
                    actions={
                        str(i) + str(characteristics[i].uuid): action_menu(
                            characteristics[i]
                        )
                        for i in range(len(characteristics))
                    },
                )

            return return_function

        return AsyncMenu(
            name="Service Action Menu",
            action_string="\n"
            + "\n".join(
                f"({i}) {list(device.services)[i].uuid}"
                for i in range(len(list(device.services)))
            ),
            actions={
                str(i): characteristic_menu(list(device.services)[i])
                for i in range(len(list(device.services)))
            },
        )

    await AsyncMenu(
        name=f"{device.name}",
        actions={
            "list device attributes": lambda: list_device_services(client.device),
            "movesense control": choose_movesense_menu,
            "service action": service_action,
        },
    ).loop()

    print(f"disconnecting from {device.name}")
    # clear calls, as the following disconnect is not accidental
    calls_on_sudden_disconnect.clear()
    if not await client.disconnect():
        print(f"error disconneting from {device.name}, terminating now")

    print("disconnect successful - program finished")
    return


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
