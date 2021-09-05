import auto.executor
import io
import os
import pathlib
import pytest
import sys
import tempenv
import uuid

from auto.executor import Executor, PROCESS_LOG_LINE_PREFIX
from .config_test import valid_auto_config
from unittest.mock import MagicMock, patch

@pytest.fixture(scope='function')
def py_file(tmpdir):
    p = pathlib.Path(tmpdir)
    f = p / f'tmp_{str(uuid.uuid4())}.py'
    f.write_text('print("hello")')
    yield f.resolve()

@pytest.fixture(scope='function')
def executor(valid_auto_config, tmpdir, py_file):
    exec_config = valid_auto_config._dict.auto_config.executor
    exec_config.execution_directory = str(tmpdir)
    exec_config.max_process_runtime_seconds = 5
    exec_config.extensions_to_remove_from_pathext = ['py', 'pyw', 'pyc']

    yield Executor(valid_auto_config, py_file)

def test_init_regular(executor):
    executor.config.get_component_logger = MagicMock()
    executor.__init__(executor.config, executor.run_path)
    executor.config.get_component_logger.assert_called_once_with('executor')

def test_init_run_path_doesnt_exist(executor):
    executor.config.get_component_logger = MagicMock()
    with pytest.raises(FileNotFoundError):
        executor.__init__(executor.config, executor.run_path / 'not_real')
    executor.config.get_component_logger.assert_called_once_with('executor')

def test_init_run_path_allows_something_in_path(executor):
    executor.config.get_component_logger = MagicMock()

    # put our tmp_XXX...py in PATH
    with tempenv.TemporaryEnvironment({
        'PATH' : str(executor.run_path.parent)
    }):
        executor.__init__(executor.config, pathlib.Path(executor.run_path.name))

    executor.config.get_component_logger.assert_called_once_with('executor')
    assert executor.run_path == executor.run_path.resolve()

def test_get_process_max_runtime_seconds(executor):
    assert executor.get_process_max_runtime_seconds() == 5
    executor.config._dict.auto_config.executor.max_process_runtime_seconds = None
    assert executor.get_process_max_runtime_seconds() == 31556952

def test_get_execution_directory(executor, tmpdir):
    tmp = pathlib.Path(tmpdir) / 'bleh'
    assert not tmp.is_dir()
    executor.config._dict.auto_config.executor.execution_directory = str(tmp)
    assert executor.get_execution_directory() == tmp
    assert tmp.is_dir()

    executor.config._dict.auto_config.executor.execution_directory = None
    assert executor.get_execution_directory() is None

def test_get_pathext(executor):
    executor.config._dict.auto_config.executor.extensions_to_remove_from_pathext = ['py', 'pyw', 'pyc', 'cmd', 'lol']

    with tempenv.TemporaryEnvironment({
        'PATHEXT': os.pathsep.join(['py', 'cmd', 'bat', 'exe'])
    }):
        assert executor.get_pathext() == ['bat', 'exe']

def test_log_process_stdout(executor):
    logger = MagicMock()
    log_lines = []
    logger.info = lambda x: log_lines.append(x)
    executor.logger = logger

    process = MagicMock()
    process.stdout = io.BytesIO(b'''
    Hello
I am
    cool! ''')

    executor._log_process_stdout(process)

    assert log_lines == [
        f'{PROCESS_LOG_LINE_PREFIX}',
        f'{PROCESS_LOG_LINE_PREFIX}    Hello',
        f'{PROCESS_LOG_LINE_PREFIX}I am',
        f'{PROCESS_LOG_LINE_PREFIX}    cool! '
    ]

def test_run_subprocess_output_to_logger_death_time(executor):
    executor.get_process_max_runtime_seconds = MagicMock(return_value=0)

    sleep_cmd = [sys.executable, '-c', 'import time;time.sleep(1)']

    logger = MagicMock()
    log_lines = []
    logger.info = lambda x: log_lines.append(x)
    logger.debug = lambda x: log_lines.append(x)
    executor.logger = logger

    assert executor.run_subprocess_output_to_logger(sleep_cmd) != 0
    assert 'Killing process as death' in log_lines[-2]

def test_run_subprocess_output_to_logger_normal(executor):
    cmd = [sys.executable, '-c', 'print (",".join([str(a) for a in range(5)]))']

    logger = MagicMock()
    log_lines = []
    logger.info = lambda x: log_lines.append(x)
    logger.debug = lambda x: log_lines.append(x)
    executor.logger = logger

    assert executor.run_subprocess_output_to_logger(cmd) == 0

    assert f'{PROCESS_LOG_LINE_PREFIX}0,1,2,3,4'

def test_execute_in_pathext(executor):
    executor.run_path = pathlib.Path('bleh.exe')
    executor.get_pathext = MagicMock(return_value=['.exe'])
    executor.run_subprocess_output_to_logger = MagicMock()

    logger = MagicMock()
    log_lines = []
    logger.info = lambda x: log_lines.append(x)
    logger.debug = lambda x: log_lines.append(x)
    executor.logger = logger

    executor.execute()
    assert 'PATHEX' in log_lines[-1]
    executor.run_subprocess_output_to_logger.assert_called_once_with([str(executor.run_path)])

def test_execute_in_python(executor):
    executor.run_path = pathlib.Path('bleh.py')
    executor.get_pathext = MagicMock(return_value=[])
    executor.run_subprocess_output_to_logger = MagicMock()

    logger = MagicMock()
    log_lines = []
    logger.info = lambda x: log_lines.append(x)
    logger.debug = lambda x: log_lines.append(x)
    executor.logger = logger

    executor.execute()
    assert 'Python' in log_lines[-1]
    executor.run_subprocess_output_to_logger.assert_called_once_with([sys.executable, str(executor.run_path)])

def test_execute_in_shebang(executor):
    executor.run_path = pathlib.Path(sys.executable)
    executor.get_pathext = MagicMock(return_value=[])
    executor.run_subprocess_output_to_logger = MagicMock()

    logger = MagicMock()
    log_lines = []
    logger.info = lambda x: log_lines.append(x)
    logger.debug = lambda x: log_lines.append(x)
    executor.logger = logger

    with patch.object(auto.executor.parseshebang, 'parse', return_value=['lolshebang']):
        executor.execute()

    assert 'Shebang' in log_lines[-1]
    executor.run_subprocess_output_to_logger.assert_called_once_with(['lolshebang', str(executor.run_path)])
