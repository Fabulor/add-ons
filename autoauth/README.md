# AutoAuth

AutoAuth identifies with NickServ automatically after you successfully change
to a nickname. It deliberately invokes `NickServ` by name, so it does not need
network-specific NickServ hostnames or configuration.

## Setup

In each network where you want auto-authentication, run:

```
/AUTOAUTH SET your-account-password
```

The add-on immediately encrypts the password and enables itself for that
network. Change to a registered nickname to authenticate.

## Commands

| Command | Description |
| --- | --- |
| `/AUTOAUTH SET <password>` | Encrypt and save the password for the current network, then enable AutoAuth. |
| `/AUTOAUTH STATUS` | Show whether a password is configured and whether AutoAuth is enabled. |
| `/AUTOAUTH ON` | Enable AutoAuth for the current network. |
| `/AUTOAUTH OFF` | Disable AutoAuth without removing the saved password. |
| `/AUTOAUTH CLEAR` | Remove the saved encrypted password for the current network. |
| `/AUTOAUTH HELP` | Show command usage. |

## Security

Passwords are saved in `autoauth.json` in this folder as Windows DPAPI-encrypted
data. The encrypted value can only be decrypted by the same Windows user on the
same PC that created it; it is not portable to another user account or computer.

The password is sent to the connected IRC network when AutoAuth invokes
`NickServ IDENTIFY`. Use a TLS-enabled IRC connection.

`/AUTOAUTH SET <password>` may be retained in Fabulor's local command history.
Clear that history after setup if Fabulor records sensitive commands.

## Behaviour

AutoAuth watches Fabulor's confirmed nick-change events, verifies that the new
nickname is your current nickname, then runs:

```
/NickServ IDENTIFY <your password>
```

It only acts when a password is configured and AutoAuth is enabled for the
current network.

After it sends the identify command, AutoAuth displays a local success or
failure message when it receives a recognised NickServ confirmation notice.
