"""riotctrl.ctrl test module."""

import os
import sys
import tempfile

import pytest
import pexpect

import riotctrl.ctrl

CURDIR = os.path.dirname(__file__)
APPLICATIONS_DIR = os.path.join(CURDIR, 'utils', 'application')


def test_riotctrl_application_dir():
    """Test the creation of a riotctrl with an `application_dir`."""
    appbase = os.path.abspath(os.environ['APPBASE'])
    application = os.path.join(appbase, 'application')
    board = 'native'

    env = {'BOARD': board}
    ctrl = riotctrl.ctrl.RIOTCtrl(application, env)

    assert ctrl.application_directory == application
    assert ctrl.board() == board

    clean_cmd = ['make', '--no-print-directory', '-C', application, 'clean']
    assert ctrl.make_command(['clean']) == clean_cmd


def test_riotctrl_curdir():
    """Test the creation of a riotctrl with current directory."""
    appbase = os.path.abspath(os.environ['APPBASE'])
    application = os.path.join(appbase, 'application')
    board = 'native'

    _curdir = os.getcwd()
    _environ = os.environ.copy()
    try:
        os.environ['BOARD'] = board
        os.chdir(application)

        ctrl = riotctrl.ctrl.RIOTCtrl()

        assert ctrl.application_directory == application
        assert ctrl.board() == board
        assert ctrl.make_command(['clean']) == ['make', 'clean']
    finally:
        os.chdir(_curdir)
        os.environ.clear()
        os.environ.update(_environ)


@pytest.fixture(name='app_pidfile_env')
def fixture_app_pidfile_env():
    """Environment to use application pidfile"""
    with tempfile.NamedTemporaryFile() as tmpfile:
        yield {'PIDFILE': tmpfile.name}


def test_running_echo_application(app_pidfile_env):
    """Test basic functionalities with the 'echo' application."""
    env = {'BOARD': 'board', 'APPLICATION': './echo.py'}
    env.update(app_pidfile_env)

    ctrl = riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR, env)
    ctrl.TERM_STARTED_DELAY = 1

    with ctrl.run_term(logfile=sys.stdout) as child:
        child.expect_exact('Starting RIOT Ctrl')

        # Test multiple echo
        for i in range(16):
            child.sendline('Hello Test {}'.format(i))
            child.expect(r'Hello Test (\d+)', timeout=1)
            num = int(child.match.group(1))
            assert i == num


def test_running_term_with_reset(app_pidfile_env):
    """Test that ctrl resets on run_term."""
    env = {'BOARD': 'board'}
    env.update(app_pidfile_env)
    env['APPLICATION'] = './hello.py'

    ctrl = riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR, env)
    ctrl.TERM_STARTED_DELAY = 1

    with ctrl.run_term(logfile=sys.stdout) as child:
        # Firmware should have started twice
        child.expect_exact('Starting RIOT Ctrl')
        child.expect_exact('Hello World')
        child.expect_exact('Starting RIOT Ctrl')
        child.expect_exact('Hello World')


def test_running_term_without_reset(app_pidfile_env):
    """Test not resetting ctrl on run_term."""
    env = {'BOARD': 'board'}
    env.update(app_pidfile_env)
    env['APPLICATION'] = './hello.py'

    ctrl = riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR, env)
    ctrl.TERM_STARTED_DELAY = 1

    with ctrl.run_term(reset=False, logfile=sys.stdout) as child:
        child.expect_exact('Starting RIOT Ctrl')
        child.expect_exact('Hello World')
        # Firmware should start only once
        with pytest.raises(pexpect.exceptions.TIMEOUT):
            child.expect_exact('Starting RIOT Ctrl', timeout=1)


def test_running_error_cases(app_pidfile_env):
    """Test basic functionalities with the 'echo' application.

    This tests:
    * stopping already stopped child
    """
    # Use only 'echo' as process to exit directly
    env = {'BOARD': 'board',
           'NODE_WRAPPER': 'echo', 'APPLICATION': 'Starting RIOT Ctrl'}
    env.update(app_pidfile_env)

    ctrl = riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR, env)
    ctrl.TERM_STARTED_DELAY = 1

    with ctrl.run_term(logfile=sys.stdout) as child:
        child.expect_exact('Starting RIOT Ctrl')

        # Term is already finished and expect should trigger EOF
        with pytest.raises(pexpect.EOF):
            child.expect('this should eof')

    # Exiting the context manager should not crash when ctrl is killed


def test_expect_not_matching_stdin(app_pidfile_env):
    """Test that expect does not match stdin."""
    env = {'BOARD': 'board', 'APPLICATION': './hello.py'}
    env.update(app_pidfile_env)

    ctrl = riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR, env)
    ctrl.TERM_STARTED_DELAY = 1

    with ctrl.run_term(logfile=sys.stdout) as child:
        child.expect_exact('Starting RIOT Ctrl')
        child.expect_exact('Hello World')

        msg = "This should not be matched as it is on stdin"
        child.sendline(msg)
        matched = child.expect_exact([pexpect.TIMEOUT, msg], timeout=1)
        assert matched == 0
        # This would have matched with `ctrl.run_term(echo=True)`


def test_expect_value(app_pidfile_env):
    """Test that expect value is being changed to the pattern."""
    env = {'BOARD': 'board', 'APPLICATION': './echo.py'}
    env.update(app_pidfile_env)

    ctrl = riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR, env)
    ctrl.TERM_STARTED_DELAY = 1

    with ctrl.run_term(logfile=sys.stdout) as child:
        child.expect_exact('Starting RIOT Ctrl')

        # Exception is 'exc_info.value' and pattern is in 'exc.value'
        child.sendline('lowercase')
        with pytest.raises(pexpect.TIMEOUT) as exc_info:
            child.expect('UPPERCASE', timeout=0.5)
        assert str(exc_info.value) == 'UPPERCASE'

        # value updated and old value saved
        assert exc_info.value.value == 'UPPERCASE'
        assert exc_info.value.pexpect_value.startswith('Timeout exceeded.')

        # check the context is removed (should be only 2 levels)
        assert len(exc_info.traceback) == 2

        child.sendline('lowercase')
        with pytest.raises(pexpect.TIMEOUT) as exc_info:
            child.expect_exact('UPPERCASE', timeout=0.5)
        assert str(exc_info.value) == 'UPPERCASE'


def test_term_cleanup(app_pidfile_env):
    """Test a terminal that does a cleanup after kill.

    The term process should be able to run its cleanup.
    """
    # Always run as 'deleted=True' to deleted even on early exception
    # File must exist at the end of the context manager
    with tempfile.NamedTemporaryFile(delete=True) as tmpfile:
        env = {'BOARD': 'board'}
        env.update(app_pidfile_env)
        env['APPLICATION'] = './create_file.py %s' % tmpfile.name

        ctrl = riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR, env)
        ctrl.TERM_STARTED_DELAY = 1
        with ctrl.run_term(logfile=sys.stdout) as child:
            child.expect_exact('Running')
            # Ensure script is started correctly
            content = open(tmpfile.name, 'r', encoding='utf-8').read()
            assert content == 'Running\n'

        # File should not exist anymore so no error to create one
        # File must exist to be cleaned by tempfile
        open(tmpfile.name, 'x')
