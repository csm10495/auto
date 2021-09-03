from setuptools import setup
import pathlib

init_text = pathlib.Path(__file__).parent / 'auto' / '__init__.py'
version = None
for line in init_text.read_text().splitlines():
    if line.startswith('__version__'):
        version = eval(line.split('=')[1])

assert version, 'Could not find __version__!'

setup(
    name='auto',
    author='csm10495',
    author_email='csm10495@gmail.com',
    url='http://github.com/csm10495/auto',
    version=version,
    packages=['auto'],
    license='MIT License',
    python_requires='>=3.7',
    long_description=open('readme.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
    ],
    include_package_data = True,
    install_requires=['pystray'],
)