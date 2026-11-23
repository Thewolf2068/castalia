from pathlib import Path
import toml
from castalia import config, db, library
from typing import TypedDict

# class rom(TypedDict):
#     path: Path

def extract_valid_list_of_roms(directory: Path, extensions: list[str], recursive: bool = False) -> list[Path]:
    output: list[Path] = []
    if recursive:
        stuff = directory.rglob("*")
    else:
        stuff = directory.iterdir()
    for file in stuff:
        if file.suffix in extensions:
            output.append(file.expanduser().resolve())
    return output

def get_system_extensions(platforms_location: Path, platform: str) -> list[str]:
    output: list[str] = []
    with open(platforms_location, 'r') as f:
        platforms = toml.load(f)
    for extensions in platforms["platforms"][platform]["extensions"]:
        output.append(extensions)

    return output

def process_file(directory: Path, platform: str):
    # This is the next thing i am doing
    return


def import_file(path: Path, platform: str, recursive: bool = False):
    config_directory = config.find_castalia_dir()
    platforms_location = config_directory / "platforms.toml"
    valid_extensions = get_system_extensions(platforms_location, platform)
    valid_roms = extract_valid_list_of_roms(path, valid_extensions, recursive)


    






def main():
    rom_directory = Path("~/roms/PSP/").expanduser().resolve()
    # extract_valid_list_of_roms(rom_directory, [".iso"], recursive=True)
    import_file(rom_directory, "psx", True)





if __name__ == "__main__":
    main()
