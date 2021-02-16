"""
Shell interaction extension for riotctrl

Defines classes to abstract interactions with RIOT shell commands
"""

import abc

import pexpect
import pexpect.replwrap


# pylint: disable=R0903
class ShellInteractionParser(abc.ABC):
    """Allows parsing of the result string of a ShellInteraction"""

    @abc.abstractmethod
    def parse(self, cmd_output):
        """
        Abstract parse method. Must be extended for a specific command

        :param  cmd_output (str): Output of ShellInteraction::cmd()
        """


class ShellInteraction():
    """
    Base class for shell interactions

    :param riotctrl: a RIOTCtrl object
    :param prompt: the prompt of the shell (default: '> ')
    """
    PROMPT_TIMEOUT = .5

    def __init__(self, riotctrl, prompt='> '):
        self.riotctrl = riotctrl
        self.prompt = prompt
        self.replwrap = None
        self.term_was_started = False

    def __del__(self):
        if self.term_was_started:
            self.stop_term()

    def _start_replwrap(self):
        if self.replwrap is None or self.replwrap.child != self.riotctrl.term:
            # consume potentially shown prompt to be on the same ground as if
            # it is not shown
            self.riotctrl.term.expect_exact([self.prompt, pexpect.TIMEOUT],
                                            timeout=self.PROMPT_TIMEOUT)
            # enforce prompt to be shown by sending newline
            self.riotctrl.term.sendline("")
            self.replwrap = pexpect.replwrap.REPLWrapper(
                self.riotctrl.term,
                orig_prompt=self.prompt,
                prompt_change=None,
            )

    def start_term(self):
        """
        Starts the terminal of the RIOTCtrl object
        """
        self.term_was_started = True
        self.riotctrl.start_term()

    def stop_term(self):
        """
        Stops the terminal of the RIOTCtrl object
        """
        self.riotctrl.stop_term()

    @staticmethod
    def check_term(func, reset=True, **startkwargs):
        """
        Decorator to ensure the terminal is running and stopped
        """
        def wrapper(self, *args, **kwargs):
            if self.riotctrl.term is None:
                with self.riotctrl.run_term(reset, **startkwargs):
                    return func(self, *args, **kwargs)
            return func(self, *args, **kwargs)

        return wrapper

    def cmd(self, cmd, timeout=-1, async_=False):
        """
        Sends a command via the ShellInteraction's `riotctrl`

        :param  cmd: A shell command as string.

        :return: Output of the command as a string
        """
        self._start_replwrap()
        return self.replwrap.run_command(cmd, timeout=timeout, async_=async_)
