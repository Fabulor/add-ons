# Fabulor-Name: AutoAuth
# Fabulor-Version: 1.0.0
# Fabulor-Description: Identifies with NickServ after a successful nick change

"""Identify with NickServ after changing to a registered nickname.

Passwords are stored per network with Windows DPAPI.  The encrypted data can
only be decrypted by the same Windows user on this computer.
"""

import base64
import ctypes
from ctypes import wintypes
import json
import os
import time

import fabulor

__module_name__ = "AutoAuth"
__module_version__ = "1.0.0"
__module_description__ = "Identifies with NickServ after a successful nick change"

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "autoauth.json")
_RECENT_IDENTIFIES = {}
_PENDING_IDENTIFIES = {}
_CONFIRMATION_TIMEOUT = 20

_SUCCESS_NOTICES = (
    "password accepted",
    "you are now identified",
    "you are now logged in",
    "you are now recognized",
    "you are identified",
    "already identified",
)
_FAILURE_NOTICES = (
    "invalid password",
    "incorrect password",
    "password incorrect",
    "authentication failed",
    "identify failed",
    "login failed",
    "you are not identified",
    "not registered",
)


class _DataBlob(ctypes.Structure):
    _fields_ = (("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte)))


_crypt32 = ctypes.windll.crypt32
_kernel32 = ctypes.windll.kernel32
_crypt32.CryptProtectData.argtypes = (
    ctypes.POINTER(_DataBlob),
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    ctypes.c_void_p,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(_DataBlob),
)
_crypt32.CryptProtectData.restype = wintypes.BOOL
_crypt32.CryptUnprotectData.argtypes = (
    ctypes.POINTER(_DataBlob),
    ctypes.POINTER(wintypes.LPWSTR),
    ctypes.POINTER(wintypes.LPWSTR),
    ctypes.c_void_p,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(_DataBlob),
)
_crypt32.CryptUnprotectData.restype = wintypes.BOOL
_kernel32.LocalFree.argtypes = (ctypes.c_void_p,)
_kernel32.LocalFree.restype = ctypes.c_void_p


def _print(message):
    fabulor.prnt("[AutoAuth] " + message)


def _last_error():
    return (
        ctypes.FormatError(ctypes.get_last_error()).strip() or "unknown Windows error"
    )


def _protect(plaintext):
    data = plaintext.encode("utf-8")
    buffer = ctypes.create_string_buffer(data, len(data))
    source = _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    encrypted = _DataBlob()
    if not _crypt32.CryptProtectData(
        ctypes.byref(source),
        "Fabulor AutoAuth",
        None,
        None,
        None,
        0,
        ctypes.byref(encrypted),
    ):
        raise OSError("Windows DPAPI could not encrypt the password: " + _last_error())
    try:
        return base64.b64encode(
            ctypes.string_at(encrypted.pbData, encrypted.cbData)
        ).decode("ascii")
    finally:
        _kernel32.LocalFree(encrypted.pbData)


def _unprotect(encoded):
    try:
        data = base64.b64decode(encoded.encode("ascii"), validate=True)
    except (AttributeError, ValueError) as error:
        raise ValueError("stored password is not valid encrypted data") from error
    if not data:
        raise ValueError("stored password is empty")

    buffer = ctypes.create_string_buffer(data, len(data))
    source = _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte)))
    plaintext = _DataBlob()
    if not _crypt32.CryptUnprotectData(
        ctypes.byref(source), None, None, None, None, 0, ctypes.byref(plaintext)
    ):
        raise OSError("Windows DPAPI could not decrypt the password: " + _last_error())
    try:
        return ctypes.string_at(plaintext.pbData, plaintext.cbData).decode("utf-8")
    finally:
        _kernel32.LocalFree(plaintext.pbData)


def _load_settings():
    if not os.path.isfile(SETTINGS_FILE):
        return {"version": 1, "networks": {}}
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as handle:
            settings = json.load(handle)
        if not isinstance(settings, dict) or not isinstance(
            settings.get("networks"), dict
        ):
            raise ValueError("the settings file has an invalid format")
        return settings
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        _print("Could not load settings: {}".format(error))
        return {"version": 1, "networks": {}}


