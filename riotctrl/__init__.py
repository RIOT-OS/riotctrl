"""RIOT Ctrl abstraction.

This prodives python object abstraction of a RIOT node.
The first goal is to be the starting point for the serial abstraction and
build on top of that to provide higher level abstraction like over the shell.

It could provide an RPC interface to a node in Python over the serial port
and maybe also over network.
"""

__version__ = '0.1.1'
