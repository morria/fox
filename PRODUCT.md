# Fox BBS

This program is a BBS used for "fox hunting".

It connects to direwolf (via TCP port 8000) as the TNC and accepts AX.25
connections. Users get a tiny banner announcing the SSID of the BBS
(which is configured on config/fox.yaml) and then drops them into a group
chat. They receive up to the last 15 messages from the last 24 hours upon
connecting and then are given a prompt (`{ssid}> `) through which they may
post messages to the chat. When any other connected client posts a message it
will be distributed to all connected clients and then they will be given a
prompt again.

## Stack

The software will be written in Python3 and will run in a virtual environment.
It will connect to Direwolf running on port 8000 (AGWPE protocol) of localhost.
It will be highly pythonic code with a very standard and predictable layout.
