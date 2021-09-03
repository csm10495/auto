from unittest.mock import MagicMock, patch
import os
import pytest

# I've noticed on non Windows systems, a display is required to import pystray..
# effectively mock out pystray in this case completely.
if os.name != 'nt':
    import sys
    sys.modules['pystray'] = MagicMock()

import auto.icon_thread

IconThread = auto.icon_thread.IconThread

@pytest.fixture(scope='function')
def mock_icon():
    with patch.object(auto.icon_thread.pystray, 'Icon') as icon:
        yield icon

def test_icon_thread_init(mock_icon):
    t = IconThread(1, 2, a=3, b=4)
    assert t._icon_args == (1, 2,)
    assert t._icon_kwargs == {'a' : 3, 'b': 4}

def test_icon_thread_run(mock_icon):
    t = IconThread(1, 2, a=3, b=4)
    t.icon = MagicMock()

    t.run()
    mock_icon.assert_called_once_with(1, 2, a=3, b=4)
    t.icon.run.assert_called_once_with()

def test_icon_thread_stop(mock_icon):
    t = IconThread(1, 2, a=3, b=4)
    t.stop() # does nothing since .icon is None

    t.icon = MagicMock()
    t.stop() # calls .icon.stop()
    t.icon.stop.assert_called_once_with()

def test_icon_thread_as_context_manager(mock_icon):
    t = IconThread()
    t.run = MagicMock()
    t.stop = MagicMock()

    with t:
        t.run.assert_called_once_with()
        t.stop.assert_not_called()

    t.run.assert_called_once_with()
    t.stop.assert_called_once_with()