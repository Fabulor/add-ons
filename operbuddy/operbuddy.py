# Fabulor-Name: OperBuddy
# Fabulor-Version: 1.0.0
# Fabulor-Description: IRC operator commands and server-notice routing

"""Fabulor add-on with useful commands and notifications for IRC operators."""

import json
import os

import fabulor

__module_name__ = "OperBuddy"
__module_version__ = "1.0.0"
__module_description__ = "IRC operator commands and server-notice routing"

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "settings.json")
DEFAULT_SETTINGS = {
    "away_message": (
        "[AutoReply]: I am currently away, please be patient until I return. "
        "If you need help please join #help"
    ),
    "use_away_message": 1,
    "whois_on_query": 1,
    "global_invite": 0,
    "show_full_server_name": 0,
    "netsplit_audio_file": "",
}
_BOOLEAN_SETTINGS = {
    "use_away_message",
    "whois_on_query",
    "global_invite",
    "show_full_server_name",
}
_settings = dict(DEFAULT_SETTINGS)
_invite_channel = None


def _print(message):
    fabulor.prnt("[OperBuddy] " + message)


def _load_settings():
    if not os.path.isfile(SETTINGS_FILE):
        return
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as handle:
            saved = json.load(handle)
        if not isinstance(saved, dict):
            raise ValueError("settings must be a JSON object")
        for key, value in saved.items():
            if key not in DEFAULT_SETTINGS:
                continue
            if key in _BOOLEAN_SETTINGS:
                if isinstance(value, bool) or value not in (0, 1):
                    raise ValueError("{} must be 0 or 1".format(key))
                value = int(value)
            elif not isinstance(value, str):
                raise ValueError("{} must be text".format(key))
            _settings[key] = value
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        _print("Could not load settings: {}".format(error))


