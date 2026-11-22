
"""Conservative ROM filename parsing and IGDB search-candidate generation.

This is entirely slopcoded because i hate regex and i don't have the nerves to do this manually
Example:
    >>> analyze("Legend of Zelda, The (USA).zip", [".zip"]).candidates[:2]
    ['Legend of Zelda, The', 'Legend of Zelda']
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any


# Each expression is compiled once. Character classes and bounded repetitions are
# preferred; none uses nested unbounded quantifiers.
_EXT_RE = re.compile(r"""
    \.[A-Za-z0-9]+$                 # final extension-like suffix only
""", re.VERBOSE)
_TAG_RE = re.compile(r"""
    (?P<open>[\(\[\{])              # opening delimiter
    (?P<body>[^()\[\]{}]{1,160})    # flat tag body; bounded to avoid runaway scans
    (?P<close>[\)\]\}])             # closing delimiter
""", re.VERBOSE)
_WS_RE = re.compile(r"""
    [ \t\r\n]+                      # one or more whitespace characters
""", re.VERBOSE)
_JUNK_RE = re.compile(r"""
    ^[ .,_\-~]+|[ .,_\-~]+$         # punctuation at either edge
""", re.VERBOSE)
_SEP_RE = re.compile(r"""
    [_.]+                           # filename underscores/dots
""", re.VERBOSE)
_DASH_SEP_RE = re.compile(r"""
    \s*[-~]\s*                      # hyphen/tilde separators
""", re.VERBOSE)
_COLON_SEP_RE = re.compile(r"""
    \s*:\s*                         # colon separators in hand-renamed titles
""", re.VERBOSE)
_DISC_RE = re.compile(r"""
    ^\s*(?:disc|disk|cd|dvd)\s*     # media word
    (?P<number>[0-9]+|[A-D])         # disc number/letter
    (?:\s+of\s+(?P<count>[0-9]+))?  # optional total count
    \s*$
""", re.IGNORECASE | re.VERBOSE)
_TRACK_RE = re.compile(r"""
    ^\s*track\s*(?P<number>[0-9]+)\s*$
""", re.IGNORECASE | re.VERBOSE)
_REGION_RE = re.compile(r"""
    ^\s*(?P<region>
        USA|U\.S\.A\.?|U|US|Canada|CAN|
        Europe|EUR|E|Japan|JPN|J|Asia|ASI|Korea|KOR|
        Australia|AUS|World|W|Brazil|BRA|France|FRA|
        Germany|GER|Italy|ITA|Spain|ESP|UK|PAL|NTSC
    )\s*$
""", re.IGNORECASE | re.VERBOSE)
_LANGUAGE_RE = re.compile(r"""
    ^\s*(?P<languages>
        (?:En|Fr|De|Es|It|Pt|Nl|Sv|No|Da|Fi|Pl|Ru|Ja|Ko|Zh|Zhs|Zht)
        (?:\s*[,;+]\s*
        (?:En|Fr|De|Es|It|Pt|Nl|Sv|No|Da|Fi|Pl|Ru|Ja|Ko|Zh|Zhs|Zht))*
    )\s*$
""", re.IGNORECASE | re.VERBOSE)
_REV_RE = re.compile(r"""
    ^\s*(?:rev(?:ision)?\.?\s*|v(?:ersion)?\.?\s*)
    (?P<value>(?:[A-Za-z]?\d+(?:\.\d+)*[A-Za-z]?|[A-Za-z]))\s*$
""", re.IGNORECASE | re.VERBOSE)
_YEAR_RE = re.compile(r"""
    ^\s*(?:19|20)\d{2}(?:-\d{2}(?:-\d{2})?)?\s*$
""", re.VERBOSE)
_CRC_RE = re.compile(r"""
    ^\s*(?P<crc>[0-9A-F]{8})\s*$
""", re.IGNORECASE | re.VERBOSE)
_SERIAL_RE = re.compile(r"""
    (?<![A-Z0-9])
    (?P<serial>
        (?:SLUS|SCUS|SLES|SCES|SLPS|SCPS|SLPM|PAPX|PCSE|ULES)
        [-_ ]?\d{3,5}(?:[._-]\d{2,3})?
    )
    (?![A-Z0-9])
""", re.IGNORECASE | re.VERBOSE)
_GOOD_REGION_RE = re.compile(r"""
    ^\s*(?P<codes>U|E|J|UE|UJ|JU|JE|EU|EJ|W|M\d+)\s*$
