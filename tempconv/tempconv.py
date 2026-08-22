# Fabulor-Name: Temp Convert
# Fabulor-Version: 1.0.0
# Fabulor-Description: Convert temperatures between Celsius, Fahrenheit, Kelvin, and Rankine

"""Convert temperatures locally between Celsius, Fahrenheit, Kelvin, and Rankine.

Python port of the original Perl add-on by LifeIsPain
<idontlikespam (at) orvp [dot] net>.
"""

import re

import fabulor

__module_name__ = "Temp Convert"
__module_version__ = "1.0.0"
__module_description__ = (
    "Convert temperatures between Celsius, Fahrenheit, Kelvin, and Rankine"
)

_TEMPERATURE_RE = re.compile(
    r"^\s*(-?(?:\d+(?:\.\d*)?|\.\d+))\s*([CKFR])\s*(?:(?:TO|IN)\s*)?([CKFR])\s*$",
    re.IGNORECASE,
)


def _command_tail(words, word_eol):
    if word_eol and word_eol[0]:
        raw = word_eol[0].strip()
        if raw.upper().startswith("TEMPCONV") and (
            len(raw) == len("TEMPCONV") or raw[len("TEMPCONV")].isspace()
        ):
            return raw[len("TEMPCONV") :].lstrip()
    return " ".join(words[1:])


def _to_kelvin(value, scale):
    if scale == "C":
        return value + 273.15
    if scale == "F":
        return (value + 459.67) * 5 / 9
    if scale == "R":
        return value * 5 / 9
    return value


def _from_kelvin(value, scale):
    if scale == "C":
        return value - 273.15
    if scale == "F":
        return value * 9 / 5 - 459.67
    if scale == "R":
        return value * 9 / 5
    return value


def on_tempconv_command(words, word_eol, userdata):
    del userdata
    match = _TEMPERATURE_RE.fullmatch(_command_tail(words, word_eol))
    if match is None:
        fabulor.prnt("Usage: /TEMPCONV <temperature>[C|K|F|R] [TO|IN] [C|K|F|R]")
        return fabulor.EAT_ALL

    value = float(match.group(1))
    source = match.group(2).upper()
    target = match.group(3).upper()
    converted = _from_kelvin(_to_kelvin(value, source), target)
    fabulor.prnt(f"{value:.4g}{source} = {converted:.4g}{target}")
    return fabulor.EAT_ALL


fabulor.hook_command(
    "TEMPCONV",
    on_tempconv_command,
    help="Convert temperatures; use /TEMPCONV 32F TO C",
)
