from setuptools import setup
from flumine.__init__ import __version__


INSTALL_REQUIRES = [
]
TEST_REQUIRES = [
]

setup(
        name='flumine',
        version=__version__,
        packages=['flumine', 'flumine.strategies'],
        package_dir={'flumine': 'flumine'},
        install_requires=INSTALL_REQUIRES,
        # requires=['requests'],
        url='https://github.com/liampauling/flumine',
        license='MIT',
        author='liampauling',
        author_email='',
        description='Betfair data record framework utilising streaming',
        test_suite='tests'
)
