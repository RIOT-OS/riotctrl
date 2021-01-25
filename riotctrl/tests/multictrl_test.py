"""riotctrl.multictrl test module."""

import os
import sys
import tempfile

import pexpect
import pytest

import riotctrl.ctrl
import riotctrl.multictrl.ctrl
import riotctrl.multictrl.shell
import riotctrl.shell

CURDIR = os.path.dirname(__file__)
APPLICATIONS_DIR = os.path.join(CURDIR, 'utils', 'application')


@pytest.fixture(name='app_pidfile_env')
def fixture_app_pidfile_envs():
    """Environment to use application pidfile"""
    with tempfile.NamedTemporaryFile() as tmpfile1:
        with tempfile.NamedTemporaryFile() as tmpfile2:
            yield [{'PIDFILE': tmpfile1.name}, {'PIDFILE': tmpfile2.name}]


@pytest.fixture(name='skip_first_prompt')
def fixture_skip_first_prompt(request):
    """
    Configures if first prompt should be skipped in the ctrls fixture
    """
    return getattr(request, "param", True)


@pytest.fixture(name='ctrls')
def fixture_ctrls(app_pidfile_env, skip_first_prompt):
    """Initializes RIOTCtrl for MultiShellInteractionMixin tests"""
    env1 = {
        'QUIET': '1',   # pipe > in command interferes with test
        'BOARD': 'board1',
        'APPLICATION': './shell.py' +
                       (' 1' if skip_first_prompt else ''),
    }
    env2 = {}
    env2.update(env1)
    env2['BOARD'] = 'board2'
    env1.update(app_pidfile_env[0])
    env2.update(app_pidfile_env[1])

    ctrls = riotctrl.multictrl.ctrl.MultiRIOTCtrl({
        'one': riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR, env1),
        'two': riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR, env2),
    })
    yield ctrls


def test_multiriotctrl_init():
    """Test typing for MultiRIOTCtrl initialization"""
    riotctrl.multictrl.ctrl.MultiRIOTCtrl()
    riotctrl.multictrl.ctrl.MultiRIOTCtrl({'test': riotctrl.ctrl.RIOTCtrl()})
    riotctrl.multictrl.ctrl.MultiRIOTCtrl({0: riotctrl.ctrl.RIOTCtrl()})
    riotctrl.multictrl.ctrl.MultiRIOTCtrl([(0, riotctrl.ctrl.RIOTCtrl())])
    riotctrl.multictrl.ctrl.MultiRIOTCtrl(((0, riotctrl.ctrl.RIOTCtrl()),))
    riotctrl.multictrl.ctrl.MultiRIOTCtrl(
        riotctrl.multictrl.ctrl.MultiRIOTCtrl(
            {'test': riotctrl.ctrl.RIOTCtrl()}
        )
    )


def test_multiriotctrl_application_dir():
    """Test if a freshly initialized MultiRIOTCtrl contains the keys the
    RIOTCtrl was initialized with
    """
    appbase = os.path.abspath(os.environ['APPBASE'])
    application1 = os.path.join(appbase, 'application')
    application2 = APPLICATIONS_DIR
    board1 = 'native'
    board2 = 'iotlab-m3'

    env1 = {'BOARD': board1}
    env2 = {'BOARD': board2}
    ctrl = riotctrl.multictrl.ctrl.MultiRIOTCtrl({
        'one': riotctrl.ctrl.RIOTCtrl(application1, env1),
        'two': riotctrl.ctrl.RIOTCtrl(application2, env2),
    })
    assert ctrl.application_directory == {
        'one': application1,
        'two': application2,
    }
    assert ctrl.board() == {
        'one': board1,
        'two': board2,
    }

    clean_cmd1 = ['make', '--no-print-directory', '-C', application1, 'clean']
    clean_cmd2 = ['make', '--no-print-directory', '-C', application2, 'clean']
    assert ctrl.make_command(['clean']) == {
        'one': clean_cmd1,
        'two': clean_cmd2,
    }


def test_multiriotctrl_running_term_with_reset(app_pidfile_env):
    """Test that MultiRIOTCtrl resets on run_term and expect behavior."""
    env1 = {'BOARD': 'board'}
    env1.update(app_pidfile_env[0])
    env1['APPLICATION'] = './hello.py'
    env2 = {}
    env2.update(env1)
    env2.update(app_pidfile_env[1])

    ctrl = riotctrl.multictrl.ctrl.MultiRIOTCtrl({
        'one': riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR, env1),
        'two': riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR, env2),
    })
    ctrl.TERM_STARTED_DELAY = 1

    assert ctrl['one'].env["PIDFILE"] == app_pidfile_env[0]["PIDFILE"]
    assert ctrl['two'].env["PIDFILE"] == app_pidfile_env[1]["PIDFILE"]

    with ctrl.run_term(logfile=sys.stdout) as child:
        # Firmware should have started twice on both boards
        res = child.expect_exact('Starting RIOT Ctrl')
        assert {'one': 0, 'two': 0} == res
        res = child.expect_exact('Hello World')
        assert {'one': 0, 'two': 0} == res
        res = child.expect([
            'This is not what we expect',
            'Starting RIOT Ctrl'
        ])
        assert {'one': 1, 'two': 1} == res
        res = child.expect_exact('Hello World')
        assert {'one': 0, 'two': 0} == res


