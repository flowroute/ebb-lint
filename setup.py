import os
import sys

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
    dep for deps in extras_require.values() for dep in deps})


install_requires = [
    'flake8',
    'intervaltree',
    'six',
    'venusian',
]

if sys.version_info < (3, 4):
    install_requires.append('enum34')


with open('README.rst') as infile:
    long_description = infile.read()


setup(
    name='ebb-lint',
    vcversioner={
        'version_module_paths': ['ebb_lint/_version.py'],
    },
    description='lint for ensuring quality software',
    long_description=long_description,
    author='Flowroute Inc.',
    author_email='development@flowroute.com',
    url='https://github.com/flowroute/ebb-lint',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Quality Assurance',
    ],
    license='MIT',
    packages=[
        'ebb_lint',
        'ebb_lint.checkers',
        'ebb_lint.test',
    ],
    install_requires=install_requires,
    extras_require=extras_require,
    setup_requires=['vcversioner'],
    entry_points={
        'flake8.extension': [
            'L = ebb_lint:EbbLint',
        ],
    },
)
