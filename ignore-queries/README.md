# Ignore Queries

Suppresses unwanted private messages with separate settings and whitelists for
each IRC network.

## Commands

- `/IGNOREQUERIES ON|OFF|TOGGLE|STATUS` controls the add-on for the current
  network.
- `/IGNOREQUERIES WHITELIST ADD <nick>` allows a nickname to message you.
- `/IGNOREQUERIES WHITELIST REMOVE <nick>` removes a nickname.
- `/IGNOREQUERIES WHITELIST LIST` displays the current network's whitelist.

The same controls are available under **Settings > Ignore Queries**. Settings
and whitelists are saved beside the add-on in `settings.json` and
`whitelist.json`.

When enabled, the add-on suppresses non-whitelisted private messages and sends
the sender a short notice. Repeat notices to the same nickname are limited to
one every 30 minutes.
