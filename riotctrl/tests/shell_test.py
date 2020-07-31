"""riotctrl.shell test module."""

import os
import sys
import tempfile

import pytest

import riotctrl.ctrl
import riotctrl.shell

CURDIR = os.path.dirname(__file__)
APPLICATIONS_DIR = os.path.join(CURDIR, 'utils', 'application')


@pytest.fixture(name='app_pidfile_env')
def fixture_app_pidfile_env():
    """Environment to use application pidfile"""
    with tempfile.NamedTemporaryFile() as tmpfile:
        yield {'PIDFILE': tmpfile.name}


def init_ctrl(app_pidfile_env, skip_first_prompt=False):
    """Initializes RIOTCtrl for ShellInteraction tests"""
    env = {
        'QUIET': '1',   # pipe > in command interferes with test
        'BOARD': 'board',
        'APPLICATION': './shell.py' +
                       (' 1' if skip_first_prompt else ''),
    }
    env.update(app_pidfile_env)

    ctrl = riotctrl.ctrl.RIOTCtrl(APPLICATIONS_DIR, env)
    return ctrl


def test_shell_interaction_cmd(app_pidfile_env):
    """Test basic functionalities with the 'shell' application."""
    ctrl = init_ctrl(app_pidfile_env)
    with ctrl.run_term(logfile=sys.stdout, reset=False):
        shell = riotctrl.shell.ShellInteraction(ctrl)
        res = shell.cmd('foobar')
        assert 'foobar' in res
        res = shell.cmd('snafoo')
        assert 'snafoo' in res


def test_shell_interaction_cmd_first_prompt_missing(app_pidfile_env):
    """Test basic functionalities with the 'shell' application when first
    prompt is missing."""
    ctrl = init_ctrl(app_pidfile_env, skip_first_prompt=True)
    with ctrl.run_term(logfile=sys.stdout, reset=False):
        shell = riotctrl.shell.ShellInteraction(ctrl)
        res = shell.cmd('foobar')
        assert 'foobar' in res
        res = shell.cmd('snafoo')
        assert 'snafoo' in res


def test_shell_interaction_cmd_reset_term(app_pidfile_env):
    """Test basic functionalities with the 'shell' application."""
    ctrl = init_ctrl(app_pidfile_env)
    ctrl.start_term()
    shell = riotctrl.shell.ShellInteraction(ctrl)
    res = shell.cmd('foobar')
    assert 'foobar' in res
    ctrl.start_term()   # reset's term implicitly
    res = shell.cmd('snafoo')
    assert 'snafoo' in res
    ctrl.stop_term()


class Snafoo(riotctrl.shell.ShellInteraction):
    """Test inheritance class to test check_term decorator"""
    @riotctrl.shell.ShellInteraction.check_term
    def snafoo(self):
        """snafoo pseudo command"""
        return self.cmd('snafoo')


def test_shell_interaction_check_term(app_pidfile_env):
    """Tests the check_term decorator"""
    ctrl = init_ctrl(app_pidfile_env, skip_first_prompt=True)
    shell = Snafoo(ctrl)
    res = shell.snafoo()
    assert 'snafoo' in res


def test_shell_interaction_check_term_when_term_started(app_pidfile_env):
    """Tests the check_term decorator"""
    ctrl = init_ctrl(app_pidfile_env, skip_first_prompt=True)
    shell = Snafoo(ctrl)
    shell.start_term()
    res = shell.snafoo()
    try:
        assert 'snafoo' in res
    finally:
        del shell
