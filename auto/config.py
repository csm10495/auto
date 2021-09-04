'''
Home to the config file for running auto
'''

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
    def _is_key_in_config_dict(cls, key: str, typ: typing.Union[typing.Type, tuple], config: dict):
        '''
        Helper method that will raise if a key isn't in the dict or if the key's value isn't of
        the given type.
        '''
        if key not in config:
            raise ConfigKeyMissingError(f"{key} is missing from config: {config}")

        value = config[key]
        if not isinstance(value, typ):
            raise ConfigValueTypeIncorrectError(f"{key}'s value {value} has an incorrrect type: (not {typ})")

    def verify_config(self):
        '''
        Verifies the internal configuration. If anything is wrong a
        ConfigVerificationError will be raised.
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

        # executor verification
        executor_config = auto_config['executor']
        self._is_key_in_config_dict('enable', bool, executor_config)

    def get_watcher_config(self) -> Box:
        ''' Returns a Box corresponding with the watcher config settings '''
        return self._dict['auto_config']['watcher']

    def get_executor_config(self) -> Box:
        ''' Returns a Box corresponding with the executor config settings '''
        return self._dict['auto_config']['executor']

