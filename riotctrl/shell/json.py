"""
JSON parser for riotctrl shell interactions
"""

import json

from . import ShellInteractionParser


# pylint: disable=too-few-public-methods
class JSONShellInteractionParser(ShellInteractionParser):
    """Allows for parsing result strings of a ShellInteraction as JSON"""

    def parse(self, cmd_output):
        """
        Parse cmd_output as JSON

        :param cmd_output (str): Output of ShellInteraction::cmd(). Must be
                                 valid JSON
        """
        return json.loads(cmd_output)
