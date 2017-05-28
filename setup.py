import re
from setuptools import setup


INSTALL_REQUIRES = [
    'betfairlightweight>=1.2'
]

TEST_REQUIRES = [
]

with open('flumine/__init__.py', 'r') as f:
    version = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]',
        f.read(),
        re.MULTILINE
    ).group(1)

setup(
        name='flumine',
        version=version,
        packages=[
                'flumine',
                'flumine.resources'
        ],
        package_dir={
                'flumine': 'flumine'
        },
        install_requires=INSTALL_REQUIRES,
        url='https://github.com/liampauling/flumine',
        license='MIT',
        author='liampauling',
        author_email='',
        description='Betfair data record framework utilising streaming',
        classifiers=[
                'License :: OSI Approved :: MIT License',
                'Operating System :: OS Independent',
                'Programming Language :: Python :: 3.4',
                'Programming Language :: Python :: 3.5',
                'Programming Language :: Python :: 3.6',
        ],
        test_suite='tests'
)
