# Uptime

Displays the current Windows system uptime from Fabulor.

## Command

`/UPTIME [auto|say|local]`

- `auto` and `say` send the uptime to the active channel.
- `local` displays the uptime only in Fabulor.
- When no channel is active, output remains local.

The add-on queries Windows through PowerShell, PowerShell 7, or WMIC, using the
first available method.
