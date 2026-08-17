# Uptime

Displays the current Windows system uptime from Fabulor.

## Command

`/UPTIME [auto|say|local]`

- `auto` and `say` send the uptime to the active channel.
- `local` displays the uptime only in Fabulor.
- When no channel is active, output remains local.

The add-on requests the local Windows uptime directly from Fabulor's trusted
simple Tcl API. It does not launch external processes or depend on PowerShell,
WMI/CIM, or the deprecated WMIC executable.
