# Whois

Routes Fabulor's formatted WHOIS replies to a `Whois` tab on the same
connection. The tab is created without taking focus and is shared by WHOIS
requests on that connection; separate connections have separate tabs. An
existing query named `Whois` on that connection is reused, so its messages
will share the tab.

The add-on preserves Fabulor's event formatting and server timestamps. Normal
away messages and WHOWAS name lines are not redirected. A "no such nick"
response to `/WHOIS` is also routed when it can be associated with a recent
request. Ambiguous errors and other output that cannot be associated with a
WHOIS remain in their normal location.

IRCv3 bot status (335) and draft WHOIS metadata (760) are routed when Fabulor
formats them as WHOIS special lines, or as server text associated with a
recent or active WHOIS for the same nickname. Metadata capability negotiation
is handled by the client; this add-on does not request it.

If the tab cannot be created or output cannot be rendered, the original output
remains visible and a routing error is reported.
