from pathlib import Path
from rich import print
from rich.markup import escape
from castalia.errors import LibraryError, CastaliaError


def create_directory_if_missing(directory_location: Path) -> None:
    try:
        directory_location.mkdir(parents=True, exist_ok=True)
    except FileExistsError as e:
        raise LibraryError(
            f"{directory_location} exists but is a file, not a directory"
        ) from e
    except OSError as e:
        raise LibraryError(f"Cannot create {directory_location}: {e.strerror}") from e

def directory_builder(library_root: str, platform: str, file_name: str | None = None) -> Path:
    if file_name is not None:
        return Path(library_root).expanduser() / platform / file_name
    return Path(library_root).expanduser() / platform

def main():
    library = "~/Roms/"
    platform = "psx"
    newDir = directory_builder(library, platform)
    #This is just for testeing, i know that i should seperate roms and directories in the future more cleanly structurally
    try:
        create_directory_if_missing(newDir)
    except CastaliaError as e:
        print(f"[italic red]Error: {escape(str(e))}[/italic red]")
        raise SystemExit(1)
    print (newDir)

if __name__ == "__main__":
    main()
