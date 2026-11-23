from pathlib import Path
from requests import get
import toml
from rich.console import Console
from castalia import config, db, library, parser, selector
from castalia.parser import SimilarityGames
from typing import TypedDict

console = Console()

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

def get_platform_id(platform: str, platforms_location: Path) -> int:
    with open(platforms_location, 'r') as f:
        platforms = toml.load(f)
    
    if platforms["platforms"][platform]["igdb"] is not None:
        return platforms["platforms"][platform]["igdb"]
    return 0

def get_authentication_stuff(config_directory: Path) -> tuple[str, str]:
    output: tuple[str, str] = "", ""
    with open(config_directory / "config.toml", 'r') as f:
        config_file = toml.load(f)
    
    client_id = config_file['igdb']['client_id']
    
    config_file= config.load_config(config_directory)
    bearer_token = config.get_token(config_directory, config_file)

    output = client_id, bearer_token
    return output
    
                                                              



def process_file(directory: Path, platform_id: int, config_directory: Path,
                 valid_extensions: list[str], client_id: str, bearer_token: str) -> SimilarityGames:
    file = directory.name
    
    with console.status(f"[bold cyan]Searching IGDB for [white]{file}[/white]...", spinner="dots"):
        search_results = parser.search_game(file, valid_extensions, platform_id, client_id, bearer_token)
    diffed_titles = parser.compare_titles(file, valid_extensions, search_results)
    selected_title: SimilarityGames = selector.list_options(diffed_titles, str(file))


    return selected_title
    

    
    

def import_file(path: Path, platform: str, recursive: bool = False):
    config_directory = config.find_castalia_dir()
    platforms_location = config_directory / "platforms.toml"
    valid_extensions = get_system_extensions(platforms_location, platform)

    valid_roms = extract_valid_list_of_roms(path, valid_extensions, recursive)
    platform_id = get_platform_id(platform, platforms_location)
    client_id, bearer_token = get_authentication_stuff(config_directory)

    for rom in valid_roms:
        process_file(rom, platform_id, config_directory, valid_extensions, client_id, bearer_token)

def main():
    rom_directory = Path("~/roms/PSP/").expanduser().resolve()
    import_file(rom_directory, "psp", True)





if __name__ == "__main__":
    main()
