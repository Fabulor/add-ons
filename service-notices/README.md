# Service Notices

Redirects private notices from ChanServ and NickServ to a shared `Services` tab.

The tab is created when the first matching notice arrives and does not take
focus. Each connected IRC network has its own `Services` tab, and both services
share that tab within the network.

Notices sent directly to a channel and notices from other senders are left
unchanged. If the destination tab cannot be created, the original notice is
also left unchanged so it is not lost.
