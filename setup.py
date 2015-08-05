import os

from setuptools import setup


# required due to vboxfs not supporting hard links. this doesn't have any ill
# effects. it just means there's a bit of copying instead of hard linking.
del os.link


extras_require = {
    'dev': [
        'coverage',
        'pytest',
    ],
}

extras_require['all'] = list({
    dep for deps in extras_require.itervalues() for dep in deps})


setup(
    name='ebb-devtools',
    vcversioner={
        'version_module_paths': ['ebb_devtools/_version.py'],
    },
    description='tools for developing quality software',
    author='Flowroute Inc.',
    author_email='development@flowroute.com',
    packages=[
        'ebb_devtools',
        'ebb_devtools.lint',
        'ebb_devtools.lint.test',
    ],
    install_requires=[
        'enum34',
        'flake8',
        'parsley',
    ],
    extras_require=extras_require,
    setup_requires=['vcversioner'],
    entry_points={
        'flake8.extension': [
            'L = ebb_devtools.lint:EbbLint',
        ]
    },
)
