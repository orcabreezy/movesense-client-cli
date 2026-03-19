from dataclasses import dataclass
from typing import Any


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

        # use timestamp only if it is known
        return [
            DataEntry(
                self.timestamp + i * self.interval,
                self.values[i],
            )
            for i in range(len(self.values))
        ]

    def set_interval(self, interval: int):
        self.interval = interval

    def to_csv_chunk(self) -> str:
        return "\n" + "\n".join(
            f"{entry.timestamp}, {entry.value}" for entry in self.to_data_entries()
        )


def add_interval_if_known(chunks: list[DataChunk]) -> list[DataChunk]:
    if len(chunks) < 2:
        return chunks
    interval = (chunks[1].timestamp - chunks[0].timestamp) // len(chunks[1].values)
    for chunk in chunks:
        chunk.set_interval(interval)
    return chunks