""", re.IGNORECASE | re.VERBOSE)
_GOOD_FLAG_RE = re.compile(r"""
    ^\s*(?P<flag>!|[ab hfo]\d*|cr|f|h|m|p|t|tr|u|v)\s*$
""", re.IGNORECASE | re.VERBOSE)
_TRANSLATION_RE = re.compile(r"""
    ^\s*T\s*[-+]\s*(?P<language>[A-Za-z]{2,3})\s*$
""", re.IGNORECASE | re.VERBOSE)
_FLAG_RE = re.compile(r"""
    ^\s*(?P<flag>
        beta(?:\s*\d+)?|proto(?:type)?|demo|sample|unl(?:icensed)?|
        alt(?:ernate)?|hack|translated|translation|english\s+patched|
        undub(?:bed)?|bad\s*dump|bad|cracked|fixed|modified|pirated|
        trained|fan[\s-]*translation|final|retail
    )\s*$
""", re.IGNORECASE | re.VERBOSE)
_PUBLISHER_YEAR_RE = re.compile(r"""
    ^\s*(?:19|20)\d{2}\s*$
""", re.VERBOSE)
_TRAILING_ARTICLE_RE = re.compile(r"""
    ^(?P<title>.+?),\s*(?P<article>
        The|A|An|Le|La|Les|L'|El|Los|Las|Der|Die|Das|De|Het|Een
    )$
""", re.IGNORECASE | re.VERBOSE)
_SCENE_GROUP_RE = re.compile(r"""
    ^(?P<title>.+?)-(?P<group>[A-Z0-9][A-Z0-9_-]{1,24})$
""", re.IGNORECASE | re.VERBOSE)
_ROMAN_RE = re.compile(r"""
    \b(?P<numeral>VIII|VII|VI|IV|V|III|II|IX|X)\b
""", re.IGNORECASE | re.VERBOSE)
_EMPTY_TAG_RE = re.compile(r"""[\(\[\{]\s*[\)\]\}]""", re.VERBOSE)
_SUBTITLE_SPLIT_RE = re.compile(r"""\s+-\s+""", re.VERBOSE)
_VERSION_LOOSE_RE = re.compile(r"""(?<![A-Za-z0-9])v(?:ersion)?\s*(?P<version>\d+(?:\.\d+){1,3}[A-Za-z]?)(?![A-Za-z0-9])""", re.IGNORECASE | re.VERBOSE)
_LOOSE_REGION_RE = re.compile(r"""(?<![A-Za-z])(?:USA|Europe|Japan|World)(?![A-Za-z])""", re.IGNORECASE | re.VERBOSE)
_PUBLISHER_RE = re.compile(r"""[A-Za-z0-9 .&-]{1,80}""", re.VERBOSE)
_SCENE_RE = re.compile(r"""(?P<title>.+?)(?:\.USA)?\.(?P<platform>PSX|PS2|PSP)-(?P<group>[A-Z0-9_-]{2,24})$""", re.IGNORECASE | re.VERBOSE)
_TRAILING_REGION_RE = re.compile(
    r"""
    (?:[ ._-]+)
    (?:USA|U\.?S\.?A\.?|US|Canada|CAN|Europe|EUR|Japan|JPN|
       Asia|ASI|Korea|KOR|Australia|AUS|World|Brazil|BRA|
       France|FRA|Germany|GER|Italy|ITA|Spain|ESP|UK|PAL|NTSC)
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)

