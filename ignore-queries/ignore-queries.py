# Fabulor-Name: Ignore Queries
# Fabulor-Version: 1.0.3
# Fabulor-Description: Suppresses private messages with per-network whitelists

"""Fabulor add-on for suppressing unwanted private messages."""

import json
import os
import time

import fabulor

__module_name__ = "Ignore Queries"
__module_version__ = "1.0.3"
__module_description__ = (
    "Suppresses private messages with per-network toggles and whitelists"
)

IGNORE_DURATION = 30 * 60
WHITELIST_FILE = os.path.join(os.path.dirname(__file__), "whitelist.json")
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")

_state = {}
_MENU_ROOT = "Settings/Ignore Queries"
_MENU_PATHS = (
    _MENU_ROOT,
    _MENU_ROOT + "/Toggle",
    _MENU_ROOT + "/On",
    _MENU_ROOT + "/Off",
    _MENU_ROOT + "/Status",
    _MENU_ROOT + "/Whitelist List",
)

_RFC1459_CASEMAP = str.maketrans(
    {
        "[": "{",
        "]": "}",
        "\\": "|",
        "^": "~",
    }
)


def _new_network_state():
    return {"enabled": False, "timers": {}, "whitelist": set()}


def _network_identity():
    network = fabulor.get_info("network")
    server = fabulor.get_info("server")
    name = network or server
    if not name:
        return None, None
    return name.casefold(), name


def _get_network_state():
    key, display_name = _network_identity()
    if key is None:
        return None, None
    return _state.setdefault(key, _new_network_state()), display_name


def _print(message):
    fabulor.prnt("[Ignore Queries] " + message)


