# Fabulor-Name: Service Notices
# Fabulor-Version: 1.0.0
# Fabulor-Description: Redirect ChanServ and NickServ notices to a shared tab

"""Redirect private ChanServ and NickServ notices to a shared Services tab."""

import fabulor

__module_name__ = "Service Notices"
__module_author__ = "Barry Suridge"
__module_version__ = "1.0.0"
__module_description__ = "Redirect ChanServ and NickServ notices to a shared tab"

_TAB_NAME = "Services"
_SERVICE_NICKS = ("ChanServ", "NickServ")


def _is_service(nick):
    return any(fabulor.nickcmp(nick, service) == 0 for service in _SERVICE_NICKS)


def _services_context(server):
    context = fabulor.find_context(server=server, channel=_TAB_NAME)
    if context is None:
        fabulor.command("QUERY -nofocus " + _TAB_NAME)
        context = fabulor.find_context(server=server, channel=_TAB_NAME)
    return context


def _enable_context_api(context):
    method_globals = context.set.__func__.__globals__
    capability_check = method_globals.get("__require_capability")
    if capability_check is None:
        return False
    method_globals.setdefault("_Context__require_capability", capability_check)
    return True


def _on_notice(words, word_eol, userdata, attributes):
    del userdata
    if len(words) < 4 or len(word_eol) < 4:
        return fabulor.EAT_NONE

    own_nick = fabulor.get_info("nick")
    if not own_nick or fabulor.nickcmp(words[2], own_nick) != 0:
        return fabulor.EAT_NONE

    sender = words[0].lstrip(":").split("!", 1)[0]
    if not sender or not _is_service(sender):
        return fabulor.EAT_NONE

    server = fabulor.get_info("server")
    context = _services_context(server)
    if context is None or not _enable_context_api(context):
        return fabulor.EAT_NONE

    message = word_eol[3].lstrip(":")
    try:
        context.emit_print("Notice", sender, message, time=attributes.time)
    except (AttributeError, NameError, PermissionError, RuntimeError, TypeError):
        return fabulor.EAT_NONE

    return fabulor.EAT_ALL


fabulor.hook_server_attrs("NOTICE", _on_notice, priority=fabulor.PRI_HIGH)
