import datetime
import os


def get_timestamp_string() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def write_to_file(
    file_content: str, extension: str, subfolder: str, name: str = ""
) -> None:
    if not name:
        name = get_timestamp_string()
    else:
        name = f"{name}_{get_timestamp_string()}"

    # Ensure the subfolder exists
    os.makedirs(subfolder, exist_ok=True)

    file_path = os.path.join(subfolder, f"{name}.{extension}")
    with open(file_path, "w") as file:
        file.write(file_content)


def write_to_file_binary(
    file_content: list[bytearray], extension: str, subfolder: str, name: str = ""
) -> str:
    if not name:
        name = get_timestamp_string()

    # Ensure the subfolder exists
    os.makedirs(subfolder, exist_ok=True)

    file_path = os.path.join(subfolder, f"{name}.{extension}")
    with open(file_path, "wb") as file:
        for b in file_content:
            file.write(b)

    return file_path
