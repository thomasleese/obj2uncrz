#!/usr/bin/env python
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup, find_packages


setup(
    name='obj2uncrz',
    version='1.0.1',
    keywords='obj uncrz',
    url='https://github.com/tomleese/obj2uncrz',
    packages=find_packages(exclude=['tests', 'tests.*']),
    entry_points={
        'console_scripts': ['obj2uncrz = obj2uncrz.__main__:main']
    },
    zip_safe=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Topic :: Utilities'
    ],
    test_suite='tests'
)
