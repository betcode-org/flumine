from setuptools import setup
from flumine.__init__ import __version__


INSTALL_REQUIRES = [
    'betfairlightweight>=0.8.4'
]
TEST_REQUIRES = [
]

setup(
        name='flumine',
        version=__version__,
        packages=['flumine', 'flumine.resources'],
        package_dir={'flumine': 'flumine'},
        install_requires=INSTALL_REQUIRES,
        url='https://github.com/liampauling/flumine',
        license='MIT',
        author='liampauling',
        author_email='',
        description='Betfair data record framework utilising streaming',
        test_suite='tests'
)