def _save_settings():
    temporary_file = SETTINGS_FILE + ".tmp"
    try:
        with open(temporary_file, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(_settings, handle, indent=2, sort_keys=True)
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


def _words_tail(word_eol, index):
    if len(word_eol) <= index:
        return ""
    return word_eol[index].lstrip(":").strip()


def _server_name(words):
    prefix = words[0].lstrip(":") if words else "server"
    if _settings["show_full_server_name"]:
        return prefix
    return prefix.split(".", 1)[0]


def _enable_context_api(context):
    method = getattr(context, "emit_print", None)
    if method is None:
        return False
    capability_check = method.__func__.__globals__.get("__require_capability")
    if capability_check is None:
        return False
    method.__func__.__globals__.setdefault(
        "_Context__require_capability", capability_check
    )
    return True


def _emit_tab_message(tab_name, message):
    server = fabulor.get_info("server")
    context = fabulor.find_context(server=server, channel=tab_name)
    if context is None:
        fabulor.command("QUERY -nofocus " + tab_name)
        context = fabulor.find_context(server=server, channel=tab_name)
    if context is None or not _enable_context_api(context):
        _print("{}: {}".format(tab_name, message))
        return
    try:
        context.emit_print("Channel Message", tab_name, message)
    except (AttributeError, NameError, PermissionError, RuntimeError, TypeError):
        _print("{}: {}".format(tab_name, message))


def _show_settings():
    for key in DEFAULT_SETTINGS:
        value = _settings[key]
        if key in _BOOLEAN_SETTINGS:
            value = "enabled" if value else "disabled"
        elif not value:
            value = "(not set)"
        _print("{}: {}".format(key, value))


def _parse_command_text(words, word_eol):
    action = words[1].lower() if len(words) > 1 else "help"
    if action == "set":
        if len(words) < 3:
            return action, "", ""
        key = words[2].lower()
        value = _words_tail(word_eol, 3)
        return action, key, value
    return action, "", ""


def on_operbuddy(words, word_eol, userdata):
    del userdata
    action, key, value = _parse_command_text(words, word_eol)
    if action in ("help", "?"):
        _print("Usage: /OPERBUDDY SETTINGS | SET <setting> <value>")
        _print("Settings: {}".format(", ".join(DEFAULT_SETTINGS)))
    elif action in ("settings", "enabled"):
        _show_settings()
    elif action == "set":
        if key not in DEFAULT_SETTINGS:
            _print("Unknown setting: {}".format(key or "(missing)"))
        elif key in _BOOLEAN_SETTINGS:
            try:
                parsed_value = int(value)
            except ValueError:
                parsed_value = -1
            if parsed_value not in (0, 1) or value not in ("0", "1"):
                _print("{} must be 0 or 1.".format(key))
            else:
                previous_value = _settings[key]
                _settings[key] = parsed_value
                if _save_settings():
                    if key == "global_invite" and not parsed_value:
                        global _invite_channel
                        _invite_channel = None
                    _print("Set {} to {}.".format(key, parsed_value))
                else:
                    _settings[key] = previous_value
        else:
            if not value:
                _print("Usage: /OPERBUDDY SET {} <value>".format(key))
            else:
                previous_value = _settings[key]
                _settings[key] = value
                if _save_settings():
                    _print("Set {}.".format(key))
                else:
                    _settings[key] = previous_value
    else:
        _print("Unknown action. Use /OPERBUDDY for help.")
    return fabulor.EAT_ALL


def on_ginvite(words, word_eol, userdata):
    del userdata
    global _invite_channel
    if len(words) < 2 or not words[1]:
        _print("Usage: /GINVITE <channel>")
    else:
        previous_value = _settings["global_invite"]
        _settings["global_invite"] = 1
        if not _save_settings():
            _settings["global_invite"] = previous_value
            return fabulor.EAT_ALL
        _invite_channel = words[1]
        fabulor.command("QUOTE MASKTRACE !*!*@*")
        _print("Sending global invites to {}.".format(_invite_channel))
    return fabulor.EAT_ALL


def on_global_invite_numeric(words, word_eol, userdata):
    del word_eol, userdata
    if not _settings["global_invite"] or not _invite_channel or len(words) <= 5:
        return fabulor.EAT_NONE
    fabulor.command("INVITE {} {}".format(words[5], _invite_channel))
    return fabulor.EAT_ALL


def on_open_dialog(words, word_eol, userdata, attributes=None):
    del words, word_eol, userdata, attributes
    channel = fabulor.get_info("channel") or ""
    if channel.lower().startswith("opbud:"):
        return fabulor.EAT_ALL
    if not _settings["whois_on_query"] or not channel:
        return fabulor.EAT_ALL
    fabulor.command("QUERY " + channel)
    fabulor.command("WHOIS " + channel)
    away = fabulor.get_info("away")
    if _settings["use_away_message"] and away:

        def send_away_reply():
            fabulor.command("MSG {} {}".format(channel, _settings["away_message"]))
            return False

        fabulor.hook_timer(500, send_away_reply)
    return fabulor.EAT_ALL


def on_rehash(words, word_eol, userdata):
    del userdata
    message = _words_tail(word_eol, 3)
    _print("{}:\t{}".format(_server_name(words), message))
    return fabulor.EAT_ALL


def on_wallops(words, word_eol, userdata):
    del userdata
    _emit_tab_message("OpBud:WALLOPS", _words_tail(word_eol, 2))
    return fabulor.EAT_ALL


def on_snotice(words, word_eol, userdata, attributes=None):
    del userdata, attributes
    if len(words) < 3 or words[2] != "*":
        return fabulor.EAT_NONE

    message = _words_tail(word_eol, 3)
    details = _words_tail(word_eol, 6)
    client_details = _words_tail(word_eol, 8)
    lowered = message.lower()
    if "*** notice -- netsplit" in lowered:
        _emit_tab_message("OpBud:Links", details)
        audio_file = _settings["netsplit_audio_file"]
        if audio_file:
            fabulor.command("SPLAY " + audio_file)
        return fabulor.EAT_ALL
    if "split from" in lowered:
        _emit_tab_message("OpBud:Links", "\x0304" + details + "\x03")
        fabulor.command("GUI SHOW")
        fabulor.command("GUI FOCUS")
        return fabulor.EAT_ALL
    if "being introduced by" in lowered or "netjoin" in lowered:
        _emit_tab_message("OpBud:Links", details)
        return fabulor.EAT_ALL
    if "*** notice -- client exiting" in lowered:
        _emit_tab_message("OpBud:Clients", "\x0304" + client_details + "\x03")
        return fabulor.EAT_ALL
    if "*** notice -- client connecting" in lowered:
        _emit_tab_message("OpBud:Clients", "\x0303" + client_details + "\x03")
        return fabulor.EAT_ALL
    if "listed on dnsbl" in lowered:
        _emit_tab_message("OpBud:Clients", details)
        return fabulor.EAT_ALL

    _emit_tab_message("OpBud:SNotice", "<{}> {}".format(_server_name(words), details))
    return fabulor.EAT_ALL


def on_stats_g(words, word_eol, userdata):
    del userdata
    if len(words) <= 6:
        return fabulor.EAT_NONE
    ip = words[4]
    username = words[6]
    reason_and_setter = _words_tail(word_eol, 7).split("|", 1)
    reason = reason_and_setter[0]
    setter = reason_and_setter[1] if len(reason_and_setter) > 1 else ""
    _emit_tab_message("OpBud:Bans", "Global K:Line for {}@{}".format(username, ip))
    _emit_tab_message("OpBud:Bans", "Reason: {}".format(reason))
    _emit_tab_message("OpBud:Bans", "Set By: {}".format(setter))
    return fabulor.EAT_ALL


def on_reroute(words, word_eol, userdata):
    del userdata
    if len(words) < 3:
        _print("Usage: /REROUTE <server> <target-server>")
        return fabulor.EAT_ALL
    source, target = words[1], words[2]
    _print("Rerouting {} to {}.".format(source, target))
    fabulor.command("SQUIT {} :rerouting to {}".format(source, target))

    def connect_server():
        fabulor.command("CONNECT {} 0 {}".format(source, target))
        return False

    fabulor.hook_timer(1000, connect_server)
    return fabulor.EAT_ALL


def on_closechan(words, word_eol, userdata):
    del userdata
    if len(words) < 3:
        _print("Usage: /CLOSECHAN <channel> <redirect-channel> [reason]")
        return fabulor.EAT_ALL
    channel, redirect = words[1], words[2]
    reason = _words_tail(word_eol, 3)
    if not reason:
        reason = "This channel is being closed. Please join {} instead.".format(
            redirect
        )
    fabulor.command("MODE {} +fpis {}".format(channel, redirect))
    fabulor.command("PRIVMSG OperServ :CLEARCHAN KICK {} {}".format(channel, reason))
    _print("Redirected {} to {}.".format(channel, redirect))
    return fabulor.EAT_ALL


_load_settings()
if not os.path.isfile(SETTINGS_FILE):
    _save_settings()

fabulor.hook_command("OPERBUDDY", on_operbuddy, help="OperBuddy settings and help")
fabulor.hook_command("GINVITE", on_ginvite, help="GINVITE <channel>")
fabulor.hook_command("REROUTE", on_reroute, help="REROUTE <server> <target-server>")
fabulor.hook_command(
    "CLOSECHAN", on_closechan, help="CLOSECHAN <channel> <redirect-channel> [reason]"
)
fabulor.hook_server("382", on_rehash)
fabulor.hook_server("WALLOPS", on_wallops)
fabulor.hook_server("216", on_stats_g)
fabulor.hook_server("709", on_global_invite_numeric)
fabulor.hook_server_attrs("NOTICE", on_snotice, priority=fabulor.PRI_HIGH)
if hasattr(fabulor, "hook_print_attrs"):
    fabulor.hook_print_attrs(
        "Open Dialog", on_open_dialog, priority=getattr(fabulor, "PRI_LOW", 0)
    )
else:
    fabulor.hook_print("Open Dialog", on_open_dialog)

_print("Loaded v{} by xnite.".format(__module_version__))
