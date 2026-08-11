"""
Usage: /ud <word>
Creator: x13machine <https://github.com/x13machine>
License: WTFPL <http://www.wtfpl.net/>
"""

# Fabulor-Name: Urban Dictionary
# Fabulor-Version: 1.0
# Fabulor-Description: Gets the Urban Dictionary definitions

"""Fabulor addon to access UrbanDictionary definitions. Usage: /ud <word>"""

__module_name__ = "Urban Dictionary"
__module_version__ = "1.0"
__module_description__ = "Gets the Urban Dictionary definitions"
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import hexchat


def ud(word, word_eol, userdata):
    try:
        if len(word_eol) < 2 or not word_eol[1].strip():
            hexchat.prnt("Urban Dictionary: usage: /ud <word>")
            return hexchat.EAT_ALL

        query = urlencode({"term": word_eol[1]})
        with urlopen(
            "https://api.urbandictionary.com/v0/define?" + query, timeout=10
        ) as response:
            data = json.loads(response.read().decode("utf-8"))["list"][0]

        hexchat.prnt("Urban Dictionary -> " + data["word"] + ": " + data["definition"])
    except (IndexError, KeyError):
        hexchat.prnt("Urban Dictionary: no definition found")
    except (HTTPError, URLError, json.JSONDecodeError) as error:
        hexchat.prnt("Urban Dictionary: lookup failed: " + str(error))

    return hexchat.EAT_ALL


hexchat.hook_command("ud", ud, help="UD <word>")
