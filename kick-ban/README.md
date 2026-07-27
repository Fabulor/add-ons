# Kick Ban

Tcl moderation helpers for banning and removing a user from the current
channel.

## Commands

- `/KB <nick> [reason]` bans the user's hostmask and kicks the user.
- `/KBN <nick> [reason]` bans the nickname as `<nick>!*@*` and kicks the user.

Each command supplies a default reason when none is given. The add-on also
refuses attempts to kick your own nickname.