def _save_settings():
    temporary = SETTINGS_FILE + ".tmp"
    try:
        with open(temporary, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(_settings, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, SETTINGS_FILE)
        return True
    except OSError as error:
        try:
            os.remove(temporary)
        except OSError:
            # Best-effort cleanup: if removing the temporary file fails,
            # keep reporting the original save error without overriding it.
            pass
        _print("Could not save settings: {}".format(error))
        return False


def _network():
    name = fabulor.get_info("network") or fabulor.get_info("server")
    if not name:
        return None, None
    return name.casefold(), name


def _command_tail(words, word_eol):
    if word_eol and word_eol[0]:
        raw = word_eol[0].strip()
        if raw.upper().startswith("AUTOAUTH") and (len(raw) == 8 or raw[8].isspace()):
            return raw[8:].lstrip()
    return " ".join(words[1:])


def _help():
    _print("Usage: /AUTOAUTH SET <password> | CLEAR | ON | OFF | STATUS")
    _print("SET encrypts a password for this network with your Windows account.")


def _show_status():
    key, display = _network()
    if key is None:
        _print("Use this command in a connected network context.")
        return
    entry = _settings["networks"].get(key)
    if entry and entry.get("password"):
        state = "enabled" if entry.get("enabled", True) else "disabled"
        _print("Auto-authentication is {} for {}.".format(state, display))
    else:
        _print("No password is stored for {}.".format(display))


def on_autoauth_command(words, word_eol, userdata):
    del userdata
    tail = _command_tail(words, word_eol)
    parts = tail.split(None, 1)
    action = parts[0].upper() if parts else "STATUS"
    key, display = _network()

    if action == "HELP":
        _help()
    elif key is None:
        _print("Use this command in a connected network context.")
    elif action == "STATUS":
        _show_status()
    elif action == "SET" and len(parts) == 2 and parts[1]:
        password = parts[1]
        if "\r" in password or "\n" in password:
            _print("Passwords containing line breaks are not supported.")
        else:
            try:
                encrypted = _protect(password)
            except OSError as error:
                _print(str(error))
            else:
                _settings["networks"][key] = {"enabled": True, "password": encrypted}
                if _save_settings():
                    _print(
                        "Encrypted password saved; auto-authentication enabled for {}.".format(
                            display
                        )
                    )
    elif action == "CLEAR":
        if _settings["networks"].pop(key, None) is None:
            _print("No password is stored for {}.".format(display))
        elif _save_settings():
            _print("Stored encrypted password removed for {}.".format(display))
    elif action in ("ON", "OFF"):
        entry = _settings["networks"].get(key)
        if not entry or not entry.get("password"):
            _print("Set a password first with /AUTOAUTH SET <password>.")
        else:
            entry["enabled"] = action == "ON"
            if _save_settings():
                _print("Auto-authentication {} for {}.".format(action.lower(), display))
    else:
        _help()
    return fabulor.EAT_ALL


def _identify_after_nick_change(new_nick):
    key, _display = _network()
    if key is None:
        return fabulor.EAT_NONE
    entry = _settings["networks"].get(key)
    if not entry or not entry.get("enabled", True) or not entry.get("password"):
        return fabulor.EAT_NONE

    new_nick = new_nick.lstrip(":")
    current_nick = fabulor.get_info("nick")
    if not new_nick or not current_nick or fabulor.nickcmp(new_nick, current_nick) != 0:
        return fabulor.EAT_NONE

    marker = (key, current_nick.casefold())
    now = time.monotonic()
    if now - _RECENT_IDENTIFIES.get(marker, 0) < 2:
        return fabulor.EAT_NONE
    try:
        password = _unprotect(entry["password"])
    except (OSError, UnicodeDecodeError, ValueError) as error:
        _print(
            "Cannot decrypt the password for this network: {}. Use /AUTOAUTH SET to replace it.".format(
                error
            )
        )
        return fabulor.EAT_NONE

    _RECENT_IDENTIFIES[marker] = now
    _PENDING_IDENTIFIES[key] = now
    fabulor.command("NickServ IDENTIFY " + password)
    return fabulor.EAT_NONE


def on_nick_change(words, word_eol, userdata):
    """Handle the raw IRC NICK message: :old!user@host NICK :new."""
    del word_eol, userdata
    if len(words) < 3:
        return fabulor.EAT_NONE
    return _identify_after_nick_change(words[2])


def on_change_nick_print(words, word_eol, userdata, attributes=None):
    """Handle Fabulor's displayed Change Nick event: old-nick, new-nick."""
    del word_eol, userdata, attributes
    if len(words) < 2:
        return fabulor.EAT_NONE
    return _identify_after_nick_change(words[1])


def on_nickserv_notice(words, word_eol, userdata, attributes):
    """Report a NickServ result for an identification initiated by this add-on."""
    del word_eol, userdata, attributes
    if len(words) < 4:
        return fabulor.EAT_NONE
    key, _display = _network()
    started = _PENDING_IDENTIFIES.get(key)
    if key is None or started is None:
        return fabulor.EAT_NONE
    if time.monotonic() - started > _CONFIRMATION_TIMEOUT:
        del _PENDING_IDENTIFIES[key]
        return fabulor.EAT_NONE

    sender = words[0].lstrip(":").split("!", 1)[0]
    if not sender or fabulor.nickcmp(sender, "NickServ") != 0:
        return fabulor.EAT_NONE
    notice = " ".join(words[3:]).lstrip(":").casefold()
    if any(phrase in notice for phrase in _FAILURE_NOTICES):
        del _PENDING_IDENTIFIES[key]
        _print("NickServ authentication failed.")
    elif any(phrase in notice for phrase in _SUCCESS_NOTICES):
        del _PENDING_IDENTIFIES[key]
        _print("NickServ authentication succeeded.")
    return fabulor.EAT_NONE


_settings = _load_settings()
fabulor.hook_command(
    "AUTOAUTH",
    on_autoauth_command,
    help="Manage encrypted NickServ auto-authentication; use /AUTOAUTH HELP",
)
fabulor.hook_server("NICK", on_nick_change)
if hasattr(fabulor, "hook_print_attrs"):
    fabulor.hook_print_attrs(
        "Change Nick", on_change_nick_print, priority=getattr(fabulor, "PRI_LOW", 0)
    )
fabulor.hook_server_attrs("NOTICE", on_nickserv_notice, priority=fabulor.PRI_LOW)
_print("Loaded. Use /AUTOAUTH SET <password> in each network you want to enable.")
