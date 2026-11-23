from pathlib import Path
import toml


def get_platform_id(platform: str, platforms_location: Path) -> int:
    with open(platforms_location, 'r') as f:
        platforms = toml.load(f)

    if platforms["platforms"][platform]["igdb"] is not None:
        return platforms["platforms"][platform]["igdb"]
    return 0


def get_system_extensions(platforms_location: Path, platform: str) -> list[str]:
    output: list[str] = []
    with open(platforms_location, 'r') as f:
        platforms = toml.load(f)
    for extensions in platforms["platforms"][platform]["extensions"]:
        output.append(extensions)
    return output