def _load_whitelist():
    if not os.path.isfile(WHITELIST_FILE):
        return

    try:
        with open(WHITELIST_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        if not isinstance(data, dict):
            raise ValueError("top-level value must be an object")

        for network, nicks in data.items():
            if not isinstance(network, str) or not isinstance(nicks, list):
                raise ValueError("network names must map to nickname arrays")
            if not all(isinstance(nick, str) and nick for nick in nicks):
                raise ValueError("nicknames must be non-empty strings")

            state = _state.setdefault(network.casefold(), _new_network_state())
            state["whitelist"].update(nicks)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        _print("Could not load whitelist: {}".format(error))


def _load_settings():
    if not os.path.isfile(SETTINGS_FILE):
        return

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as handle:
            data = json.load(handle)

        if not isinstance(data, dict):
            raise ValueError("top-level value must be an object")

        for network, settings in data.items():
            if not isinstance(network, str) or not isinstance(settings, dict):
                raise ValueError("network names must map to setting objects")

            enabled = settings.get("enabled")
            if enabled is None:
                continue
            if not isinstance(enabled, bool):
                raise ValueError("enabled must be a boolean")

            state = _state.setdefault(network.casefold(), _new_network_state())
            state["enabled"] = enabled
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        _print("Could not load settings: {}".format(error))


def _save_settings():
    data = {network: {"enabled": state["enabled"]} for network, state in _state.items()}
    temporary_file = SETTINGS_FILE + ".tmp"

    try:
        with open(temporary_file, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary_file, SETTINGS_FILE)
    except OSError as error:
        try:
            os.remove(temporary_file)
        except OSError:
            pass
        _print("Could not save settings: {}".format(error))
        return False

    return True


def _save_whitelist():
    data = {
        network: sorted(state["whitelist"], key=str.casefold)
        for network, state in _state.items()
        if state["whitelist"]
    }
    temporary_file = WHITELIST_FILE + ".tmp"

    try:
        with open(temporary_file, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary_file, WHITELIST_FILE)
    except OSError as error:
        try:
            os.remove(temporary_file)
        except OSError:
            pass
        _print("Could not save whitelist: {}".format(error))
        return False

    return True


def _nick_key(nick):
    return nick.casefold().translate(_RFC1459_CASEMAP)


def _matching_nick(nicknames, nick):
    wanted = _nick_key(nick)
    for candidate in nicknames:
        if _nick_key(candidate) == wanted:
            return candidate
    return None


def _require_network():
    state, network = _get_network_state()
    if state is None:
        _print("This command must be used in a connected network context.")
    return state, network


def _set_enabled(enabled):
    state, network = _require_network()
    if state is None:
        return
    state["enabled"] = enabled
    _save_settings()
    status = "enabled" if enabled else "disabled"
    _print("{} for {}.".format(status.capitalize(), network))


def _show_status():
    state, network = _require_network()
    if state is None:
        return
    status = "enabled" if state["enabled"] else "disabled"
    _print("{} is {} for {}.".format(__module_name__, status, network))


def _whitelist_add(nick):
    state, network = _require_network()
    if state is None:
        return
    existing = _matching_nick(state["whitelist"], nick)
    if existing is not None:
        _print("'{}' is already whitelisted for {}.".format(existing, network))
        return
    state["whitelist"].add(nick)
    if _save_whitelist():
        _print("Added '{}' to the whitelist for {}.".format(nick, network))


def _whitelist_remove(nick):
    state, network = _require_network()
    if state is None:
        return
    existing = _matching_nick(state["whitelist"], nick)
    if existing is None:
        _print("'{}' is not whitelisted for {}.".format(nick, network))
        return
    state["whitelist"].remove(existing)
    if _save_whitelist():
        _print("Removed '{}' from the whitelist for {}.".format(existing, network))


def _whitelist_list():
    state, network = _require_network()
    if state is None:
        return
    whitelist = sorted(state["whitelist"], key=str.casefold)
    if whitelist:
        _print("Whitelist for {}: {}".format(network, ", ".join(whitelist)))
    else:
        _print("Whitelist for {} is empty.".format(network))


def _show_help():
    _print("Usage: /IGNOREQUERIES ON|OFF|TOGGLE|STATUS")
    _print("       /IGNOREQUERIES WHITELIST ADD|REMOVE <nick>")
    _print("       /IGNOREQUERIES WHITELIST LIST")


def _command_arguments(words, word_eol):
    if word_eol and word_eol[0]:
        tokens = word_eol[0].split()
        if tokens and tokens[0].lstrip("/").upper() == "IGNOREQUERIES":
            return tokens[1:]

    return words[1:]


def on_ignorequeries_command(words, word_eol, userdata):
    del userdata
    args = _command_arguments(words, word_eol)
    action = args[0].upper() if args else "STATUS"

    if action == "ON":
        _set_enabled(True)
    elif action == "OFF":
        _set_enabled(False)
    elif action == "TOGGLE":
        state, _network = _require_network()
        if state is not None:
            _set_enabled(not state["enabled"])
    elif action == "STATUS":
        _show_status()
    elif action in ("WHITELIST", "ALLOW"):
        subcommand = args[1].upper() if len(args) > 1 else "LIST"
        if subcommand == "LIST":
            _whitelist_list()
        elif subcommand in ("ADD", "REMOVE") and len(args) > 2 and args[2]:
            if subcommand == "ADD":
                _whitelist_add(args[2])
            else:
                _whitelist_remove(args[2])
        else:
            _show_help()
    else:
        _show_help()

    return fabulor.EAT_ALL


def _alias_command(action):
    def callback(words, word_eol, userdata):
        del words, word_eol, userdata
        _set_enabled(action)
        return fabulor.EAT_ALL

    return callback


def on_toggle_command(words, word_eol, userdata):
    del words, word_eol, userdata
    state, _network = _require_network()
    if state is not None:
        _set_enabled(not state["enabled"])
    return fabulor.EAT_ALL


def _whitelist_alias(action):
    def callback(words, word_eol, userdata):
        del word_eol, userdata
        if action == "list":
            _whitelist_list()
        elif len(words) > 1 and words[1]:
            if action == "add":
                _whitelist_add(words[1])
            else:
                _whitelist_remove(words[1])
        else:
            _show_help()
        return fabulor.EAT_ALL

    return callback


def on_privmsg(words, word_eol, userdata, attrs):
    del word_eol, userdata, attrs
    if len(words) < 3:
        return fabulor.EAT_NONE

    state, _network = _get_network_state()
    if state is None or not state["enabled"]:
        return fabulor.EAT_NONE

    target = words[2]
    own_nick = fabulor.get_info("nick")
    if not own_nick or fabulor.nickcmp(target, own_nick) != 0:
        return fabulor.EAT_NONE

    prefix = words[0].lstrip(":")
    nick = prefix.split("!", 1)[0]
    if not nick or _matching_nick(state["whitelist"], nick) is not None:
        return fabulor.EAT_NONE

    now = time.monotonic()
    timers = state["timers"]
    expired_before = now - IGNORE_DURATION
    state["timers"] = {
        sender: timestamp
        for sender, timestamp in timers.items()
        if timestamp >= expired_before
    }

    matching_timer = _matching_nick(state["timers"], nick)
    if matching_timer is None:
        fabulor.send_message(
            nick,
            "Sorry, I am ignoring queries. If you would like to talk to me, "
            "please talk in the channel. Thanks.",
        )
    else:
        del state["timers"][matching_timer]

    state["timers"][nick] = now
    return fabulor.EAT_FABULOR


def _register_menu_entries():
    menu_commands = (
        'MENU ADD "{}"'.format(_MENU_ROOT),
        'MENU ADD "{}/Toggle" "IGNOREQUERIES TOGGLE"'.format(_MENU_ROOT),
        'MENU ADD "{}/On" "IGNOREQUERIES ON"'.format(_MENU_ROOT),
        'MENU ADD "{}/Off" "IGNOREQUERIES OFF"'.format(_MENU_ROOT),
        'MENU ADD "{}/Status" "IGNOREQUERIES STATUS"'.format(_MENU_ROOT),
        'MENU ADD "{}/Whitelist List" "IGNOREQUERIES WHITELIST LIST"'.format(
            _MENU_ROOT
        ),
    )
    for command in menu_commands:
        fabulor.command(command)


def _unregister_menu_entries(userdata):
    del userdata
    for path in reversed(_MENU_PATHS):
        fabulor.command('MENU DEL "{}"'.format(path))


_load_whitelist()
_load_settings()

fabulor.hook_command(
    "IGNOREQUERIES",
    on_ignorequeries_command,
    help="Ignore private messages; use /IGNOREQUERIES for status",
)
fabulor.hook_command("IGNOREQUERIES_ON", _alias_command(True))
fabulor.hook_command("IGNOREQUERIES_OFF", _alias_command(False))
fabulor.hook_command("IGNOREQUERIES_TOGGLE", on_toggle_command)
fabulor.hook_command("IGNOREQUERIES_WHITELIST_ADD", _whitelist_alias("add"))
fabulor.hook_command("IGNOREQUERIES_WHITELIST_REMOVE", _whitelist_alias("remove"))
fabulor.hook_command("IGNOREQUERIES_WHITELIST_LIST", _whitelist_alias("list"))
fabulor.hook_server_attrs("PRIVMSG", on_privmsg, priority=fabulor.PRI_HIGH)
_register_menu_entries()
fabulor.hook_unload(_unregister_menu_entries)

_print("Loaded. Use /IGNOREQUERIES for status or /IGNOREQUERIES HELP for help.")
