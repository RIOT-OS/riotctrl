"""RIOTctrl abstraction.

Define class to abstract a node over the RIOT build system.
"""

import abc
import os
import time
import logging
import subprocess
import contextlib

import pexpect


DEVNULL = subprocess.DEVNULL
MAKE = os.environ.get('MAKE', 'make')


class TermSpawn(pexpect.spawn):
    """Subclass to adapt the behaviour to our need.

    * change default `__init__` values
      * disable local 'echo' to not match send messages
      * 'utf-8/replace' by default
      * default timeout
    * tweak exception:
      * replace the value with the called pattern
      * remove exception context from inside pexpect implementation
    """

    def __init__(self,  # pylint:disable=too-many-arguments
                 command, timeout=10, echo=False,
                 encoding='utf-8', codec_errors='replace', **kwargs):
        super().__init__(command, timeout=timeout, echo=echo,
                         encoding=encoding, codec_errors=codec_errors,
                         **kwargs)

    def expect(self, pattern, *args, **kwargs):
        # pylint:disable=signature-differs
        try:
            return super().expect(pattern, *args, **kwargs)
        except (pexpect.TIMEOUT, pexpect.EOF) as exc:
            raise self._pexpect_exception(exc, pattern)

    def expect_exact(self, pattern, *args, **kwargs):
        # pylint:disable=arguments-differ
        try:
            return super().expect_exact(pattern, *args, **kwargs)
        except (pexpect.TIMEOUT, pexpect.EOF) as exc:
            raise self._pexpect_exception(exc, pattern)

    @staticmethod
    def _pexpect_exception(exc, pattern):
        """Tweak pexpect exception.

        * Put the calling 'pattern' as value
        * Remove exception context
        """
        exc.pexpect_value = exc.value
        exc.value = pattern

        # Remove exception context
        exc.__cause__ = None
        exc.__traceback__ = None
        return exc


class RIOTCtrl():
    """Class abstracting a RIOTctrl in an application.

    This should abstract the build system integration.

    :param application_directory: relative directory to the application.
    :param env: dictionary of environment variables that should be used.
                These overwrites values coming from `os.environ` and can help
                define factories where environment comes from a file or if the
                script is not executed from the build system context.

    Environment variable configuration

    :environment BOARD: current RIOT board type.
    :environment RIOT_TERM_START_DELAY: delay before `make term` is said to be
                                        ready after calling.
    """

    TERM_SPAWN_CLASS = TermSpawn
    TERM_STARTED_DELAY = int(os.environ.get('RIOT_TERM_START_DELAY') or 3)

    MAKE_ARGS = ()
    FLASH_TARGETS = ('flash',)
    RESET_TARGETS = ('reset',)
    TERM_TARGETS = ('cleanterm',)

    def __init__(self, application_directory='.', env=None):
        self._application_directory = application_directory

        self.env = os.environ.copy()
        self.env.update(env or {})

        self.term = None  # type: pexpect.spawn

        self.logger = logging.getLogger(__name__)

    @property
    def application_directory(self):
        """Absolute path to the current directory."""
        return os.path.abspath(self._application_directory)

    def board(self):
        """Return board type."""
        return self.env['BOARD']

    def flash(self, *runargs, stdout=DEVNULL, stderr=DEVNULL, **runkwargs):
        """Flash application in ``ctrl.application_directory`` to ctrl.

        :param stdout: stdout parameter passed to ctrl.make_run
                       (default: DEVNULL)
        :param stderr: stdout parameter passed to ctrl.make_run
                       (default: DEVNULL)
        :param *runargs: args passed to subprocess.run
        :param *runkwargs: kwargs passed to subprocess.run
        :return: subprocess.CompletedProcess object
        """
        self.make_run(self.FLASH_TARGETS, *runargs,
                      stdout=stdout, stderr=stderr, **runkwargs)

    def reset(self):
        """Reset current ctrl."""
        # Make reset yields error on some boards even if successful
        # Ignore printed errors and returncode
        self.make_run(self.RESET_TARGETS, stdout=DEVNULL, stderr=DEVNULL)

    @contextlib.contextmanager
    def run_term(self, reset=True, **startkwargs):
        """Terminal context manager."""
        try:
            self.start_term(**startkwargs)
            if reset:
                self.reset()
            yield self.term
        finally:
            self.stop_term()

    def start_term(self, **spawnkwargs):
        """Start the terminal.

        The function is blocking until it is ready.
        It waits some time until the terminal is ready and resets the ctrl.
        """
        self.stop_term()

        term_cmd = self.make_command(self.TERM_TARGETS)
        self.term = self.TERM_SPAWN_CLASS(term_cmd[0], args=term_cmd[1:],
                                          env=self.env, **spawnkwargs)

        # on many platforms, the termprog needs a short while to be ready
        time.sleep(self.TERM_STARTED_DELAY)

    def _term_pid(self):
        """Terminal pid or None."""
        return getattr(self.term, 'pid', None)

    def stop_term(self):
        """Safe 'term.close'.

        Handles possible exceptions.
        """
        try:
            self.term.close()
        except AttributeError:
            # Not initialized
            pass
        except ProcessLookupError:
            self.logger.warning('Process already stopped')
        except pexpect.ExceptionPexpect:
            # Not sure how to cover this in a test
            # 'make term' is not killed by 'term.close()'
            self.logger.critical('Could not close make term')

    def make_run(self, targets, *runargs, **runkwargs):
        """Call make `targets` for current RIOTctrl context.

        It is using `subprocess.run` internally.

        :param targets: make targets
        :param *runargs: args passed to subprocess.run
        :param *runkwargs: kwargs passed to subprocess.run
        :return: subprocess.CompletedProcess object
            """
        command = self.make_command(targets)
        # pylint:disable=subprocess-run-check
        return subprocess.run(command, env=self.env, *runargs, **runkwargs)

    def make_command(self, targets):
        """Make command for current RIOTctrl context.

        :return: list of command arguments (for example for subprocess)
        """
        command = [MAKE]
        command.extend(self.MAKE_ARGS)
        if self._application_directory != '.':
            dir_cmd = '--no-print-directory', '-C', self._application_directory
            command.extend(dir_cmd)
        command.extend(targets)
        return command


