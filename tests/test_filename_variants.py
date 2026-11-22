import pytest

from castalia.filename_variants import analyze


# (filename, primary candidate, expected extraction subset)
CASES = [
    ("Super Mario Bros. (USA).zip", "Super Mario Bros", {"regions": ["USA"]}),
    ("Super Mario Bros. (Europe).zip", "Super Mario Bros", {"regions": ["Europe"]}),
    ("Super Mario Bros. (Japan).zip", "Super Mario Bros", {"regions": ["Japan"]}),
    ("Sonic the Hedgehog (USA) (En,Fr,De).bin", "Sonic the Hedgehog", {"regions": ["USA"], "languages": ["English", "French", "German"]}),
    ("Metroid (Rev 1).nes", "Metroid", {"revision": "1"}),
    ("Zelda (v1.1).nes", "Zelda", {"revision": "1.1"}),
    ("Game (Beta).rom", "Game", {"flags": ["beta"]}),
    ("Game (Proto).rom", "Game", {"flags": ["proto"]}),
    ("Game (Demo).rom", "Game", {"flags": ["demo"]}),
    ("Game (Sample).rom", "Game", {"flags": ["sample"]}),
    ("Game (Unl).rom", "Game", {"flags": ["unlicensed"]}),
    ("Game (Alt).rom", "Game", {"flags": ["alt"]}),
    ("Game (Disc 1).iso", "Game", {"disc_number": "1"}),
    ("Game (Disc 1 of 2).iso", "Game", {"disc_number": "1", "disc_count": "2"}),
    ("Game (Track 01).bin", "Game", {"track_number": "01"}),
    ("Dr. Mario (USA).chd", "Dr. Mario", {"regions": ["USA"]}),
    ("Vol. 2 (Europe).zip", "Vol. 2", {"regions": ["Europe"]}),
    ("1942 (Japan).nes", "1942", {"regions": ["Japan"]}),
    ("Tom Clancy's Rainbow Six 3 (USA).iso", "Tom Clancy's Rainbow Six 3", {"regions": ["USA"]}),
    ("Sim City 2000 (USA).zip", "Sim City 2000", {"regions": ["USA"]}),
    ("Mr. Do! (USA).zip", "Mr. Do!", {"regions": ["USA"]}),
    ("Legend of Zelda, The (USA).nes", "The Legend of Zelda", {"regions": ["USA"]}),
    ("Man Born in Hell, A (Europe).zip", "A Man Born in Hell", {"regions": ["Europe"]}),
    ("Castlevania II - Belmont's Revenge (USA).gb", "Castlevania II: Belmont's Revenge", {"regions": ["USA"]}),
    ("Legend of Zelda, The - A Link to the Past (USA).sfc", "The Legend of Zelda: A Link to the Past", {"regions": ["USA"]}),
    ("Shin Megami Tensei - Persona 3 Portable (USA).iso", "Shin Megami Tensei: Persona 3 Portable", {"regions": ["USA"]}),
    ("Pokémon Red (USA).gb", "Pokémon Red", {"regions": ["USA"]}),
    ("Final Fantasy VII (USA).iso", "Final Fantasy VII", {"regions": ["USA"]}),
    ("Final Fantasy VIII (Europe).iso", "Final Fantasy VIII", {"regions": ["Europe"]}),
    ("Final Fantasy IV (Japan).sfc", "Final Fantasy IV", {"regions": ["Japan"]}),
    ("Tom & Jerry (USA).nes", "Tom & Jerry", {"regions": ["USA"]}),
    ("O'Brien's Adventure (USA).zip", "O'Brien's Adventure", {"regions": ["USA"]}),
    ("Game (U).zip", "Game", {"regions": ["USA"]}),  # GoodTools
    ("Game (E).zip", "Game", {"regions": ["Europe"]}),
    ("Game (J).zip", "Game", {"regions": ["Japan"]}),
    ("Game (UE).zip", "Game", {"regions": ["USA/Europe"]}),  # CONFIDENCE_LOW: combined code ordering
    ("Game (JU).zip", "Game", {"regions": ["USA/Japan"]}),
    ("Game (M3).zip", "Game", {"goodtools_codes": ["M3"]}),
    ("Game [!].zip", "Game", {"dump_flags": ["verified_good_dump"]}),
    ("Game [b1].zip", "Game", {"flags": ["bad_dump"]}),
    ("Game [h1].zip", "Game", {"flags": ["hack"]}),
    ("Game [a1].zip", "Game", {"flags": ["alt"]}),
    ("Game [f1].zip", "Game", {"dump_flags": ["fixed"]}),
    ("Game [o1].zip", "Game", {"dump_flags": ["overdump"]}),
    ("Game [T+Eng].zip", "Game", {"flags": ["fan_translation"], "translations": ["English"]}),
    ("Game [T-Ger].zip", "Game", {"flags": ["fan_translation"], "translations": ["German"]}),
    ("Game (Translated).zip", "Game", {"flags": ["fan_translation"]}),
    ("Game (Hack).zip", "Game", {"flags": ["hack"]}),
    ("Game (English Patched).zip", "Game", {"flags": ["fan_translation"]}),
    ("Game (Undub).iso", "Game", {"flags": ["undub"]}),
    ("Game [1A2B3C4D].zip", "Game", {"crc32": ["1A2B3C4D"]}),
    ("Game SLUS-00067.iso", "Game", {"serial_ids": ["SLUS-00067"]}),
    ("Game SCUS_941.63.iso", "Game", {"serial_ids": ["SCUS_941.63"]}),
    ("Game SLES-01234.iso", "Game", {"serial_ids": ["SLES-01234"]}),
    ("Sonic (1991)(Sega)(USA).zip", "Sonic", {"regions": ["USA"], "years": ["1991"]}),
    ("Game.Name.USA.PSX-GROUP.zip", "Game Name", {"regions": ["USA"]}),  # scene heuristic
    ("Game_Name_(USA).zip", "Game Name", {"regions": ["USA"]}),
    ("game name v1.2 final.zip", "game name final", {"version": "1.2"}),
    ("Game (USA) (Beta 2).zip", "Game", {"regions": ["USA"], "flags": ["beta"]}),
    ("Game (Europe) (Rev A).zip", "Game", {"regions": ["Europe"], "revision": "A"}),
    ("Game (World).zip", "Game", {"regions": ["World"]}),
    ("Game (Australia).zip", "Game", {"regions": ["Australia"]}),
    ("Game (France).zip", "Game", {"regions": ["France"]}),
    ("Game (Germany).zip", "Game", {"regions": ["Germany"]}),
    ("Game (Italy).zip", "Game", {"regions": ["Italy"]}),
    ("Game (Spain).zip", "Game", {"regions": ["Spain"]}),
    ("Game (Korea).zip", "Game", {"regions": ["Korea"]}),
    ("Game (Brazil).zip", "Game", {"regions": ["Brazil"]}),
    ("Game (Asia).zip", "Game", {"regions": ["Asia"]}),
    ("Game (En).zip", "Game", {"languages": ["English"]}),
    ("Game (Fr,De).zip", "Game", {"languages": ["French", "German"]}),
    ("Game (Disc A).iso", "Game", {"disc_number": "A"}),
    ("Game (CD1).iso", "Game", {"disc_number": "1"}),
    ("Game (DVD 2 of 3).iso", "Game", {"disc_number": "2", "disc_count": "3"}),
    ("Game (Disk 2).iso", "Game", {"disc_number": "2"}),
    ("Game (Track 2).bin", "Game", {"track_number": "2"}),
    ("The Legend of Zelda (USA).nes", "The Legend of Zelda", {"regions": ["USA"]}),
    ("A Boy and His Blob (USA).nes", "A Boy and His Blob", {"regions": ["USA"]}),
    ("Le Mans 24 Hours (Europe).iso", "Le Mans 24 Hours", {"regions": ["Europe"]}),
    ("Die Hard (Germany).iso", "Die Hard", {"regions": ["Germany"]}),
    ("De Blob (Europe).iso", "De Blob", {"regions": ["Europe"]}),
    ("Pokémon - Version Émeraude (France).gba", "Pokémon: Version Émeraude", {"regions": ["France"]}),
    ("Final Fantasy 7 (USA).iso", "Final Fantasy 7", {"regions": ["USA"]}),
    ("Final Fantasy X (USA).iso", "Final Fantasy X", {"regions": ["USA"]}),
    ("Game: Subtitle (USA).iso", "Game: Subtitle", {"regions": ["USA"]}),
    ("Game ~ Subtitle (USA).iso", "Game: Subtitle", {"regions": ["USA"]}),
    ("Game__Name...USA.zip", "Game Name", {"regions": ["USA"]}),
    ("sf2.zip", "sf2", {}),
    ("mslug.zip", "mslug", {}),
    ("0001.bin", "0001", {}),
    ("", "", {}),
    ("", "", {}),
    ("Dr. Mario.zip", "Dr. Mario", {}),
    ("Vol. 2.iso", "Vol. 2", {}),
    ("Mr. Do!.chd", "Mr. Do!", {}),
    ("Game (USA) [h1] (Disc 1 of 2).chd", "Game", {"regions": ["USA"], "flags": ["hack"], "disc_number": "1", "disc_count": "2"}),
    ("Game (USA) (Rev 2) [1A2B3C4D].7z", "Game", {"regions": ["USA"], "revision": "2", "crc32": ["1A2B3C4D"]}),
    ("Game (En,Fr,De,Es,It).zip", "Game", {"languages": ["English", "French", "German", "Spanish", "Italian"]}),
    ("Game [T+Fre] (Japan).zip", "Game", {"regions": ["Japan"], "flags": ["fan_translation"], "translations": ["French"]}),  # CONFIDENCE_LOW: Fre alias
    ("Game (Prototype).zip", "Game", {"flags": ["proto"]}),
    ("Game (Unlicensed).zip", "Game", {"flags": ["unlicensed"]}),
    ("Game (Bad Dump).zip", "Game", {"flags": ["bad_dump"]}),
    ("Game (Fan Translation).zip", "Game", {"flags": ["fan_translation"]}),
    ("Game (Undubbed).zip", "Game", {"flags": ["undub"]}),
    ("Game (Rev. 3).zip", "Game", {"revision": "3"}),
    ("Game v2.05.zip", "Game", {"version": "2.05"}),
    ("Title (1986)(Publisher)[cr].zip", "Title", {"years": ["1986"], "dump_flags": ["cracked"]}),
    ("Game [cr][tr][a].zip", "Game", {"dump_flags": ["cracked", "translated", "alt"]}),
    ("Game (USA) (Disc 2 of 2) (Track 01).cue", "Game", {"regions": ["USA"], "disc_number": "2", "disc_count": "2", "track_number": "01"}),
    ("A Game, An (USA).zip", "An A Game", {"regions": ["USA"]}),  # CONFIDENCE_LOW: uncommon trailing article
    ("Game (PAL).iso", "Game", {"regions": ["Europe"]}),
    ("Game (NTSC).iso", "Game", {"regions": ["USA"]}),
    ("Game (U.S.A.).zip", "Game", {"regions": ["USA"]}),
]


