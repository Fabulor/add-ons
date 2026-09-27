# OperBuddy

OperBuddy provides IRC operator commands and routes selected server notices
into dedicated query tabs. It is written for Fabulor's Python add-on API and
was originally tested against Charybdis; command and numeric behavior can vary
between IRC daemons and services packages.

## Commands

| Command | Description |
| --- | --- |
| `/OPERBUDDY` | Show command help. |
| `/OPERBUDDY SETTINGS` | Display the current settings. |
| `/OPERBUDDY SET <setting> <value>` | Change a setting. Boolean settings accept `0` or `1`. |
| `/GINVITE <channel>` | Start a `MASKTRACE` and invite matching users to the channel as numeric `709` replies arrive. |
| `/REROUTE <server> <target-server>` | Disconnect a server and reconnect it through the target server. |
| `/CLOSECHAN <channel> <redirect-channel> [reason]` | Set the redirect mode and ask OperServ to kick channel members. |

## Settings

Settings are saved to `settings.json` beside the add-on.

| Setting | Default | Description |
| --- | --- | --- |
| `whois_on_query` | `1` | Request WHOIS when a new query opens. |
| `use_away_message` | `1` | Send the configured away reply when opening a query while away. |
| `away_message` | A help-oriented auto-reply | Text sent by the away reply feature. |
| `show_full_server_name` | `0` | Show the full server name in the SNOTICE tab instead of only its first hostname component. |
| `global_invite` | `0` | Enable processing of `709` replies for the most recently requested global invite. `/GINVITE` enables this automatically. |
| `netsplit_audio_file` | Empty | Optional audio file played for netsplit notices using Fabulor's `SPLAY` command. |

Examples:

```text
/OPERBUDDY SET whois_on_query 0
/OPERBUDDY SET away_message I am away; please ask in #help
/OPERBUDDY SET netsplit_audio_file C:\sounds\netsplit.wav
```

## Notice Tabs

The add-on creates these tabs as needed:

- `OpBud:WALLOPS` for WALLOPS messages.
- `OpBud:Links` for netsplit, split, and netjoin notices.
- `OpBud:Clients` for client connect, exit, and DNSBL notices.
- `OpBud:SNotice` for other server notices.
- `OpBud:Bans` for numeric `216` global K-line details.

Numeric `382` rehash messages are printed in the current context. Some IRCd or
services implementations may use different message formats, numeric replies,
or channel redirect modes; verify `/CLOSECHAN`, `/REROUTE`, and `/GINVITE` on
your network before using them operationally.
