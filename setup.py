from setuptools import setup, find_packages
from codecs import open
from os import path


here = path.abspath(path.dirname(__file__))


with open(path.join(here, 'DESCRIPTION.rst'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='gigasetelements-cli',
    version='1.3.4',
    description='gigasetelements-cli allows you to control your \
    Gigaset Elements home security system from the command line.',
    long_description=long_description,
    url='https://github.com/dynasticorpheus/gigaset-elements',
    author='dynasticorpheus',
    author_email='dynasticorpheus@gmail.com',
    license='GPL2',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],

    keywords='Home Automation, Home Security, Internet of Things (IoT)',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=['requests', 'colorama', 'python-crontab',
                      'pushbullet.py'],

    entry_points={
        'console_scripts': [
            'gigasetelements-cli=gigasetelements.gigasetelements:main',
        ],
    },
)
