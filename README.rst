RIOT Ctrl
=========

This provides python object abstraction of a RIOT device.
The first goal is to be the starting point for the serial abstraction and
build on top of that to provide higher level abstraction like over the shell.

It could provide an RPC interface to a device in Python over the serial port
and maybe also over network.

The goal is here to be test environment agnostic and be usable in any test
framework and also without it.


Testing
-------

Run `tox` to run the whole test suite:

::

    tox
    ...
    ________________________________ summary ________________________________
      test: commands succeeded
      lint: commands succeeded
      flake8: commands succeeded
      congratulations :)

Usage
-----

RIOTCtrl provides a python object abstraction of a RIOT device. It’s
meant as a starting point for any serial abstraction on which higher
level abstractions (like a shell) can be built.

.. code:: python

    from riotctrl.ctrl import RIOTCtrl

    env = {'BOARD': 'native'}
    # if not running from the application directory the a path must be provided
    ctrl = RIOTCtrl(env=env, application_directory='.')
    # flash the application
    ctrl.make_run(['flash'])
    # run the terminal through a contextmanager
    with ctrl.run_term():
        ctrl.term.expect('>')       # wait for shell to start
        ctrl.term.sendline("help")  # send the help command
        ctrl.term.expect('>')       # wait for the command result to finnish
        print(ctrl.term.before)     # print the command result
    # run without a contextmanager
    ctrl.start_term()               # start a serial terminal
    ctrl.term.sendline("help")      # send the help command
    ctrl.term.expect('>')           # wait for the command result to finnish
    print(ctrl.term.before)         # print the command result
    ctrl.stop_term()                # close the terminal

Creating a RIOTCtrl object is done via environments. If empty then all
configuration will come from the target application makefile. But any
Make environment variable can be overridden, for example setting
``BOARD`` to a target ``BOARD`` which is not the default for that
application.

Any make target used on RIOT devices can be used on the abstraction
like: ``make flash`` => ``ctrl.make_run(['flash'])``.

``ctrl.start_term()`` (``make term``\ ’s alter ego) by default spawns a
`pexpect <https://pexpect.readthedocs.io/en/stable/overview.html>`__
child application. From there interactions with the application
under use can be atomized. In the example below the output of the
``"help"`` command is captured:

ShellInteractions
~~~~~~~~~~~~~~~~~

RIOTCtrl provides a minimal extensions by using:
`pexpect replwrap <https://pexpect.readthedocs.io/en/stable/api/replwrap.html>`__
“[A] Generic wrapper for read-eval-print-loops, a.k.a. interactive shells”.
This implements a nice wrapper for RIOT shell commands since it will wait for a
command to finish before returning its output.

RIOT already provides a ``ShellInteraction`` for the ``"help"`` command as well
as many others. To make importing them as ``from riotctrl_shell.sys import Help``
possible RIOT's `pythonlibs <https://github.com/RIOT-OS/RIOT/tree/master/dist/pythonlibs>`__
needs to be part of the ``PYTHONPATH``, this can be done by setting in the environment
``PYTHONPATH=$PYTHONPATH:${RIOTBASE}/dist/pythonlibs`` or doing so in the
script ``sys.path.append('/path/to/RIOTBASE/dist/pythonlibs')``

The previous example can be re-written using ``ShellInteraction``:

.. code:: python

    from riotctrl.ctrl import RIOTCtrl
    from riotctrl.shell import ShellInteraction

    env = {'BOARD': 'native'}
    # if not running from the application directory the a path must be provided
    ctrl = RIOTCtrl(env=env, application_directory='.')
    # flash the application
    ctrl.flash()                     # alias for ctrl.make_run(['flash'])
    # shell interaction instance
    shell = ShellInteraction(ctrl)
    shell.start_term()               # start a serial terminal
    print(shell.cmd("help"))         # print the command result
    shell.stop_term()                # close the terminal

or using the already provided `Help <https://github.com/RIOT-OS/RIOT/blob/master/dist/pythonlibs/riotctrl_shell/sys.py#L16-L21>`__
``ShellInteraction``:

.. code:: python

    from riotctrl.ctrl import RIOTCtrl
    from riotctrl_shell.sys import Help

    env = {'BOARD': 'native'}
    # if not running from the application directory the a path must be provided
    ctrl = RIOTCtrl(env=env, application_directory='.')
    # flash the application
    ctrl.flash()                     # alias for ctrl.make_run(['flash'])
    # shell interaction instance, Help uses the @ShellInteraction.check_term
    # decorator, it will start the terminal if its not yet running, and close
    # it after the command ends
    shell = Help(ctrl)              # create ShellInteraction
    print(shell.help())             # print the command result

Writing ShellInteraction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lets use this simple C shell application as an example:

