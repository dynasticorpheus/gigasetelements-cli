#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""Install routine for gigasetelements command-line interface."""

import os
import codecs
from setuptools import setup, find_packages


HERE = os.path.abspath(os.path.dirname(__file__))


with codecs.open(os.path.join(HERE, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()

packagelist = ['future', 'requests', 'pushbullet.py', 'unidecode', 'colorama', 'configargparse']

if os.name == 'posix':
    packagelist.append('python-crontab')
    packagelist.append('daemonize')

setup(
    name='gigasetelements-cli',
    version='2023.4.0',
    description='gigasetelements-cli allows you to control your \
    Gigaset Elements home security system from the command line.',
    long_description=long_description,
    url='https://github.com/dynasticorpheus/gigasetelements-cli',
    author='dynasticorpheus',
    author_email='dynasticorpheus@gmail.com',
    license='GPL2',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6'
    ],

    keywords='Home Automation, Home Security, Internet of Things (IoT)',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=packagelist,

    entry_points={
        'console_scripts': [
            'gigasetelements-cli=gigasetelements.gigasetelements:main',
        ],
    },
)
