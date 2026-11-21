# Fabulor-Name: Whois
# Fabulor-Version: 1.0.0
# Fabulor-Description: Route WHOIS output to a network-specific tab

"""Route Fabulor's formatted WHOIS events to a tab on the same connection."""

import time

import fabulor

__module_name__ = "Whois"
__module_version__ = "1.0.0"
__module_description__ = "Route WHOIS output to a network-specific tab"

_TAB_NAME = "Whois"
_DIALOG_TYPE = 3
_REQUEST_TIMEOUT = 60
_WHOIS_EVENTS = (
    "WhoIs Authenticated",
    "WhoIs Away Line",
    "WhoIs Channel/Oper Line",
    "WhoIs End",
    "WhoIs Identified",
    "WhoIs Idle Line",
    "WhoIs Idle Line with Signon",
    "WhoIs Name Line",
    "WhoIs Real Host",
    "WhoIs Server Line",
    "WhoIs Special",
)
_active = {}
_pending = {}
_emitting = False
_reported_failures = set()


def _connection_id():
    return fabulor.get_info("id")


def _same_nick(left, right):
    return fabulor.nickcmp(left, right) == 0


def _destination(connection_id):
    def find():
        for item in fabulor.get_list("channels") or []:
            if (str(item.id) == connection_id and item.type == _DIALOG_TYPE
                    and _same_nick(item.channel, _TAB_NAME)):
                return item.context
        return None

    context = find()
    if context is None:
        fabulor.command("QUERY -nofocus " + _TAB_NAME)
        context = find()
    return context


def _route(event, words, attributes):
    global _emitting
    connection_id = _connection_id()
    if not connection_id:
        fabulor.prnt("[Whois] Cannot identify the connection; original output retained.")
        return fabulor.EAT_NONE

    try:
        context = _destination(connection_id)
        if context is None:
            raise RuntimeError("could not create the Whois tab")
        if context == fabulor.get_context():
            return fabulor.EAT_NONE
        _emitting = True
        try:
            result = context.emit_print(event, *words, time=attributes.time)
        finally:
            _emitting = False
        if not result:
            raise RuntimeError("could not emit the WHOIS event")
    except (AttributeError, NameError, PermissionError, RuntimeError, TypeError) as exc:
        if connection_id not in _reported_failures:
            fabulor.prnt("[Whois] Routing failed ({}); original output retained.".format(exc))
            _reported_failures.add(connection_id)
        return fabulor.EAT_NONE

    _reported_failures.discard(connection_id)
    return fabulor.EAT_ALL


def _on_whois_command(words, word_eol, userdata):
    del word_eol, userdata
    connection_id = _connection_id()
    if connection_id and len(words) > 1:
        now = time.monotonic()
        requests = [(nick, deadline) for nick, deadline in _pending.get(connection_id, [])
                    if deadline > now]
        requests.extend((nick, now + _REQUEST_TIMEOUT)
                        for nick in words[-1].split(",") if nick)
        _pending[connection_id] = requests
    return fabulor.EAT_NONE


def _on_numeric(words, word_eol, userdata):
    del word_eol
    connection_id = _connection_id()
    if not connection_id or len(words) < 4:
        return fabulor.EAT_NONE
    nick = words[3]
    if userdata == "311":
        _active.setdefault(connection_id, []).append(nick)
    else:
        _active[connection_id] = [item for item in _active.get(connection_id, [])
                                  if not _same_nick(item, nick)]
        _pending[connection_id] = [(item, deadline)
                                   for item, deadline in _pending.get(connection_id, [])
                                   if not _same_nick(item, nick)]
    return fabulor.EAT_NONE


def _on_print(words, word_eol, event, attributes):
    del word_eol
    if _emitting:
        return fabulor.EAT_NONE
    if event in ("WhoIs Away Line", "WhoIs Name Line"):
        connection_id = _connection_id()
        if not words or not any(_same_nick(words[0], nick)
                                for nick in _active.get(connection_id, [])):
            return fabulor.EAT_NONE
    return _route(event, words, attributes)


def _on_server_text(words, word_eol, userdata, attributes):
    del word_eol, userdata
    if _emitting or len(words) < 3 or words[2] != "401":
        return fabulor.EAT_NONE
    connection_id = _connection_id()
    now = time.monotonic()
    requests = [(nick, deadline) for nick, deadline in _pending.get(connection_id, [])
                if deadline > now]
    _pending[connection_id] = requests
    target = words[0].split(" ", 1)[0]
    if not any(_same_nick(target, nick) for nick, _ in requests):
        return fabulor.EAT_NONE
    return _route("Server Text", words, attributes)


def _on_disconnect(words, word_eol, userdata):
    del words, word_eol, userdata
    connection_id = _connection_id()
    _active.pop(connection_id, None)
    _pending.pop(connection_id, None)
    _reported_failures.discard(connection_id)
    return fabulor.EAT_NONE


for _event in _WHOIS_EVENTS:
    fabulor.hook_print_attrs(_event, _on_print, _event, priority=fabulor.PRI_HIGH)
fabulor.hook_print_attrs("Server Text", _on_server_text, priority=fabulor.PRI_HIGH)
fabulor.hook_print("Disconnected", _on_disconnect)
fabulor.hook_command("WHOIS", _on_whois_command)
for _numeric in ("311", "318"):
    fabulor.hook_server(_numeric, _on_numeric, _numeric)
