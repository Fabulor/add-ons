# Whois

Routes Fabulor's formatted WHOIS replies to a `Whois` tab on the same
connection. The tab is created without taking focus and is shared by WHOIS
requests on that connection; separate connections have separate tabs. An
existing query named `Whois` on that connection is reused, so its messages
will share the tab.

The add-on preserves Fabulor's event formatting and server timestamps. Normal
away messages and WHOWAS name lines are not redirected. A "no such nick"
response to `/WHOIS` is also routed when it can be associated with a recent
request. Ambiguous errors and output that Fabulor does not identify as WHOIS
remain in their normal location.

If the tab cannot be created or output cannot be rendered, the original output
remains visible and a routing error is reported.
