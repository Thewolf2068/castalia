from rich import print
from typing import final
from rich.prompt import Prompt
from rich.markup import escape

from castalia.parser import SimilarityGames

@final
class NextLinePrompt(Prompt):
    prompt_suffix = "\n> "

def list_options(titles: list[SimilarityGames], filename: str) -> SimilarityGames:
    i = 1
    print(f"[underline]Searched for {escape(filename)}[/underline]")
    for title in titles:
        similarity = round(title["similarity"] * 100, 2)
        if similarity >= 80:
            color = "bold green"
        elif similarity>= 50:
            color = "yellow"
        else:
            color = "bold red"
        print(f"({i})[ [{color}]{escape(title["percentage_similarity"])}[/{color}] ]: {escape(title["name"])}")
        i = i + 1
    selection = int(NextLinePrompt.ask("Select the entry")) - 1

    return titles[selection]