REGION_MAP: dict[str, str] = {
    "usa": "USA", "u.s.a": "USA", "u.s.a.": "USA", "u": "USA", "us": "USA",
    "canada": "USA", "can": "USA",
    "europe": "Europe", "eur": "Europe", "e": "Europe", "uk": "Europe",
    "pal": "Europe", "japan": "Japan", "jpn": "Japan", "j": "Japan",
    "asia": "Asia", "asi": "Asia", "korea": "Korea", "kor": "Korea",
    "australia": "Australia", "aus": "Australia", "world": "World",
    "w": "World", "brazil": "Brazil", "bra": "Brazil", "france": "France",
    "fra": "France", "germany": "Germany", "ger": "Germany",
    "italy": "Italy", "ita": "Italy", "spain": "Spain", "esp": "Spain",
    "ntsc": "USA",
}
GOODTOOLS_REGION_MAP: dict[str, str] = {
    "u": "USA", "e": "Europe", "j": "Japan", "ue": "USA/Europe",
    "uj": "USA/Japan", "ju": "USA/Japan", "je": "Japan/Europe",
    "eu": "Europe/USA", "ej": "Europe/Japan", "w": "World",
}
LANGUAGE_MAP: dict[str, str] = {
    "en": "English", "fr": "French", "de": "German", "es": "Spanish",
    "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "sv": "Swedish",
    "no": "Norwegian", "da": "Danish", "fi": "Finnish", "pl": "Polish",
    "ru": "Russian", "ja": "Japanese", "ko": "Korean", "zh": "Chinese",
    "zhs": "Chinese (Simplified)", "zht": "Chinese (Traditional)",
}
FLAG_MAP: dict[str, str] = {
    "beta": "beta", "proto": "proto", "prototype": "proto", "demo": "demo",
    "sample": "sample", "unl": "unlicensed", "unlicensed": "unlicensed",
    "alt": "alt", "alternate": "alt", "hack": "hack",
    "translated": "fan_translation", "translation": "fan_translation",
    "english patched": "fan_translation", "fan translation": "fan_translation",
    "fan-translation": "fan_translation", "undub": "undub",
    "undubbed": "undub", "bad": "bad_dump", "bad dump": "bad_dump",
    "cracked": "cracked", "fixed": "fixed", "modified": "modified",
    "pirated": "pirated", "trained": "trained", "final": "final",
    "retail": "retail",
}


@dataclass
class FilenameAnalysis:
    """Structured filename analysis and ordered search candidates.

    Example:
        >>> result = analyze("Sonic_The_Hedgehog_(USA).zip", [".zip"])
        >>> result.extracted["regions"]
        ['USA']
    """
    variants: dict[str, str | list[str]] = field(default_factory=dict)
    candidates: list[str] = field(default_factory=list)
    extracted: dict[str, Any] = field(default_factory=dict)


def remove_known_extension(file_name: str, known_extensions: list[str]) -> str:
    """Remove only a final configured extension, case-insensitively.

    Example: ``remove_known_extension("Dr. Mario.CHD", [".chd"])`` -> ``"Dr. Mario"``.
    """
    lower = file_name.casefold()
    matches = [ext for ext in known_extensions if ext and lower.endswith(ext.casefold())]
    if not matches:
        return file_name
    extension = max(matches, key=len)
    return file_name[:-len(extension)]


def _clean_tag_text(value: str) -> str:
    """Trim whitespace and harmless surrounding punctuation from a tag."""
    return value.strip()


