Gigaset Elements API command-line interface
===========================================

|Version status| |Github stars| |Github forks| |CodeQL| |Quality Gate Status| |Downloads| |BuyMeCoffee|

gigasetelements-cli is a python based program which allows you to control your Gigaset Elements home security system.
It comes with an easy to use CLI (command-line interface) suitable for direct use or cron jobs.

.. image:: https://asset.conrad.com/media10/isa/160267/c1/-/nl/1650392_BB_00_FB/image.jpg
    :target: https://www.gigaset-elements.com

Installation
------------

**PYPI** - [https://pypi.python.org/pypi/gigasetelements-cli]

For easy installation including dependencies simply run below command (with elevated privileges if needed)

[-] *pip install gigasetelements-cli*

**GITHUB** - [https://github.com/dynasticorpheus/gigasetelements-cli]

[1] *git clone -b develop https://github.com/dynasticorpheus/gigasetelements-cli*

[2] install *dependencies*, pip install -r requirements.txt (with elevated privileges if needed)

[3] *python setup.py install --force* (or run from source using wrapper ./gigasetelements-cli.py)

**GITHUB** - [https://github.com/dynasticorpheus/gigasetelements-cli] [RECOMMENDED]

[1] *pip install git+https://github.com/dynasticorpheus/gigasetelements-cli@develop*


Features
------------
 * Show system and sensor status
 * List events and filter by type and/or date
 * Add and remove cronjobs for modus change at given time
 * Receive pushbullet messages on status and/or modus change
 * Show camera info and expose video urls for external usage (e.g. VLC)
 * Switch camera recording on/off
 * Monitor mode outputting live event stream to screen and/or log file
 * Show notification settings
 * Show registered mobile devices
 * Siren arming/disarming
 * Show custom rules (button/plug)
 * Switch plug on/off
 * Set alarm trigger delay

Usage
-----
* **Set alarm modus to HOME**::

    $ gigasetelements-cli -u first.last@domain.com -p mybigsecret -m home

    Gigaset Elements - Command Line Interface

    [-]  User logged in successfully.
    [-]  Authenticated as "first.last@domain.com" with language "nl"
    [-]  Basestation F19B75Z4EDC9F128A1P8C79BFA3178A1
    [-]  Modus set to HOME
                                        
* **Set alarm modus to AWAY and send PushBullet notification**::

    $ gigasetelements-cli -u first.last@domain.com -p mybigsecret -m away -n z9FaKeSCKQDi2cmPUSHB62aiXx5I57eiujTOKENfS34

    Gigaset Elements - Command Line Interface

    [-]  User logged in successfully.
    [-]  Authenticated as "first.last@domain.com" with language "nl"
    [-]  Basestation F19B75Z4EDC9F128A1P8C79BFA3178A1
    [-]  Modus set to AWAY
    [-]  PushBullet notification sent

* **Show system EVENTS**::

    $ gigasetelements-cli -u first.last@domain.com -p mybigsecret -e 5

    Gigaset Elements - Command Line Interface

    [-]  User logged in successfully.
    [-]  Authenticated as "first.last@domain.com" with language "nl"
    [-]  Basestation F19B75Z4EDC9F128A1P8C79BFA3178A1
    [-]  Showing last 5 event(s)
    [-]  02/21/2015 22:03:01 movement Livingroom
    [-]  02/21/2015 22:02:25 close Frontdoor
    [-]  02/21/2015 22:01:24 movement Hallway
    [-]  02/21/2015 22:01:22 homecoming
    [-]  02/21/2015 22:01:18 open Frontdoor

* **Read options from CONFIG file**::

    $ gigasetelements-cli -c /etc/gigasetelements-cli.conf

    Gigaset Elements - Command Line Interface

    [-]  Reading configuration from /etc/gigasetelements-cli.conf
    [-]  User logged in successfully.
    [-]  Authenticated as "first.last@domain.com" with language "nl"
    [-]  Basestation F19B75Z4EDC9F128A1P8C79BFA3178A1
    [-]  Modus set to HOME
    [-]  PushBullet notification sent


 On POSIX configuration file is automatically read from below locations: (use -i to ignore)

 *    ~/.gigasetelements-cli
 *    /etc/gigasetelements-cli.conf
 *    /usr/etc/gigasetelements-cli.conf
 *    /usr/local/etc/gigasetelements-cli.conf
 *    /opt/etc/gigasetelements-cli.conf

* **Schedule CRONJOB**::

    $ gigasetelements-cli -m home -o 17:00

    Gigaset Elements - Command Line Interface

    [-]  Cron job scheduled | Modus will be set to HOME on Sunday 26 April 2015 17:00


Help
-----

    $ gigasetelements-cli -h


To do
-----
* Improve overall code
* Replicate all functionality from app and/or website ... a long list
* Support for gigaset elements button


Notes
-----
Been ages since I have coded and python is new for me so in other words be kind :)


Donation Hall of Fame
------
A lot of time & effort goes into making gigasetelements-cli so if you like it you might want to consider buying me a :beer: :)

.. image:: http://www.paypal.com/en_US/i/btn/x-click-but04.gif
    :target: https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=FETZ23LK5UH2J&item_number=gigasetelements%2dcli&currency_code=EUR
    :alt: Donate via PayPal

**Cheers / Proost / Sante / Servus / Salud / Na zdrowie / Salute**

* *Orkun S*
* *Adrian R*
* *Joshua T*
* *Auke C*
* *RPC B*
* *Silke H*
* *Frank M*
* *Max G*
* *Andreas G*

License
-------
GPL2

.. |Version status| image:: https://img.shields.io/pypi/v/gigasetelements-cli.svg
   :target: https://pypi.python.org/pypi/gigasetelements-cli/
.. |Downloads| image:: https://img.shields.io/pypi/dm/gigasetelements-cli.svg
   :target: https://pypi.python.org/pypi/gigasetelements-cli/
.. |CodeQL| image:: https://github.com/dynasticorpheus/gigasetelements-cli/actions/workflows/codeql-analysis.yml/badge.svg
   :target: https://github.com/dynasticorpheus/gigasetelements-cli/actions/workflows/codeql-analysis.yml
.. |Github forks| image:: https://img.shields.io/github/forks/dynasticorpheus/gigasetelements-cli.svg
   :target: https://github.com/dynasticorpheus/gigasetelements-cli/network/members/
.. |Github stars| image:: https://img.shields.io/github/stars/dynasticorpheus/gigasetelements-cli.svg
   :target: https://github.com/dynasticorpheus/gigasetelements-cli/stargazers/
.. |BuyMeCoffee| image:: https://camo.githubusercontent.com/cd005dca0ef55d7725912ec03a936d3a7c8de5b5/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f6275792532306d6525323061253230636f666665652d646f6e6174652d79656c6c6f772e737667
   :target: https://buymeacoffee.com/dynasticorpheus/
.. |Quality Gate Status| image:: https://sonarcloud.io/api/project_badges/measure?project=dynasticorpheus_gigasetelements-cli&metric=alert_status
   :target: https://sonarcloud.io/summary/new_code?id=dynasticorpheus_gigasetelements-cli/