.. code:: c

    #include <stdio.h>
    #include <stdlib.h>
    #include "shell.h"

    static unsigned int counter = 0;

    static int _cmd_counter(int argc, char **argv)
    {
        if (argc == 1) {
            printf("counter: %d\n", counter);
        }
        else if (argc == 2) {
            counter += atoi(argv[1]);
        }
        else {
            puts("Usage: counter [value]");
            return -1;
        }
        return 0;
    }

    static const shell_command_t shell_commands[] = {
        { "counter", "prints current counter or adds input", _cmd_counter },
        { NULL, NULL, NULL }
    };

    int main(void)
    {
        char line_buf[SHELL_DEFAULT_BUFSIZE];

        shell_run(shell_commands, line_buf, SHELL_DEFAULT_BUFSIZE);

        return 0;
    }

This simple command allows to return the current counter value or modifying
by adding a value to it.

::

    main(): This is RIOT! (Version: 2021.10-devel-645-g2c3266-pr_kconfig_mtd)
    > boardinfo
    board: native
    cpu: native
    > counter 5
    > counter -3
    > counter
    counter: 2

A ``ShellInteraction`` for this could look as follows:

.. code:: python

    from riotctrl.shell import ShellInteraction


    class CounterCmdShell(ShellInteraction):
        @ShellInteraction.check_term
        def counter_cmd(self, args=None, timeout=-1, async_=False):
            cmd = "counter"
            if args is not None:
                cmd += " {args}".format(args=" ".join(str(a) for a in args))
            return self.cmd(cmd, timeout=timeout, async_=False)

Parsing Interaction Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Parsers can be written for the result of ShellInteraction commands,
these can then be returned in any format, for this a base class
ShellInteractionParser is provided where the ``parse()`` method needs to
be implemented.

An examples for the ``counter`` command

.. code:: python

    import re
    from riotctrl.shell import ShellInteractionParser


    class CounterCmdShellParser(ShellInteractionParser):
        pattern = re.compile(r"counter: (?P<counter>\d+)$")

        def parse(self, cmd_output):
            devices = None
            for line in cmd_output.splitlines():
                m = self.pattern.search(line)
                if m is not None:
                    return m.group["counter"]

.. code:: python

    env = {'BOARD': 'native'}
    # if not running from the application directory the a path must be provided
    ctrl = RIOTCtrl(env=env, application_directory='.')
    # flash the application
    ctrl.flash()                     # alias for ctrl.make_run(['flash'])
    # shell interaction instance
    shell = CounterCmdShell(ctrl)
     with ctrl.run_term():
        parser = CounterCmdShellParser()
        counter = parse.parse(shell_counter_cmd())
        shell.counter_cmd(4)
        assert counter + 4 = parse.parse(shell_counter_cmd())

Interacting with multiple RIOT devices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

RIOTCtrl only wrap’s a single RIOT device, handling multiple devices is
not yet handled in RIOTCtrl, but through different environments multiple
RIOT devices can be created and controlled.

Users of RIOT and `FIT IoT-LAB <https://www.iot-lab.info/>`__ may have
already ran experiments on multiple ctrls of the same type (e.g:
``iotlab-m3``) using the ``IOTLAB_NODE`` make environment variable. With
this one can easily control which device it is targeting.

But if running this locally, with e.g.: multiple ``samr21-xpro``
connected the serial or ``DEBUG_ADAPTER_ID`` must be used to flash the
correct device, and for some ``BOARD``\ s also the serial port ``PORT``.
These variables can be appended to the environment of the spawned
object, e.g:

-  `FIT IoT-LAB <https://www.iot-lab.info/>`__:

.. code:: python

    # first device using dwm1001-1 on the saclay site
    env1 = {'BOARD': 'dwm10001', 'IOTLAB_NODE': 'dwm1001-1.saclay.iot-lab.info'}
    ctrl1 = RIOTCtrl(env=env1, application_directory='.')
    # second device using dwm1001-2 on the saclay site
    env2 = {'BOARD': 'dwm10001', 'IOTLAB_NODE': 'dwm1001-2.saclay.iot-lab.info'}
    ctrl2 = RIOTCtrl(env=env2, application_directory='.')

-  locally:

.. code:: python

    # first samr21-xpro
    env1 = {'BOARD': 'samr21-xpro', 'DEBUG_ADAPTER_ID': 'ATML2127031800004957'}
    ctrl1 = RIOTCtrl(env=env1, application_directory='.')
    # second samr21-xpro
    env2 = {'BOARD': 'samr21-xpro', 'DEBUG_ADAPTER_ID': 'ATML2127031800011458'}
    ctrl2 = RIOTCtrl(env=env2, application_directory='.')

For the advanced user one could also do as suggested in
`multiple-boards-udev <https://api.riot-os.org/advanced-build-system-tricks.html#multiple-boards-udev>`__
and use an easy to remember variable to identify BOARDs (which would
allow also running the same python code on different setups), if
following the above guide:

