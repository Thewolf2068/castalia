import pytest
from castalia.parser import *
from castalia.filename_variants import comparison_title



@pytest.fixture
def rom_game_cases():
    return [
        {
            "filename": "Legend of Zelda, The (USA).sfc",
            "extensions": [".sfc", ".smc"],
            "expected_game": "The Legend of Zelda SNES",
        },
        {
            "filename": "Super Mario World (USA).sfc",
            "extensions": [".sfc", ".smc"],
            "expected_game": "Super Mario World",
        },
        {
            "filename": "Sonic The Hedgehog (Europe).md",
            "extensions": [".md", ".gen"],
            "expected_game": "Sonic the Hedgehog",
        },
    ]
@pytest.mark.parametrize(
    ("filename", "extensions", "expected"),
    [
        ("Legend of Zelda, The (USA).sfc", [".sfc"], "The Legend of Zelda"),
        ("Super Mario World (USA).sfc", [".sfc"], "Super Mario World"),
        ("Sonic The Hedgehog (Europe).md", [".md"], "Sonic The Hedgehog"),
    ],
)

def test_comparison_title(filename: str, extensions: list[str], expected: str):
    result = comparison_title(filename, extensions)
    result = normalize_title(result)
    assert result == expected