class RIOTCtrlFactoryBase(abc.ABC):
    # pylint: disable=too-few-public-methods
    # A factory usually does not have more methods than one.
    """Abstract factory to create different RIOTCtrl."""

    @abc.abstractmethod
    def get_ctrl(self, application_directory='.', env=None):
        """
        Returns a RIOTCtrl object of a class specified by the Factory

        :param application_directory: `application_directory` initialization
                                      parameter for the RIOTCtrl object
        :param env:                   `env` initialization parameter for
                                      the RIOTCtrl object.
        """
        raise NotImplementedError


class RIOTCtrlBoardFactory(RIOTCtrlFactoryBase):
    # pylint: disable=too-few-public-methods
    # A factory usually does not have more methods than one.
    """Factory mixin to create different RIOTCtrl types based on
    the BOARD environment variable.

    :param board_cls: A dict that maps the `BOARD` environment variable to a
                      RIOTCtrl class.
    """
    DEFAULT_CLS = RIOTCtrl
    BOARD_CLS = {}

    def __init__(self, board_cls=None):
        self.board_cls = {}
        self.board_cls.update(self.BOARD_CLS)
        if board_cls is not None:
            self.board_cls.update(board_cls)

    def get_ctrl(self, application_directory='.', env=None):
        """
        Returns a RIOTCtrl object of a class as specified in `board_cls` on
        initialization.

        :param application_directory: `application_directory` initialization
                                      parameter for the RIOTCtrl object
        :param env:                   `env` initialization parameter for
                                      the RIOTCtrl object. This will also be
                                      used to determine the actual class of
                                      the return value.

        When `BOARD` is set in the environment variables when `env` is provided
        in `env`, that value is used to look-up the RIOTCtrl class in the
        factory's `board_cls` for that specific `BOARD` value.
        """
        the_env = {}
        the_env.update(os.environ)
        if env:
            the_env.update(env)
        if 'BOARD' not in the_env or the_env['BOARD'] not in self.board_cls:
            cls = self.DEFAULT_CLS
        else:
            cls = self.board_cls[the_env['BOARD']]
        # cls does its own fetching of `os.environ` so only provide `env` here
        return cls(application_directory=application_directory, env=env)