def extract_tags(value: str) -> tuple[str, dict[str, Any]]:
    """Remove recognized parenthesized/bracketed/braced metadata, preserving unknown tags.

    Example: ``extract_tags("Game (USA) [!]")`` extracts the region and dump flag.
    """
    data: dict[str, Any] = {
        "regions": [], "languages": [], "disc_number": None, "disc_count": None,
        "disc_label": None, "track_number": None, "revision": None,
        "version": None, "flags": [], "dump_flags": [], "translations": [],
        "crc32": [], "serial_ids": [], "years": [], "publishers": [],
        "goodtools_codes": [], "unknown_tags": [],
    }
    output: list[str] = []
    cursor = 0
    saw_year = False
    for match in _TAG_RE.finditer(value):
        output.append(value[cursor:match.start()])
        raw = _clean_tag_text(match.group("body"))
        key = raw.casefold()
        disc = _DISC_RE.match(raw)
        track = _TRACK_RE.match(raw)
        region = _REGION_RE.match(raw)
        language = _LANGUAGE_RE.match(raw)
        revision = _REV_RE.match(raw)
        crc = _CRC_RE.match(raw)
        good_region = _GOOD_REGION_RE.match(raw)
        good_flag = _GOOD_FLAG_RE.match(raw)
        translation = _TRANSLATION_RE.match(raw)
        flag = _FLAG_RE.match(raw)
        if disc:
            data["disc_number"] = disc.group("number").upper()
            data["disc_count"] = disc.group("count")
            data["disc_label"] = raw
        elif track:
            data["track_number"] = track.group("number")
        elif region:
            canonical = REGION_MAP.get(region.group("region").casefold())
            if canonical and canonical not in data["regions"]:
                data["regions"].append(canonical)
        elif language:
            for code in re.split(r"\s*[,;+]\s*", language.group("languages")):
                lang = LANGUAGE_MAP.get(code.casefold())
                if lang and lang not in data["languages"]:
                    data["languages"].append(lang)
        elif revision:
            data["revision"] = revision.group("value")
        elif crc:
            data["crc32"].append(crc.group("crc").upper())
        elif translation:
            code = translation.group("language").casefold()
            data["translations"].append(LANGUAGE_MAP.get(code, {"eng": "English", "fre": "French", "ger": "German", "spa": "Spanish", "ita": "Italian"}.get(code, code.upper())))
            if "fan_translation" not in data["flags"]:
                data["flags"].append("fan_translation")
        elif flag:
            normalized = FLAG_MAP.get(key) or ("beta" if key.startswith("beta") else "proto" if key.startswith("proto") else None)
            if normalized and normalized not in data["flags"]:
                data["flags"].append(normalized)
        elif good_region:
            code = good_region.group("codes").upper()
            data["goodtools_codes"].append(code)
            mapped = GOODTOOLS_REGION_MAP.get(code.casefold())
            if mapped and mapped not in data["regions"]:
                data["regions"].append(mapped)
        elif good_flag:
            code = good_flag.group("flag").casefold()
            if code == "!":
                normalized = "verified_good_dump"
            elif code.startswith("b"):
                normalized = "bad_dump"
            elif code.startswith("h"):
                normalized = "hack"
            elif code.startswith("a"):
                normalized = "alt"
            elif code.startswith("f"):
                normalized = "fixed"
            elif code.startswith("o"):
                normalized = "overdump"
            elif code in {"cr", "t", "tr"}:
                normalized = "cracked" if code == "cr" else "translated"
            else:
                normalized = code
            if normalized not in data["dump_flags"]:
                data["dump_flags"].append(normalized)
            if normalized in {"bad_dump", "hack", "alt"} and normalized not in data["flags"]:
                data["flags"].append(normalized)
        elif _YEAR_RE.match(raw):
            data["years"].append(raw)
            saw_year = True
        elif saw_year and _PUBLISHER_RE.fullmatch(raw):
            data["publishers"].append(raw)
        else:
            data["unknown_tags"].append(raw)
            output.append(match.group(0))
        cursor = match.end()
    output.append(value[cursor:])
    cleaned = "".join(output)
    serials = [m.group("serial").upper() for m in _SERIAL_RE.finditer(cleaned)]
    if serials:
        data["serial_ids"].extend(serials)
        cleaned = _SERIAL_RE.sub(" ", cleaned)
    # Remove only empty delimiters left after recognized metadata.
    cleaned = _EMPTY_TAG_RE.sub(" ", cleaned)
    return cleaned, data


def normalize_separators(value: str) -> str:
    """Turn filename separators into spaces while retaining explicit subtitle dashes.

    Example: ``normalize_separators("Game.Name_USA")`` -> ``"Game Name USA"``.
    """
    value = _SEP_RE.sub(" ", value)
    value = _COLON_SEP_RE.sub(" - ", value)
    value = re.sub(r"\s*~\s*", " - ", value)
    value = _WS_RE.sub(" ", value)
    value = _JUNK_RE.sub("", value)
    return value.strip()


def move_trailing_article(value: str) -> str:
    """Move a recognized comma-suffixed article to the front.

    Example: ``move_trailing_article("Legend of Zelda, The")`` -> ``"The Legend of Zelda"``.
    """
    match = _TRAILING_ARTICLE_RE.match(value.strip())
    if not match:
        return value.strip()
    article = match.group("article")
    title = match.group("title")
    return f"{article} {title}"


def split_subtitle(value: str) -> list[str]:
    """Return full title and useful main/subtitle components.

    Example: ``split_subtitle("Game - Episode II")`` -> full, main, and subtitle.
    """
    parts = [move_trailing_article(part.strip()) for part in _SUBTITLE_SPLIT_RE.split(value) if part.strip()]
    if len(parts) <= 1:
        return [value] if value else []
    result = [": ".join(parts)]
    result.extend(parts)
    return result


def title_text_variants(value: str) -> list[str]:
    """Generate conservative punctuation, Roman-numeral, and accent variants.

    Example: ``title_text_variants("Pokémon & Final Fantasy VII")`` includes
    ``"Pokemon and Final Fantasy 7"``.
    """
    values = [value]
    if "&" in value:
        values.append(value.replace("&", "and"))
    if "'" in value or "’" in value:
        values.extend([value.replace("’", "'"), value.replace("'", "")])
    if '"' in value:
        values.append(value.replace('"', ""))
    roman = _ROMAN_RE.search(value)
    if roman:
        numeral_values = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5,
                          "VI": 6, "VII": 7, "VIII": 8, "IX": 9, "X": 10}
        number = numeral_values.get(roman.group("numeral").upper())
        if number is not None:
            values.append(value[:roman.start()] + str(number) + value[roman.end():])
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    if ascii_value != value:
        values.append(ascii_value)
    folded = value.casefold()
    if folded != value:
        values.append(folded)
    result: list[str] = []
    seen: set[str] = set()
    for item in values:
        item = _WS_RE.sub(" ", item).strip()
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return result


