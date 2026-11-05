# Fabulor-Name: ZNC Buffers
# Fabulor-Version: 1.0.0
# Fabulor-Description: Add menu actions to clear and play ZNC buffers

"""Add menu actions for clearing and replaying ZNC buffers."""

import fabulor

__module_name__ = "ZNC Buffers"
__module_author__ = "fladd & TingPing"
__module_version__ = "1.0.0"
__module_description__ = "Add menu actions to clear and play ZNC buffers"

_MENU_ROOT = "ZNC Buffers"
_MENU_PATHS = (
    _MENU_ROOT,
    _MENU_ROOT + "/Clear Buffer",
    _MENU_ROOT + "/Play Buffer",
)
_MENU_COMMANDS = (
    'MENU ADD "{}"'.format(_MENU_ROOT),
    'MENU ADD "{}/Clear Buffer" "ZNCBUFFER CLEAR"'.format(_MENU_ROOT),
    'MENU ADD "{}/Play Buffer" "ZNCBUFFER PLAY"'.format(_MENU_ROOT),
)
_STATUS_PREFIX = ":*status!znc@znc.in"
_recently_cleared = []


def _print(message):
    fabulor.prnt("[ZNC Buffers] " + message)


def _on_privmsg(words, word_eol, userdata):
    del userdata
    if (
        len(words) <= 6
        or len(word_eol) <= 4
        or words[0] != _STATUS_PREFIX
        or not word_eol[4].startswith("buffers matching")
    ):
        return fabulor.EAT_NONE

    cleared = words[6][1:-1]
    if cleared in _recently_cleared:
        _recently_cleared.remove(cleared)
        return fabulor.EAT_ALL

    return fabulor.EAT_NONE


def _on_command(words, word_eol, userdata):
    del word_eol, userdata
    if len(words) != 2 or words[1].upper() not in ("CLEAR", "PLAY"):
        _print("Usage: /ZNCBUFFER CLEAR|PLAY")
        return fabulor.EAT_ALL

    action = words[1].upper()
    buffer_name = fabulor.get_info("channel") or ""
    if not buffer_name or buffer_name.startswith("*"):
        _print("There is no clearable ZNC buffer in the current tab.")
        return fabulor.EAT_ALL

    if action == "CLEAR":
        _recently_cleared.append(buffer_name)
        fabulor.command("znc clearbuffer {}".format(buffer_name))
    else:
        fabulor.command("znc playbuffer {}".format(buffer_name))

    return fabulor.EAT_ALL


def _register_menu_entries():
    for command in _MENU_COMMANDS:
        fabulor.command(command)


def _unregister_menu_entries(userdata):
    del userdata
    for path in reversed(_MENU_PATHS):
        fabulor.command('MENU DEL "{}"'.format(path))


fabulor.hook_command(
    "ZNCBUFFER",
    _on_command,
    help="Clear or replay the current ZNC buffer",
)
fabulor.hook_server("PRIVMSG", _on_privmsg, priority=fabulor.PRI_HIGH)
_register_menu_entries()
fabulor.hook_unload(_unregister_menu_entries)
_print("Loaded. Use the ZNC Buffers menu or /ZNCBUFFER CLEAR|PLAY.")
