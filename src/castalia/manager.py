from pathlib import Path
import shutil
import toml
from rich.console import Console
from castalia import config, db, library, parser, selector
from castalia.parser import SimilarityGames
from rich import print
from rich.markup import escape

console = Console()
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

def get_library_location(config_directory: Path) -> Path:
    library = Path("~/Roms").expanduser().resolve()
    with open(config_directory / "config.toml", 'r') as f:
        config_file = toml.load(f)

    library = Path(config_file['library']['path']).expanduser().resolve()
    return library



def import_file(path: Path, platform: str, recursive: bool = False):
    config_directory = config.find_castalia_dir()
    platforms_location = config_directory / "platforms.toml"
    platform_id = get_platform_id(platform, platforms_location)
    client_id, bearer_token = get_authentication_stuff(config_directory)
    library_root = get_library_location(config_directory)


    valid_extensions = get_system_extensions(platforms_location, platform)
    valid_roms = extract_valid_list_of_roms(path, valid_extensions, recursive)

    valid_roms.sort()

    for rom in valid_roms:
        selected_title, filename = process_file(rom, platform_id, valid_extensions, client_id, bearer_token)
        extension = Path(filename).suffix
        if selected_title:
            platform_directory = library_root / platform
            library.create_directory_if_missing(platform_directory)
            final_name = selected_title["name"] + extension

            moved_location = platform_directory / final_name
            if moved_location.exists():
                print(f"[bold red]File '{escape(str(moved_location))}' already exists. Skipping[/bold red]")
            else: 
                shutil.move(rom, moved_location)



def process_file(directory: Path, platform_id: int,
                 valid_extensions: list[str], client_id: str, bearer_token: str):
    file = directory.name

    with console.status(f"[bold cyan]Searching IGDB for [white]{escape(file)}[/white]...", spinner="dots"):
        search_results = parser.search_game(file, valid_extensions, platform_id, client_id, bearer_token)
    diffed_titles = parser.compare_titles(file, valid_extensions, search_results)
    if diffed_titles:
        selected_title = selector.list_options(diffed_titles, str(file))
    else:
        print(f"[bold red]No Matches found for 'escape({file})'. Skipping[/bold red]")
        selected_title = None


    return selected_title, file

def main():
    rom_directory = Path("~/roms/psp/").expanduser().resolve()
    import_file(rom_directory, "psp", True)





if __name__ == "__main__":
    main()