def test_multiriotctrl_running_error_cases(app_pidfile_env):
    """Test basic functionalities with the 'echo' application for
    MultiRIOTCtrl.

    This tests:
    * stopping already stopped child
    """
    # Use only 'echo' as process to exit directly
    env = {'BOARD': 'board',
           'NODE_WRAPPER': 'echo', 'APPLICATION': 'Starting RIOT Ctrl'}
    env.update(app_pidfile_env[0])

    ctrl = riotctrl.multictrl.ctrl.MultiRIOTCtrl({
        'one': riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR, env),
    })
    ctrl.TERM_STARTED_DELAY = 1

    with ctrl.run_term(logfile=sys.stdout) as child:
        res = child.expect_exact('Starting RIOT Ctrl')
        assert {'one': 0} == res

        # Term is already finished and expect should trigger EOF
        with pytest.raises(pexpect.EOF):
            child.expect('this should eof')

    # Exiting the context manager should not crash when ctrl is killed


def test_multiriotctrl_echo_application(app_pidfile_env):
    """Test basic functionalities of MultiRIOTCtrl with the 'echo' application.
    """
    env = {'BOARD': 'board', 'APPLICATION': './echo.py'}
    env.update(app_pidfile_env[0])

    ctrls = riotctrl.multictrl.ctrl.MultiRIOTCtrl({
        'one': riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR, env),
        'two': riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR, env),
    })
    ctrls.TERM_STARTED_DELAY = 1

    with ctrls.run_term(logfile=sys.stdout) as child:
        res = child.expect_exact('Starting RIOT Ctrl')
        assert {'one': 0, 'two': 0} == res

        # Test multiple echo
        for i in range(16):
            child.sendline('Hello Test {}'.format(i))
            res = child.expect(r'Hello Test (\d+)', timeout=1)
            assert {'one': 0, 'two': 0} == res
            num = int(child['one'].match.group(1))
            assert i == num
            num = int(child['two'].match.group(1))
            assert i == num

        for key in ctrls:
            child[key].sendline('Pinging {}'.format(key))
        res = child.expect(r'Pinging (one|two)', timeout=1)
        assert {'one': 0, 'two': 0} == res
        assert child['one'].match.group(1) == 'one'
        assert child['two'].match.group(1) == 'two'


def test_multiriotctrl_shell_interaction_typeerror():
    """Tests if ShellInteraction throws a type error when initialized with a
    MultiRIOTCtrl
    """
    ctrls = riotctrl.multictrl.ctrl.MultiRIOTCtrl({
        'one': riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR),
        'two': riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR),
    })
    with pytest.raises(TypeError):
        riotctrl.shell.ShellInteraction(ctrls)


def test_multiriotctrl_multi_shell_interaction_typeerror():
    """Tests if MultiShellInteractionMixin ShellInteraction throws a type error
    RIOTCtrl
    """
    ctrl = riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR)
    with pytest.raises(TypeError):
        riotctrl.multictrl.shell.MultiShellInteractionMixin(ctrl)


@pytest.mark.parametrize('skip_first_prompt', [False, True],
                         indirect=['skip_first_prompt'])
def test_multiriotctrl_multi_shell_interaction_cmd(ctrls):
    """Test basic functionalities with the 'shell' application with and without
    first prompt missing."""
    with ctrls.run_term(logfile=sys.stdout, reset=False):
        shell = riotctrl.multictrl.shell.MultiShellInteractionMixin(ctrls)
        res = shell.cmd('foobar')
        assert 'one' in res and 'two' in res
        assert 'foobar' in res['one'] and 'foobar' in res['two']
        res = shell.cmd('snafoo', ctrls='one')
        assert 'one' in res and 'two' not in res
        assert 'snafoo' in res['one']
        res = shell.cmd('test', ctrls=['two'])
        assert 'two' in res and 'one' not in res
        assert 'test' in res['two']


class Snafoo(riotctrl.multictrl.shell.MultiShellInteractionMixin,
             riotctrl.shell.ShellInteraction):
    """Test inheritance class to test check_term decorator"""
    @riotctrl.multictrl.shell.MultiShellInteractionMixin.check_term
    def snafoo(self, ctrls=None):
        """snafoo pseudo command"""
        return self.cmd('snafoo', ctrls=ctrls)


def test_multiriotctrl_multi_shell_interaction_check_term(ctrls):
    """Tests the check_term decorator"""
    shell = Snafoo(ctrls)
    res = shell.snafoo()
    assert 'one' in res and 'two' in res
    assert 'snafoo' in res['one'] and 'snafoo' in res['two']
    res = shell.snafoo(ctrls=['one'])
    assert 'one' in res and 'two' not in res
    assert 'snafoo' in res['one']
