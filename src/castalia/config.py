import json
import os
import time
import tomllib
from pathlib import Path
from typing import Any

from castalia.igdb_authenticator import get_bearer_token, verify_bearer_token

ENV_VAR = "CASTALIADIR"
CONFIG_FILE = "config.toml"
KEYS_FILE = "keys.json"
EXPIRY_MARGIN = 60  # refresh the token this many seconds before it expires


def find_castalia_dir() -> Path:
    env = os.environ.get(ENV_VAR)
    if env:
        directory = Path(env).expanduser()
        if not directory.is_dir():
            raise FileNotFoundError(
                f"{ENV_VAR} points to a directory that does not exist: {directory}"
            )
        return directory

    return Path.home() / ".config" / "castalia"


def load_config(directory: Path) -> dict[str, Any]:
    config_path = directory / CONFIG_FILE
    if not config_path.is_file():
        raise FileNotFoundError(f"Could not find configuration file: {config_path}")

    with open(config_path, "rb") as f:
        return tomllib.load(f)


def load_keys(directory: Path) -> dict[str, Any]:
    try:
        with open(directory / KEYS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_keys(directory: Path, keys: dict[str, Any]) -> None:
    """Write keys.json readable only by the owner, via a temp file so a crash
    cannot leave a half-written file behind."""
    keys_path = directory / KEYS_FILE
    tmp_path = directory / (KEYS_FILE + ".tmp")

    fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(keys, f)

    os.replace(tmp_path, keys_path)


def get_token(directory: Path, config: dict[str, Any]) -> str:
    """Return a valid bearer token, fetching a new one if needed."""
    keys = load_keys(directory)
    expiration = keys.get("expiration")

    if (
        keys.get("bearer_token") is None
        or expiration is None
        or expiration <= time.time() + EXPIRY_MARGIN
    ):
        igdb = config["igdb"]
        token, expiration = get_bearer_token(igdb["client_id"], igdb["client_secret"])
        keys = {"bearer_token": token, "expiration": expiration}
        save_keys(directory, keys)

    return keys["bearer_token"]


def main() -> None:
    directory = find_castalia_dir()
    config = load_config(directory)
    token = get_token(directory, config)
    verify_bearer_token(config["igdb"]["client_id"], token)


if __name__ == "__main__":
    main()
