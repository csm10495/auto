'''
Home to the config file for running auto
'''

import logging
import logging.handlers
import os
import pathlib
import typing

from box import Box

class ConfigVerificationError(ValueError):
    ''' Base class for config verification errors '''
    pass

class ConfigKeyMissingError(ConfigVerificationError):
    ''' A key is missing from a dict '''
    pass

class ConfigValueTypeIncorrectError(ConfigVerificationError):
    ''' A value exists but is not the expected type '''
    pass

class NoDefault:
    pass

class AutoConfig:
    ''' Config wrapper for auto '''

    def __init__(self, path_or_dict: typing.Union[pathlib.Path, dict], verify: bool=True):
        '''
        Initializer for the object.

        Takes in a path (to yaml file) or a dict to parse the config from
        If verification is True, check that required keys (with appropriate values in the config)
        '''
        if isinstance(path_or_dict, pathlib.Path):
            self._dict = Box.from_yaml(filename=path_or_dict)
        else:
            self._dict = Box(path_or_dict)

        if verify:
            self.verify_config()

    @classmethod
    def _is_key_in_config_dict(cls, key: str, typ: typing.Union[typing.Type, tuple], config: dict, default=NoDefault):
        '''
        Helper method that will raise if a key isn't in the dict or if the key's value isn't of
        the given type.

        If default is passed in, and the key is not present, the value will be set to the default
        for the given key.
        '''
        if key not in config:
            if default == NoDefault:
                raise ConfigKeyMissingError(f"{key} is missing from config: {config}")
            else:
                config[key] = default

        value = config[key]
        if not isinstance(value, typ):
            raise ConfigValueTypeIncorrectError(f"{key}'s value {value} has an incorrrect type: (not {typ})")

    def verify_config(self):
        '''
        Verifies the internal configuration. If anything is wrong a
        ConfigVerificationError will be raised.

        Todo: Make it so this function can add 'optional' configs that are missing.
        '''
        # top level verification
        self._is_key_in_config_dict('auto_config', dict, self._dict)

        # auto_config verification
        auto_config = self._dict['auto_config']
        self._is_key_in_config_dict('watcher', dict, auto_config)
        self._is_key_in_config_dict('executor', dict, auto_config)

        # watcher verification
        watcher_config = auto_config['watcher']
        self._is_key_in_config_dict('poll_seconds', int, watcher_config)
        self._is_key_in_config_dict('poll_directory', (type(None), str), watcher_config)
        self._is_key_in_config_dict('poll_all_directory', (type(None), str), watcher_config)
        self._is_key_in_config_dict('enable', bool, watcher_config)
        self._is_key_in_config_dict('log_directory', (type(None), str), watcher_config)
        self._is_key_in_config_dict('log_level', (type(None), str, int), watcher_config)
        self._is_key_in_config_dict('log_max_size_bytes', (type(None), int), watcher_config)
        self._is_key_in_config_dict('log_max_rotations_to_save', (type(None), int), watcher_config)
        self._is_key_in_config_dict('log_format', (type(None), str), watcher_config)

        # executor verification
        executor_config = auto_config['executor']
        self._is_key_in_config_dict('enable', bool, executor_config)
        self._is_key_in_config_dict('execution_directory', (type(None), str), executor_config)
        self._is_key_in_config_dict('extensions_to_remove_from_pathext', (type(None), list), executor_config)
        self._is_key_in_config_dict('max_process_runtime_seconds', (type(None), int), executor_config)
        self._is_key_in_config_dict('log_directory', (type(None), str), executor_config)
        self._is_key_in_config_dict('log_level', (type(None), str, int), executor_config)
        self._is_key_in_config_dict('log_max_size_bytes', (type(None), int), executor_config)
        self._is_key_in_config_dict('log_max_rotations_to_save', (type(None), int), executor_config)
        self._is_key_in_config_dict('log_format', (type(None), str), executor_config)

    def get_component_logger(self, component: str) -> logging.Logger:
        ''' Gets a logger object for the given component '''
        if component not in ('watcher', 'executor'):
            raise ValueError("only valid components are executor and watcher")

        getter_name = f'get_{component}_config'
        config = getattr(self, getter_name)()

        logger = logging.getLogger(name=f'auto.{component}')

        # not clearing handlers would lead to double, etc prints if this function is called
        # multiple times.
        logger.handlers.clear()

        if config.log_directory:
            d = pathlib.Path(config.log_directory).resolve()

            os.makedirs(d, exist_ok=True)

            log_file_name = d / 'log.txt'
            max_bytes = config.log_max_size_bytes or (1024 * 1024)
            backup_count = config.log_max_rotations_to_save or 9
            handler = logging.handlers.RotatingFileHandler(log_file_name, maxBytes=max_bytes, backupCount=backup_count)
        else:
            handler = logging.StreamHandler()

        if handler not in logger.handlers:
            handler.setFormatter(logging.Formatter(config.log_format or '%(asctime)s - %(name)s:%(lineno)d - %(levelname)s - %(message)s'))
            logger.addHandler(handler)

        if config.log_level is not None:
            logger.setLevel(config.log_level)

        return logger

    def get_watcher_config(self) -> Box:
        ''' Returns a Box corresponding with the watcher config settings '''
        return self._dict['auto_config']['watcher']

    def get_executor_config(self) -> Box:
        ''' Returns a Box corresponding with the executor config settings '''
        return self._dict['auto_config']['executor']

