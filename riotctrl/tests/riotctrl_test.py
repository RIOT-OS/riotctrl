"""riotctrl.__init__ tests"""
import riotctrl


def test_version():
    """Test there is an `__version__` attribute.

    Goal is to have a test to run the test environment.
    """
    assert getattr(riotctrl, '__version__', None) is not None
