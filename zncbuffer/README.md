# ZNC Buffers

Adds a **ZNC Buffers** menu with **Clear Buffer** and **Play Buffer** actions.
The actions apply to the currently selected tab. `/ZNCBUFFER CLEAR` and
`/ZNCBUFFER PLAY` provide the same actions from the command line.

After clearing a buffer, the add-on suppresses the matching confirmation from
ZNC's `*status` query so the confirmation does not clutter the channel.
`*`-prefixed tabs are ignored. The ZNC `clearbuffer` and `playbuffer` commands
must be available on the current connection.
