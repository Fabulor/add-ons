# Fabulor-Name: Alias
# Fabulor-Version: 1.1.0
# Fabulor-Description: Create persistent aliases for one or more commands

"""Fabulor add-on for creating persistent command aliases."""

import platform
import re
import time

import hexchat

__module_name__ = "Alias"
__module_version__ = "1.1.0"
__module_description__ = "Create persistent aliases for one or more commands"

HELP_ALIAS = (
    "Usage: /ALIAS NEWCMD COMMAND[; COMMAND2[;...]], adds NEWCMD as an "
    "alias for one or more commands separated by ';'"
)
HELP_UNALIAS = "Usage: /UNALIAS NEWCMD, removes NEWCMD from aliases"
HELP_ALIASES = "Usage: /ALIASES, shows the currently defined aliases"

_INFO_PLACEHOLDER_RE = re.compile(r"%(\w)")
_ARGUMENT_PLACEHOLDER_RE = re.compile(r"%(&?)(\d+)")
_hooks = {}


def _selected_nicks():
    users = hexchat.get_list("users") or ()
    return " ".join(user.nick for user in users if getattr(user, "selected", 0) > 0)


def _machine_info():
    machine_info = hexchat.get_info("machine")
    if machine_info:
        return machine_info

    operating_system = platform.platform()
    processor = platform.processor() or platform.machine()
    return f"{operating_system} [{processor}]" if processor else operating_system


def _replace_info_placeholder(match):
    placeholder = match.group(1)
    replacements = {
        "a": _selected_nicks,
        "c": lambda: hexchat.get_info("channel") or "",
        "e": lambda: hexchat.get_info("network") or "",
        "m": _machine_info,
        "n": lambda: hexchat.get_info("nick") or "",
        "t": lambda: time.strftime("%c"),
        "v": lambda: hexchat.get_info("version") or "",
    }
    replacement = replacements.get(placeholder)
    return replacement() if replacement is not None else match.group(0)


def _expand_command(command, words, word_eol):
    command = _INFO_PLACEHOLDER_RE.sub(_replace_info_placeholder, command)

    def replace_argument(match):
        index = int(match.group(2))
        values = word_eol if match.group(1) == "&" else words
        return values[index] if index < len(values) else ""

    return _ARGUMENT_PLACEHOLDER_RE.sub(replace_argument, command)


def _register_alias(name, commands):
    def callback(words, word_eol, userdata):
        del userdata
        for command in commands.split(";"):
            command = command.strip()
            if command:
                hexchat.command(_expand_command(command, words, word_eol))
        return hexchat.EAT_ALL

    existing_hook = _hooks.get(name)
    if existing_hook is not None:
        hexchat.unhook(existing_hook)

    _hooks[name] = hexchat.hook_command(name, callback)
    return hexchat.set_pluginpref(name, commands)


def on_alias(words, word_eol, userdata):
    del userdata
    if len(words) < 3 or not words[1] or not word_eol[2]:
        hexchat.prnt(HELP_ALIAS)
        return hexchat.EAT_HEXCHAT

    name = words[1].upper()
    if not _register_alias(name, word_eol[2]):
        hexchat.prnt(f"Alias: could not save /{name}")
    return hexchat.EAT_HEXCHAT


def on_unalias(words, word_eol, userdata):
    del word_eol, userdata
    if len(words) < 2 or not words[1]:
        hexchat.prnt(HELP_UNALIAS)
        return hexchat.EAT_HEXCHAT

    name = words[1].upper()
    hook = _hooks.pop(name, None)
    if hook is not None:
        hexchat.unhook(hook)
        hexchat.del_pluginpref(name)
    return hexchat.EAT_HEXCHAT


def on_aliases(words, word_eol, userdata):
    del words, word_eol, userdata
    hexchat.prnt("{:<20}: {}".format("Alias", "Commands"))
    hexchat.prnt("-" * 64)
    for name in sorted(_hooks):
        commands = hexchat.get_pluginpref(name)
        if commands is not None:
            hexchat.prnt(f"{name:<20}: {commands}")
    return hexchat.EAT_HEXCHAT


for preference_name in hexchat.list_pluginpref() or ():
    saved_commands = hexchat.get_pluginpref(preference_name)
    if isinstance(saved_commands, str):
        _register_alias(preference_name.upper(), saved_commands)

hexchat.hook_command("ALIAS", on_alias, help=HELP_ALIAS)
hexchat.hook_command("UNALIAS", on_unalias, help=HELP_UNALIAS)
hexchat.hook_command("ALIASES", on_aliases, help=HELP_ALIASES)
