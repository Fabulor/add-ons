# Mass HL Blocker

Mass HL Blocker suppresses highlight notifications for channel messages that
contain at least five channel-nickname mentions by default. It leaves the
message visible as an ordinary channel message.

The threshold is configurable and persists across restarts:

- `/MASSHLBLOCKER` shows the current threshold.
- `/MASSHLBLOCKER 8` sets it to eight nick mentions.

The matcher follows the Perl reference: it checks whitespace-separated words
against the current channel's nick list, removes one leading membership prefix
(`~&@%+`), and counts repeated mentions separately. It only handles messages
Fabulor has already classified as highlighted and that contain the current
nickname.

Fabulor's print-event API does not expose WeeChat message tags, so the Python
version reproduces the visible behavior by replacing the highlighted print
event with an ordinary channel-message event; it does not add the Perl
script's `mass_hl` tag.

The implementation is adapted from [mass_hl_blocker.pl](mass_hl_blocker.pl),
originally by arza and distributed under GPL-3.0.
