import toml
import requests
import xml.etree.ElementTree as ET


def loadXML():
    url = (
        "https://gitlab.com/es-de/emulationstation-de/"
        "-/raw/master/resources/systems/linux/es_systems.xml"
    )

    resp = requests.get(url, timeout=30)
    resp.raise_for_status()

    with open("es_systems.xml", "wb") as f:
        f.write(resp.content)


def parseXML(xmlfile: str) -> None:
    tree = ET.parse(xmlfile)
    root = tree.getroot()

    for child in root:
        platform = child.findtext("name")
        fullname = child.findtext("fullname")
        extensionsString = child.findtext("extension") or ""

        if not platform:
            continue

        extensionsArray = extensionsString.split()

        output["platforms"][platform] = {

            "name": fullname or platform,
            "extensions": []
        }

        for extension in extensionsArray:
            extension = extension.lower()

            if extension not in output["platforms"][platform]["extensions"]:
                output["platforms"][platform]["extensions"].append(extension)


def main():
    global output

    output = {
        "platforms": {}
    }

    loadXML()

    parseXML("es_systems.xml")

    with open("platforms.toml", "w") as f:
        toml.dump(output, f)


if __name__ == "__main__":
    main()
