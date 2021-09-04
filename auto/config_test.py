from unittest.mock import MagicMock, patch
import auto.config
import pathlib
import pytest

from box import Box

from auto.config import *

@pytest.fixture(scope='function')
def valid_auto_config(tmpdir):
    poll_dir = pathlib.Path(tmpdir)
    ac = AutoConfig({
        'auto_config': {
            'watcher' : {
                'poll_seconds' : 5,
                'poll_directory' : str(poll_dir),
                'poll_all_directory': str(poll_dir / 'all'),
                'enable': True
                },
            'executor' : {
                'enable' : True
                }
            }})

    # sanity checks
    assert ac._dict.auto_config.watcher.poll_seconds == 5
    assert ac._dict.auto_config.watcher.enable == True
    assert ac._dict.auto_config.executor.enable == True

    yield ac

def test_init_from_path(valid_auto_config, tmpdir):
    d = pathlib.Path(tmpdir)

    yaml_file = d / 'tmp'
    valid_auto_config._dict.to_yaml(filename=yaml_file)
    ac = AutoConfig(yaml_file)
    assert ac._dict == valid_auto_config._dict

def test_init_disable_verify():
    AutoConfig({}, verify=False)

    with pytest.raises(auto.config.ConfigVerificationError):
        AutoConfig({}, verify=True)

def test_is_key_in_config_dict():
    AutoConfig._is_key_in_config_dict('key', int, {'key': 1})

    with pytest.raises(ConfigKeyMissingError):
        AutoConfig._is_key_in_config_dict('key', int, {'key2': 1})

    with pytest.raises(ConfigValueTypeIncorrectError):
        AutoConfig._is_key_in_config_dict('key', int, {'key': 'yo'})

def test_get_watcher_config(valid_auto_config, tmpdir):
    polldir = pathlib.Path(tmpdir)
    assert valid_auto_config.get_watcher_config() == Box({
        'poll_seconds' : 5,
        'poll_directory' : str(polldir),
        'poll_all_directory': str(polldir / 'all'),
        'enable': True
    })

def test_get_executor_config(valid_auto_config, tmpdir):
    polldir = pathlib.Path(tmpdir)
    assert valid_auto_config.get_executor_config() == Box({
        'enable': True
    })
