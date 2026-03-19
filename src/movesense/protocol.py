from .data_chunk import DataChunk

ecg_header_string = "timestamp, ecg_voltage"
imu_header_string = (
    "timestamp, acc_x, acc_y, acc_z, gyr_x, gyr_y, gyr_z, mag_x, mag_y, mag_z"
)


def deserialize_ecg7_packet(packet):
    return deserialize_ecg_packet(packet, 4)


def deserialize_ecg8_packet(packet):
    return deserialize_ecg_packet(packet, 8, is_microseconds=True)


def deserialize_imu7_packet(packet):
    return deserialize_imu_packet(packet, 4)


def deserialize_imu8_packet(packet):
    return deserialize_imu_packet(packet, 8, is_microseconds=True)


# TODO remove hard code
def deserialize_ecg_packet(
    packet: bytes, timestamp_size: int, interval: int = 4, is_microseconds: bool = False
) -> DataChunk:
    timestamp = int.from_bytes(packet[:timestamp_size], "little")
    if is_microseconds:
        timestamp //= 1000

    packet = packet[timestamp_size:]
    values = []
    for i in range(16):
        values.append(int.from_bytes(packet[2 * i : 2 * i + 2], "little", signed=True))
    return DataChunk(timestamp=timestamp, values=values, interval=interval)


# TODO remove hard code
def deserialize_imu_packet(
    packet: bytes,
    timestamp_size: int,
    interval: int = 20,
    is_microseconds: bool = False,
) -> DataChunk:
    timestamp = int.from_bytes(packet[:timestamp_size], "little")
    if is_microseconds:
        timestamp //= 1000
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

    return DataChunk(timestamp=timestamp, values=values, interval=interval)
