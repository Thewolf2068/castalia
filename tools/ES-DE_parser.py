import toml
import sys
import time
import requests
import xml.etree.ElementTree as ET

urlPlatforms = "https://api.igdb.com/v4/platforms"

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

# def get_igdb_ids(client_id: str, bearer_secret: str) -> None:
#     bearer_secret = f"Bearer {bearer_secret}"
#     i = 0;
#     for platform, data in output["platforms"].items():
#         fullname = data["name"]
#
#
#         headers={'Client-ID': client_id, 'Authorization': bearer_secret }
#
#         x = requests.post(urlPlatforms, headers=headers, data=f'search "{fullname}"; fields name, slug;')
#
#         returnJson = x.json()
#         if returnJson:
#             output["platforms"][platform]["igdb"] = returnJson[0]["id"]
#             print(f"Response: {returnJson}")
#         else:
#             output["platforms"][platform]["igdb"] = None
#             print(f"No IGDB match found for: {platform}")
#         if i % 4 == 0:
#             time.sleep(1)
#         i = i + 1
        

        


def main():
    global output

    output = {
        "platforms": {}
    }

    loadXML()

    parseXML("es_systems.xml")

    # get_igdb_ids(sys.argv[1], sys.argv[2])

    with open("platforms.toml", "w") as f:
        toml.dump(output, f)



if __name__ == "__main__":
    main()
