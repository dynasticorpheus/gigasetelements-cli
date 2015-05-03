Gigaset Elements API command-line interface
===========================================

gigasetelements-cli is a python based program which allows you to control your Gigaset Elements home security system.
It comes with an easy to use CLI (command-line interface) suitable for direct use or cron jobs.

.. image:: http://blog.gigaset.com/wp-content/uploads/2014/05/Gigaset-elements-starter-kit.png
    :target: https://www.gigaset-elements.com

Installation
------------

**PYPI** - [https://pypi.python.org/pypi/gigasetelements-cli]

For easy installation including dependencies simply run below command (with elevated privileges if needed)

[-] *pip install gigasetelements-cli*

**GITHUB** - [https://github.com/dynasticorpheus/gigaset-elements]

[1] *git clone https://github.com/dynasticorpheus/gigaset-elements.git*  

[2] install *dependencies*, see requirements.txt

[3] *python setup.py install* (or run from source using wrapper ./gigasetelements-cli.py)


Features
------------
 * Show system and sensor status
 * List events and filter by type and/or date
 * Add and remove cronjobs for modus change at given time
 * Receive pushbullet messages on status and/or modus change

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
* Prepare for API V2
* Replicate all functionality from app and/or website ... a long list
* Improve overall code whilst I learn python


Notes
-----
Been ages since I have coded and python is new for me so in other words be kind :)


Donate
------
A lot of time and effort goes into making gigasetelements-cli so if you like it you might want to consider buying me a beer :)

.. image:: http://www.paypal.com/en_US/i/btn/x-click-but04.gif
    :target: https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=FETZ23LK5UH2J&item_number=gigasetelements%2dcli&currency_code=EUR
    :alt: Donate via PayPal


License
-------
GPL2