@pytest.mark.parametrize("filename, primary, expected", CASES)
def test_filename_analysis(filename, primary, expected):
    result = analyze(filename, [".chd", ".iso", ".bin", ".cue", ".zip", ".7z", ".nes", ".gba", ".gb", ".sfc", ".rom"])
    if primary:
        assert primary in result.candidates
    else:
        assert result.candidates == []
    for key, value in expected.items():
        assert result.extracted[key] == value


@pytest.mark.parametrize("filename", [
    "Dr. Mario.chd", "Vol. 2.iso", "1942.zip", "Tom Clancy's Rainbow Six 3.iso",
    "Sim City 2000.zip", "Mr. Do!.zip", "sf2.zip", "mslug.zip", "0001.bin",
    "Pokémon (Europe).zip", "ゲーム (Japan).zip",
])
def test_does_not_crash_on_edge_inputs(filename):
    result = analyze(filename, [".chd", ".iso", ".bin", ".zip"])
    assert isinstance(result.candidates, list)
    assert isinstance(result.extracted, dict)


def test_only_known_final_extension_is_removed():
    assert analyze("Dr. Mario", [".chd"]).candidates[0] == "Dr. Mario"
    assert "Dr Mario unknown" in analyze("Dr. Mario.unknown", [".chd"]).candidates


def test_subtitle_components_are_candidates():
    result = analyze("Shin Megami Tensei - Persona 3 Portable.zip", [".zip"])
    assert "Shin Megami Tensei: Persona 3 Portable" in result.candidates
    assert "Shin Megami Tensei" in result.candidates
    assert "Persona 3 Portable" in result.candidates


def test_disc_metadata_is_not_in_candidate():
    result = analyze("Game (Disc 1 of 2).iso", [".iso"])
    assert result.extracted["disc_number"] == "1"
    assert result.extracted["disc_count"] == "2"
    assert "Disc 1" not in result.variants["separators_normalized"]
