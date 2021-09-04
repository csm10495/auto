from unittest.mock import MagicMock, patch
import auto.config
import logging
import pathlib
import pytest
import uuid

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
                'enable': True,
                'log_directory': None,
                'log_level' : None,
                'log_max_size_bytes': None,
                'log_max_rotations_to_save': None,
                'log_format': None,
                },
            'executor' : {
                'enable' : True,
                'execution_directory' : None,
                'extensions_to_remove_from_pathext': ['py', 'pyw', 'pyc'],
                'max_process_runtime_seconds': None,
                'log_directory': None,
                'log_level' : None,
                'log_max_size_bytes': None,
                'log_max_rotations_to_save': None,
                'log_format': None,
                }
            }})

    # sanity checks
    assert ac._dict.auto_config.watcher.poll_seconds == 5
    assert ac._dict.auto_config.watcher.enable == True
    assert ac._dict.auto_config.executor.enable == True

    yield ac

@pytest.fixture(scope='function')
def mock_logging_get_logger():
    ''' Use this to make sure we get a different logger scope on each test. '''
    get_logger_real = auto.config.logging.getLogger

    def get_logger_mock(name=None):
        if str(name).startswith('auto.'):
            return get_logger_real(f'{str(uuid.uuid4())}.{name}')
        else:
            return get_logger_real(name)

    with patch.object(auto.config.logging, 'getLogger', get_logger_mock):
        yield

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

def test_get_component_logger_no_options(valid_auto_config, mock_logging_get_logger):
    assert isinstance(valid_auto_config.get_component_logger('watcher'), logging.Logger)

    logger = valid_auto_config.get_component_logger('executor')
    assert isinstance(logger, logging.Logger)

    logger.handlers = [1,2,3]
    # will clear handlers
    logger = valid_auto_config.get_component_logger('executor')

    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)

    with pytest.raises(ValueError):
        valid_auto_config.get_component_logger('executordasljdjasd')

def test_get_component_logger_with_options(valid_auto_config, tmpdir, mock_logging_get_logger):
    valid_auto_config._dict.auto_config.watcher.log_directory = str(tmpdir)
    valid_auto_config._dict.auto_config.watcher.log_level = "DEBUG"
    valid_auto_config._dict.auto_config.watcher.log_max_size_bytes = 1200
    valid_auto_config._dict.auto_config.watcher.log_max_rotations_to_save = 8

    logger = valid_auto_config.get_component_logger('watcher')
    assert isinstance(logger, logging.Logger)
    assert logger.getEffectiveLevel() == logging.DEBUG

    assert len(logger.handlers) == 1
    handler = logger.handlers[0]
    assert pathlib.Path(handler.baseFilename) == pathlib.Path(tmpdir) / 'log.txt'
    assert handler.backupCount == 8
    assert handler.maxBytes == 1200

def test_get_watcher_config(valid_auto_config, tmpdir):
    polldir = pathlib.Path(tmpdir)
    assert valid_auto_config.get_watcher_config() == Box({
        'poll_seconds' : 5,
        'poll_directory' : str(polldir),
        'poll_all_directory': str(polldir / 'all'),
        'enable': True,
        'log_directory': None,
        'log_level' : None,
        'log_max_size_bytes': None,
        'log_max_rotations_to_save': None,
        'log_format': None,
    })

def test_get_executor_config(valid_auto_config, tmpdir):
    polldir = pathlib.Path(tmpdir)
    assert valid_auto_config.get_executor_config() == Box({
        'enable': True,
        'execution_directory': None,
        'extensions_to_remove_from_pathext': ['py', 'pyw', 'pyc'],
        'max_process_runtime_seconds': None,
        'log_directory': None,
        'log_level' : None,
        'log_max_size_bytes': None,
        'log_max_rotations_to_save': None,
        'log_format': None,
    })
