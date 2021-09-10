"""
Shell interaction extenison for riotctrl.multictrl

Defines classes to abstract interactions with RIOT shell commands using
riotctrl.multictrl.MultiRIOTCtrl objects
"""

import pexpect

import riotctrl.shell
import riotctrl.multictrl.ctrl

from riotctrl.multictrl.ctrl import MultiKeyDict


class MultiShellInteractionMixin(riotctrl.shell.ShellInteraction):
    """
    Mixin class for shell interactions of riotctrl.multictrl.ctrl.MultiRIOTCtrl

    :param ctrl: a MultiRIOTCtrl object
    """
    # pylint: disable=super-init-not-called
    # intentionally do not call super-init, to not cause TypeError
    def __init__(self, ctrl):
        # used in __del__, so initialize before raising exception
        self.term_was_started = False
        if not isinstance(ctrl, riotctrl.multictrl.ctrl.MultiRIOTCtrl):
            raise TypeError(
                "{} not compatible with non multi-RIOTCtrl {}. Use {} instead."
                .format(type(self), type(ctrl),
                        riotctrl.shell.ShellInteraction)
            )
        self.riotctrl = ctrl
        self.replwrap = MultiKeyDict()

    def _start_replwrap(self):
        if not self.replwrap or \
           (any(key not in self.replwrap for key in self.riotctrl) and
            any(self.replwrap[key].child != self.riotctrl[key].term
                for key in self.riotctrl)):
            for key, ctrl in self.riotctrl.items():
                # consume potentially shown prompt to be on the same ground as
                # if it is not shown
                ctrl.term.expect_exact(["> ", pexpect.TIMEOUT], timeout=.1)
                # enforce prompt to be shown by sending newline
                ctrl.term.sendline("")
                self.replwrap[key] = pexpect.replwrap.REPLWrapper(
                    ctrl.term, orig_prompt="> ", prompt_change=None,
                )

    # pylint: disable=arguments-differ
    def cmd(self, cmd, timeout=-1, async_=False, ctrls=None):
        """
        Sends a command via the MultiShellInteractionMixin `riotctrl`s

        :param  cmd: A shell command as string.
        :param  ctrls: ctrls to run command on

        :return: Output of the command as a string
        """
        self._start_replwrap()
        if ctrls is None:
            ctrls = self.riotctrl.keys()
        elif not isinstance(ctrls, (tuple, list)):
            ctrls = (ctrls,)
        return {k: rw.run_command(cmd, timeout=timeout, async_=async_)
                for k, rw in self.replwrap.items() if k in ctrls}
