from ftplib import error_reply
import sys
import time
from difflib import SequenceMatcher
import requests
from typing import TypedDict
from castalia.filename_variants import analyze, comparison_title
from rich import print

gamesURL = "https://api.igdb.com/v4/games"

class IGDBError(Exception):
    """Base class for all IGDB problems."""

class IGDBFatalError(IGDBError):
    """Pointless to continue: offline, bad token, rate limited."""

class IGDBRequestError(IGDBError):
    """Only this one request failed (e.g. a 500)."""

class IGDBGame(TypedDict):
    id: int
    name: str

class SimilarityGames(TypedDict):
    id: int
    name: str
    percentage_similarity: str 
    similarity: float

def search_game(rom_title: str, extensions: list[str], platform_id: int,
                client_id: str, bearer_token: str) -> list[IGDBGame]:
    bearer_token = f"Bearer {bearer_token}"
    authentication = {'Client-ID': client_id, 'Authorization': bearer_token}
    analysis = analyze(rom_title, extensions)
    output = {}
    for game in analysis.candidates:
        body = f"search \"{game}\"; fields name, id; where platforms = ({platform_id});"
        try:
            search = requests.post(gamesURL, headers=authentication, data=body, timeout=10)
            search.raise_for_status()
        except requests.exceptions.Timeout as err:
            raise IGDBFatalError("Connection timeout") from err
        except requests.exceptions.ConnectionError as err:
            raise IGDBFatalError("Connection error. Are you online? Is IGDB accessible through a browser?")
        except requests.exceptions.HTTPError as err:
            status = err.response.status_code if err.response is not None else None
            match status:
                case 401:
                    raise IGDBFatalError("Token expired or/and invalid. Try regenerating") from err
                case 429:
                    raise IGDBFatalError("Too many requests") from err
                case _:
                    raise IGDBRequestError(f"Miscellaneous error code: {status}")
        data: list[IGDBGame] = search.json()
        for game in data:
            output[game["id"]] = game
        time.sleep(0.26)
    return list(output.values())


def compare_titles(rom_title: str, extensions: list[str], fetched_names: list[IGDBGame]) -> list[SimilarityGames]:
    cleaned_rom_title = comparison_title(rom_title, extensions)
    cleaned_rom_title = normalize_title(cleaned_rom_title)
    diffed_games: list[SimilarityGames] = []
    for game in fetched_names:
        similarity = SequenceMatcher(None, cleaned_rom_title.casefold(), game["name"].casefold()).ratio()
        percentage_similarity = f"{round(similarity * 100, 2)}%"
        diffed_games.append({
            "name": game["name"],
            "percentage_similarity": percentage_similarity,
            "similarity": similarity,
            "id": game["id"]
            })
    diffed_games.sort(key=lambda game: game["similarity"], reverse=True)
    return diffed_games

def normalize_title(title: str) -> str:
    title = title.strip()

    articles = ("the", "a", "an", "The", "A", "An")

    for article in articles:
        suffix = f", {article}"
        if title.endswith(suffix):
            title = f"{article} {title[:-len(suffix)]}"
            break

    return title


def main():
    client_id = sys.argv[1]
    bearer_token = sys.argv[2]
    rom_name = "Legend of Zelda, The (USA).zip"
    rom_platform = 19
    searched_games = search_game(rom_name, [".zip"], rom_platform, client_id, bearer_token )
    diffed_titles = compare_titles(rom_name, [".zip"], searched_games)
    for title in diffed_titles:
        print(f"[ {title["percentage_similarity"]} ]: {title["name"]}")

if __name__ == "__main__":
    main()



