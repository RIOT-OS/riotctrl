"""
JSON parser for riotctrl shell interactions
"""

import json
import logging
try:
    import rapidjson
except ImportError:
    rapidjson = None

from . import ShellInteractionParser


# pylint: disable=too-few-public-methods
class JSONShellInteractionParser(ShellInteractionParser):
    """Allows for parsing result strings of a ShellInteraction as JSON"""
    json_module = json

    def parse(self, cmd_output):
        """
        Parse cmd_output as JSON

        :param cmd_output (str): Output of ShellInteraction::cmd(). Must be
                                 valid JSON
        """
        return self.json_module.loads(cmd_output)


class RapidJSONShellInteractionParser(JSONShellInteractionParser):
    """Allows for parsing result strings of a ShellInteraction as JSON using
    rapidjson_. RIOTCtrl can be installed with ``rapidjson`` support using
    ``riotctrl[rapidjson]``.

    .. _rapidjson: https://rapidjson.org/
    """
    json_module = rapidjson

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(type(self).__name__)
        self._parser_args = {}
        self._parser_kwargs = {}
        if self.json_module is None:
            self.logger.warning("%s initialized without rapidjson installed\n"
                                "Please install with riotctrl[rapidjson]",
                                type(self).__name__)
        super().__init__(*args, **kwargs)

    def set_parser_args(self, *args, **kwargs):
        """Set arguments for ``loads`` function of the JSON module

        E.g.

        ::
            parser.set_parser_args(parse_mode=rapidjson.PM_TRAILING_COMMAS)
        """
        self._parser_args = args
        self._parser_kwargs = kwargs

    def parse(self, cmd_output):
        """Parse cmd_output as JSON using rapidjson_

        .. _rapidjson: https://rapidjson.org/

        :param cmd_output (str): Output of ShellInteraction::cmd(). Must be
                                 valid JSON
        """
        return self.json_module.loads(cmd_output, *self._parser_args,
                                      **self._parser_kwargs)
