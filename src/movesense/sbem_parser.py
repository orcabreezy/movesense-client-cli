import sys
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class SbemChunk:
    id: int
    len: int
    content: bytes

    def __str__(self) -> str:
        return f"({self.id}, {self.len})"


@dataclass
class DataEntry:
    timestamp: int
    value: Any


@dataclass
class DataChunk:
    timestamp: int
    values: list[Any]
    interval: int | None = None

    def to_data_entries(self) -> list[DataEntry]:
        if self.interval is None:
            raise Exception("cannot convert to entries without interval knowledge")

        return [
            DataEntry(self.timestamp + i * self.interval, self.values[i])
            for i in range(len(self.values))
        ]


@dataclass
class SbemChunkType:
    id: int
    structure_parser: Callable[[bytes], DataChunk]
    csv_header: str


def read_bin_file(name) -> bytes:
    with open(name, "rb") as file:
        return file.read()


def check_sbem_header(file: bytes) -> bool:
    return file[0:8] == b"SBEM0112"


def parse_sbem(file: bytes):
    file = file[8:]

    chunks: list[SbemChunk] = []

    while len(file) >= 2:
        chunk_id = int(file[0])
        chunk_len = int(file[1])
        chunk_content = file[2:chunk_len]
        chunks.append(SbemChunk(chunk_id, chunk_len, chunk_content))
        file = file[(chunk_len + 2) :]

    return chunks


def write_to_csv(filename: str, content: list[DataEntry], header: str):
    with open(filename, "w") as file:
        file.write(f"{header}\n")
        for c in content:
            file.write(f"{c.timestamp}, {c.value}\n")


ecg_chunk = SbemChunkType(
    id=104,
    structure_parser=lambda b: DataChunk(
        timestamp=int.from_bytes(b[:8], "little") // 1000,
        values=[
            int.from_bytes((b + 256 * a).to_bytes(2), "little", signed=True)
            for a, b in zip(b[8::2], b[9::2])
        ],
    ),
    csv_header="timestamp, ecg",
)

imu_chunk = SbemChunkType(
    id=105,  # TODO: check this !
    structure_parser=lambda b: DataChunk(
        timestamp=int.from_bytes(b[0:8], "little"),
        values=(
            lambda vecs: [
                (acc, gyr, mag)
                for acc, gyr, mag in zip(vecs[::3], vecs[1::3], vecs[2::3])
            ]
        )(
            (
                lambda int16s: [
                    (x, y, z)
                    for x, y, z in zip(int16s[::3], int16s[1::3], int16s[2::3])
                ]
            )(
                [
                    int.from_bytes((a + 256 * b).to_bytes(2), "little", signed=True)
                    for a, b in zip(b[8::2], b[9::2])
                ]
            )
        ),
    ),
    csv_header="timestamp, acc-x, acc-y, acc-z, gyr-x, gyr-y, gyr-z, mag-x, mag-x, mag-z",
)

known_chunk_types = [ecg_chunk, imu_chunk]
known_chunk_ids = {chunk_type.id: chunk_type for chunk_type in known_chunk_types}


def parse_chunks(chunks: list[SbemChunk]) -> dict[int, list[DataChunk]]:
    datachunks = {i: [] for i in known_chunk_ids}
    for chunk in chunks:
        if chunk.id not in known_chunk_ids:
            continue
        parser = known_chunk_types[
            list(known_chunk_ids).index(chunk.id)
        ].structure_parser
        datachunks[chunk.id].append(parser(chunk.content))

    return datachunks


if __name__ == "__main__":
    filename = sys.argv[1]
    if ".bin" != filename[-4:]:
        raise Exception(f'file type has to be ".bin" for {filename}')

    file_contents = read_bin_file(filename)

    if not check_sbem_header(file_contents):
        raise Exception("file header does not match SBEM0112")

    chunks = parse_sbem(file_contents)
    # for chunk in filter(lambda sc: sc.id in [ct.id for ct in known_chunk_types], chunks):
    data_chunks = parse_chunks(chunks)
    for id in data_chunks:
        chunks_for_id = data_chunks[id]
        if len(chunks_for_id) < 2:
            continue
        # Not accounting for hot interval changes
        interval: int = chunks_for_id[1].timestamp - chunks_for_id[0].timestamp
        for chunk in chunks_for_id:
            chunk.interval = interval

    flat_entries = {id: [] for id in data_chunks}
    for id in data_chunks:
        # convert to flat list
        for chunks in data_chunks[id]:
            flat_entries[id] += chunks.to_data_entries()

    # import matplotlib.pyplot as plt

    # fig, ax = plt.subplots()
    # ax.plot([entry.value for entry in flat_entries[104]])
    # plt.show()

    output_filename = f"{filename[:-4]}.csv"
    write_to_csv(output_filename, flat_entries[104], "timestamp, value")
