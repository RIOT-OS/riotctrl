"""Abstraction for multiple RIOTCtrl objects

Defines a class to abstract access to multiple RIOTCtrls.
"""

import riotctrl.ctrl

from riotctrl.multictrl.utils import MultiKeyDict


# Intentionally do not inherit from TermSpawn so we do not have to rewrite
# all of `pexpect` ;-)
# pylint: disable=too-many-ancestors
class MultiTermSpawn(MultiKeyDict):
    """Allows for access and control of multiple RIOTCtrl objects
    """
    def expect(self, pattern, *args, **kwargs):
        """
        mirroring riotctrl.ctrl.TermSpawn.expect()
        """
        return {k: v.expect(pattern, *args, **kwargs)
                for k, v in self.items()}

    def expect_exact(self, pattern, *args, **kwargs):
        """
        mirroring riotctrl.ctrl.TermSpawn.expect()
        """
        return {k: v.expect_exact(pattern, *args, **kwargs)
                for k, v in self.items()}

    def sendline(self, *args, **kwargs):
        """
        mirroring riotctrl.ctrl.TermSpawn.expect()
        """
        return {k: v.sendline(*args, **kwargs)
                for k, v in self.items()}


# pylint: disable=too-many-ancestors
class MultiRIOTCtrl(MultiKeyDict, riotctrl.ctrl.RIOTCtrl):
    """Allows for access and control of multiple RIOTCtrl objects

    >>> ctrl = MultiRIOTCtrl({'a': riotctrl.ctrl.RIOTCtrl(env={'BOARD': 'A'}),
    ...                       'b': riotctrl.ctrl.RIOTCtrl(env={'BOARD': 'B'})})
    >>> ctrl.board()
    {'a': 'A', 'b': 'B'}
    >>> ctrl['a','b'].board()
    {'a': 'A', 'b': 'B'}
    >>> ctrl['a'].board()
    'A'
    """
    TERM_SPAWN_CLASS = MultiTermSpawn

    def __init__(self, ctrls=None):
        super().__init__(ctrls)
        self.term = None  # type: MultiRIOTCtrl.TERM_SPAWN_CLASS

    @property
    def application_directory(self):
        """Absolute path to the containing RIOTCtrls current directory as
        dictionary."""
        return {k: ctrl.application_directory for k, ctrl in self.items()}

    def board(self):
        """Return board type of containing RIOTCtrls as dictionary."""
        return {k: ctrl.board() for k, ctrl in self.items()}

    def start_term_wo_sleep(self, **spawnkwargs):
        """Start the terminal (without waiting) for containing ctrls.
        """
        res = {}
        for k, ctrl in self.items():
            ctrl.start_term_wo_sleep(**spawnkwargs)
            res[k] = ctrl.term
        self.term = self.TERM_SPAWN_CLASS(res)

    def make_run(self, targets, *runargs, **runkwargs):
        """Call make `targets` for containing RIOTctrl contexts.

        It is using `subprocess.run` internally.

        :param targets: make targets
        :param *runargs: args passed to subprocess.run
        :param *runkwargs: kwargs passed to subprocess.run
        :return: subprocess.CompletedProcess object
        """
        return {k: ctrl.make_run(targets, *runargs, **runkwargs)
                for k, ctrl in self.items()}

    def make_command(self, targets):
        """Dictionary of make command for context of containing RIOTctrls.

        :return: list of command arguments (for example for subprocess)
        """
        return {k: ctrl.make_command(targets) for k, ctrl in self.items()}
