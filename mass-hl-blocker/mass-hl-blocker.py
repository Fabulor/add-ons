# Fabulor-Name: Mass HL Blocker
# Fabulor-Version: 1.0.0
# Fabulor-Description: Suppresses mass-highlight notifications without hiding messages
# Adapted from mass_hl_blocker.pl by arza <arza@arza.us>; GPL-3.0.

"""Suppress highlight notifications for messages mentioning many channel users."""

import fabulor

__module_name__ = "Mass HL Blocker"
__module_version__ = "1.0.0"
__module_description__ = (
    "Suppresses mass-highlight notifications without hiding messages"
)

_DEFAULT_LIMIT = 5
_MEMBERSHIP_PREFIXES = "~&@%+"
_limit = _DEFAULT_LIMIT


def _print(message):
    fabulor.prnt("[Mass HL Blocker] " + message)


def _load_limit():
    saved = fabulor.get_pluginpref("limit")
    if saved is None:
        if not fabulor.set_pluginpref("limit", _DEFAULT_LIMIT):
            _print("Could not save the default threshold.")
        return _DEFAULT_LIMIT

    try:
        limit = int(saved)
    except (TypeError, ValueError):
        limit = 0

    if limit < 1:
        _print(
            "Ignoring invalid saved threshold {!r}; using {}.".format(
                saved, _DEFAULT_LIMIT
            )
        )
        return _DEFAULT_LIMIT

    return limit


def _count_nick_mentions(message, nicknames):
    count = 0
    for token in message.split():
        if token.startswith(tuple(_MEMBERSHIP_PREFIXES)):
            token = token[1:]
        if token and any(fabulor.nickcmp(token, nick) == 0 for nick in nicknames):
            count += 1
    return count


def _on_highlight(words, word_eol, userdata, attributes):
    del word_eol, userdata
    if len(words) < 2:
        return fabulor.EAT_NONE

    message = words[1]
    own_nick = fabulor.get_info("nick")
    if not own_nick or own_nick not in message:
        return fabulor.EAT_NONE

    users = fabulor.get_list("users")
    if not users:
        return fabulor.EAT_NONE

    nicknames = [user.nick for user in users if user.nick]
    if _count_nick_mentions(message, nicknames) < _limit:
        return fabulor.EAT_NONE

    fabulor.emit_print(
        "Channel Message",
        *words,
        time=getattr(attributes, "time", 0),
    )
    return fabulor.EAT_ALL


def _on_command(words, word_eol, userdata):
    del word_eol, userdata
    global _limit

    args = words[1:]
    if not args:
        _print("Current threshold: {} nick mentions.".format(_limit))
        return fabulor.EAT_ALL

    if len(args) != 1 or not args[0].isascii() or not args[0].isdigit():
        _print("Usage: /MASSHLBLOCKER [positive-integer]")
        return fabulor.EAT_ALL

    new_limit = int(args[0])
    if new_limit < 1:
        _print("The threshold must be at least 1.")
        return fabulor.EAT_ALL

    if not fabulor.set_pluginpref("limit", new_limit):
        _print("Could not save the threshold; it was not changed.")
        return fabulor.EAT_ALL

    _limit = new_limit
    _print("Threshold set to {} nick mentions.".format(_limit))
    return fabulor.EAT_ALL


_limit = _load_limit()
fabulor.hook_print_attrs(
    "Channel Msg Hilight",
    _on_highlight,
    priority=fabulor.PRI_HIGH,
)
fabulor.hook_command(
    "MASSHLBLOCKER",
    _on_command,
    help="Show or set the mass-highlight threshold",
)
_print("Loaded. Use /MASSHLBLOCKER to view or change the threshold.")
