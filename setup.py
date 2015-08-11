import os

from setuptools import setup


# required due to vboxfs not supporting hard links. this doesn't have any ill
# effects. it just means there's a bit of copying instead of hard linking.
del os.link


extras_require = {
    'dev': [
        'coverage',
        'pytest',
        'pytest-cov',
    ],
}

extras_require['all'] = list({
    dep for deps in extras_require.itervalues() for dep in deps})


setup(
    name='ebb-lint',
    vcversioner={
        'version_module_paths': ['ebb_lint/_version.py'],
    },
    description='lint for ensuring quality software',
    author='Flowroute Inc.',
    author_email='development@flowroute.com',
    packages=[
        'ebb_lint',
        'ebb_lint.checkers',
        'ebb_lint.test',
    ],
    install_requires=[
        'enum34',
        'flake8',
        'venusian',
    ],
    extras_require=extras_require,
    setup_requires=['vcversioner'],
    entry_points={
        'flake8.extension': [
            'L = ebb_lint:EbbLint',
        ],
    },
)