.. code:: python

    # first samr21-xpro
    env1 = {'BOARD': 'samr21-xpro', 'BOARD_NUM': 0}
    ctrl1 = RIOTCtrl(env=env1, application_directory='.')
    # second samr21-xpro
    env2 = {'BOARD': 'samr21-xpro', 'BOARD_NUM': 1}
    ctrl2 = RIOTCtrl(env=env2, application_directory='.')

Factories
~~~~~~~~~

The same tasks are done multiple times creating the object flashing it,
starting the terminal and making sure its clean up. Once experiments
grow and take over multiple ctrls this can become tedious, using a
Factory together with a context manager can help with this.

Going back to our example lets write a factory inheriting from
``RIOTCtrlBoardFactoryBase`` (or directly from ``RIOTCtrlFactoryBase``
base class).

.. code:: python

    from contextlib import ContextDecorator
    from riotctrl.ctrl import RIOTCtrl, RIOTCtrlBoardFactory
    from riotctrl_ctrl import native

    class RIOTCtrlAppFactory(RIOTCtrlBoardFactory, ContextDecorator):

        def __init__(self):
            super().__init__(board_cls={
                'native': native.NativeRIOTCtrl,
            })
            self.ctrl_list = list()

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            for ctrl in self.ctrl_list:
                ctrl.stop_term()

        def get_ctrl(self, application_directory='.', env=None):
            # retrieve a RIOTCtrl Object
            ctrl = super().get_ctrl(
                env=env,
                application_directory=application_directory
            )
            # append ctrl to list
            self.ctrl_list.append(ctrl)
            # flash and start terminal
            ctrl.flash()
            ctrl.start_term()
            # return ctrl with started terminal
            return ctrl

And the script itself can be re-written as:

.. code:: python

    with RIOTCtrlAppFactory() as factory:
        env = {'BOARD': 'native'}
        ctrl = factory.get_ctrl(env=env)
        shell = SaulShell(ctrl)
        parser = SaulShellCmdParser()
        print(parser.parse(shell.saul_cmd()))

GNRC Networking example native
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Lets put all the above into practice and script an experiment verifying
connectivity between two ctrls, here multiple ``native`` instance will
be used.

First create two tap interfaces connected through a bridge interface,
e.g. on linux:

.. code:: shell

    ip link add name tapbr0 type bridge
    ip link set tapbr0 up
    ip tuntap add dev tap0 mode tap user $USER
    ip tuntap add dev tap1 mode tap user $USER
    ip link set dev tap0 master tapbr0
    ip link set dev tap1 master tapbr0
    ip link set dev tap0 up
    ip link set dev tap1 up

Then we can ping and parse the results asserting than packet loss is
under a threshold or that an mount of responses was received..

.. code:: python

    from riotctrl_shell.gnrc import GNRCICMPv6Echo, GNRCICMPv6EchoParser
    from riotctrl_shell.netif import Ifconfig


    class Shell(Ifconfig, GNRCICMPv6Echo):
      pass


    with RIOTCtrlAppFactory() as factory:
        # Create two native instances, specifying the tap interface
        native_0 = factory.get_ctrl(env={'BOARD':'native', 'PORT':'tap0'})
        native_1 = factory.get_ctrl(env={'BOARD':'native', 'PORT':'tap1'})
        # `NativeRIOTCtrl` allows for `make reset` with `native`
        native_0.reset()
        native_1.reset()
        # Perform a multicast ping and parse results
        pinger = Shell(native_0)
        parser = GNRCICMPv6EchoParser()
        result = parser.parse(pinger.ping6("ff02::1"))
        # assert packetloss is under 10%"))
        assert result['stats']['packet_loss'] < 10
        # assert at least one responder
        assert result['stats']['rx'] > 0

A more complex example can be seen in the Release Tests:
`04-single-hop-6lowpan-icmp <https://github.com/RIOT-OS/Release-Specs/blob/master/04-single-hop-6lowpan-icmp/test_spec04.py>`__

Examples
~~~~~~~~

-  pytest: `ReleaseSpecs <https://github.com/RIOT-OS/Release-Specs>`__
-  unittests:
    `tests/turo <https://github.com/RIOT-OS/RIOT/blob/master/tests/turo/tests/01-run.py>`__,
    `tests/congure_test <https://github.com/RIOT-OS/RIOT/blob/master/tests/congure_test/tests/01-run.py>`__

Discussion
~~~~~~~~~~

RIOTCtrl base class is not tied into having a serial based interaction, its
the most common usage so far but a new interface or ``Interaction`` could
use different different transports (e.g. COAP), and does not need to provide
a CLI type interface.

Test applications could also use Structured Output, like RIOT's
`turo <https://doc.riot-os.org/group__test__utils__result__output.html>`__,
and in this case parsing CBOR/JSON/XML output could be close to a NOP.
