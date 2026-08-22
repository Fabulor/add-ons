# Alias

Alias creates persistent custom commands without editing Fabulor's **Settings >
User Commands** list. An alias can run one command or a sequence of commands.

## Commands

| Command | Description |
| --- | --- |
| `/ALIAS <name> <command>` | Create or replace an alias. Separate multiple commands with semicolons. |
| `/UNALIAS <name>` | Remove an alias. |
| `/ALIASES` | List all saved aliases and their commands. |

Aliases are saved in Fabulor's add-on preferences and restored whenever the
add-on loads.

## Placeholders

| Placeholder | Value |
| --- | --- |
| `%1`, `%2`, ... | The corresponding individual argument passed to the alias. |
| `%&1`, `%&2`, ... | All arguments from that position onward. |
| `%a` | Nicknames selected in the current user list. |
| `%c` | Current channel. |
| `%e` | Current network. |
| `%m` | Machine information, including the operating system and processor. |
| `%n` | Your current nickname. |
| `%t` | Current local date and time. |
| `%v` | Fabulor client version. |

Unknown placeholders are left unchanged. A placeholder whose argument does not
exist expands to an empty string.

## Examples

Create `/J` as a shorter join command:

```text
/ALIAS J JOIN %1
```

Create `/GREET` to send the entire supplied message to the current channel:

```text
/ALIAS GREET MSG %c Hello %&1
```

Run several commands with one alias:

```text
/ALIAS SETUP JOIN #fabulor; MSG #fabulor Hello from %n
```

## Installation

Place `alias.py` in `%APPDATA%\Fabulor\addons\alias\`, then load or reload the
add-on in Fabulor.