def _empty_metadata() -> dict[str, Any]:
    """Create a fresh, fully shaped extraction dictionary."""
    return {
        "regions": [], "languages": [], "disc_number": None, "disc_count": None,
        "disc_label": None, "track_number": None, "revision": None, "version": None,
        "flags": [], "dump_flags": [], "translations": [], "crc32": [],
        "serial_ids": [], "years": [], "publishers": [], "goodtools_codes": [],
        "unknown_tags": [],
    }


def _merge_metadata(target: dict[str, Any], source: dict[str, Any]) -> None:
    """Merge extracted metadata without duplicating list entries."""
    for key, value in source.items():
        if isinstance(value, list):
            for item in value:
                if item not in target[key]:
                    target[key].append(item)
        elif value is not None:
            target[key] = value


def _extract_loose_metadata(value: str, data: dict[str, Any]) -> str:
    """Extract loose scene/hand-renamed version and region tokens."""
    match = _VERSION_LOOSE_RE.search(value)
    if match:
        data["version"] = match.group("version")
        value = _VERSION_LOOSE_RE.sub(" ", value)
    for token in _LOOSE_REGION_RE.finditer(value):
        region = REGION_MAP[token.group(0).casefold()]
        if region not in data["regions"]:
            data["regions"].append(region)
    value = _LOOSE_REGION_RE.sub(" ", value)
    return value

def comparison_title(file_name: str, known_extensions: list[str]) -> str:
    """Return a conservative title for comparison against IGDB results.

    Removes the configured extension and recognized region tags.
    Preserves all other filename information.
    """
    value = remove_known_extension(file_name, known_extensions)

    pieces = []
    cursor = 0

    for match in _TAG_RE.finditer(value):
        pieces.append(value[cursor:match.start()])
        raw = _clean_tag_text(match.group("body"))

        # Remove only recognized region tags.
        if not (_REGION_RE.match(raw) or _GOOD_REGION_RE.match(raw)):
            pieces.append(match.group(0))

        cursor = match.end()

    pieces.append(value[cursor:])
    value = "".join(pieces)

    # Also handle unbracketed region suffixes such as Game.USA.
    value = _TRAILING_REGION_RE.sub("", value)

    value = _EMPTY_TAG_RE.sub("", value)
    return _WS_RE.sub(" ", value).strip()

def analyze(file_name: str, known_extensions: list[str]) -> FilenameAnalysis:
    """Analyze a ROM filename and return ordered, progressively simplified candidates.

    Example:
        >>> analyze("Final.Fantasy.VII.(USA).chd", [".chd"]).candidates[0]
        'Final Fantasy VII'
    """
    extracted = _empty_metadata()
    stages: dict[str, str | list[str]] = {}
    stages["original"] = file_name
    without_extension = remove_known_extension(file_name, known_extensions)
    stages["no_extension"] = without_extension

    without_tags, found = extract_tags(without_extension)
    _merge_metadata(extracted, found)
    stages["no_tags"] = without_tags

    loose = _extract_loose_metadata(without_tags, extracted)
    # Scene release suffixes are usually group labels, not part of the game title.
    scene = _SCENE_RE.match(loose.strip())
    if scene:
        loose = scene.group("title")
    stages["metadata_extracted"] = loose

    normalized = normalize_separators(loose)
    stages["separators_normalized"] = normalized
    article = move_trailing_article(normalized)
    stages["article_moved"] = article

    subtitle_values = split_subtitle(article)
    stages["subtitle_split"] = subtitle_values

    text_values: list[str] = []
    for item in subtitle_values:
        for variant in title_text_variants(item):
            if variant not in text_values:
                text_values.append(variant)
    stages["text_variants"] = text_values

    candidates: list[str] = []
    for stage_value in stages.values():
        values = stage_value if isinstance(stage_value, list) else [stage_value]
        for candidate in values:
            candidate = _WS_RE.sub(" ", candidate).strip(" .,_-~")
            if candidate and candidate not in candidates:
                candidates.append(candidate)
    return FilenameAnalysis(variants=stages, candidates=candidates, extracted=extracted)
