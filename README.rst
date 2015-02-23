Gigaset Elements API command-line interface
==========

gigasetelements-cli is a python based program which allows you to control your Gigaset Elements home security system.
It comes with an easy to use CLI (command-line interface) suitable for direct use or cron jobs.

.. image:: http://blog.gigaset.com/wp-content/uploads/2014/05/Gigaset-elements-starter-kit.png
    :target: https://www.gigaset-elements.com


Installation
-----
No installation required but it does depend on the requests and pushbullet.py library

pip install requests pushbullet.py


Usage
-----
Set alarm modus to HOME::

    $ ./gigasetelements-cli.py -u first.last@domain.com -p mybigsecret -m home
  
    Gigaset Elements - Command-line Interface

    [-]  User logged in successfully.
    [-]  Authenticated as "first.last@domain.com" with language "nl"
    [-]  Basestation F19B75Z4EDC9F128A1P8C79BFA3178A1
    [-]  Modus set to HOME

Set alarm modus to AWAY and send PushBullet notification::

    $ ./gigasetelements-cli.py -u first.last@domain.com -p mybigsecret -m away -n z9FaKeSCKQDi2cmPUSHB62aiXx5I57eiujTOKENfS34
  
    Gigaset Elements - Command-line Interface

    [-]  User logged in successfully.
    [-]  Authenticated as "first.last@domain.com" with language "nl"
    [-]  Basestation F19B75Z4EDC9F128A1P8C79BFA3178A1
    [-]  Modus set to AWAY
    [-]  PushBullet notification sent

Show system EVENTS::

    $ ./gigasetelements-cli.py -u first.last@domain.com -p mybigsecret -e 5
  
    Gigaset Elements - Command-line Interface

    [-]  User logged in successfully.
    [-]  Authenticated as "first.last@domain.com" with language "nl"
    [-]  Basestation F19B75Z4EDC9F128A1P8C79BFA3178A1
    [-]  Showing last 5 event(s)
    [-]  02/21/2015 22:03:01 movement Livingroom  
    [-]  02/21/2015 22:02:25 close Frontdoor
    [-]  02/21/2015 22:01:24 movement Hallway
    [-]  02/21/2015 22:01:22 homecoming
    [-]  02/21/2015 22:01:18 open Frontdoor   

Read options from CONFIG file:: (command-line parameters override configuration file)

    $ ./gigasetelements-cli.py -c /etc/gigasetelements-cli.cfg
  
    Gigaset Elements - Command-line Interface

    [-]  Reading configuration from /etc/gigasetelements-cli.cfg
    [-]  User logged in successfully.
    [-]  Authenticated as "first.last@domain.com" with language "nl"
    [-]  Basestation F19B75Z4EDC9F128A1P8C79BFA3178A1
    [-]  Modus set to HOME
    [-]  PushBullet notification sent


Help
-----

    $ ./gigasetelements-cli.py -h
 
	usage: gigasetelements-cli.py [-h] [-u USERNAME] [-p PASSWORD] [-c CONFIG]
								  [-n NOTIFY] [-e EVENTS] [-m {home,away,custom}]
								  [-s] [-w] [-v]

	Gigaset Elements - Command-line Interface by dynasticorpheus@gmail.com

	optional arguments:
	  -h, --help            show this help message and exit
	  -u USERNAME, --username USERNAME
							username (email) in use with my.gigaset-elements.com
	  -p PASSWORD, --password PASSWORD
							password in use with my.gigaset-elements.com
	  -c CONFIG, --config CONFIG
							filename of configuration-file
	  -n NOTIFY, --notify NOTIFY
							pushbullet token
	  -e EVENTS, --events EVENTS
							show last <number> of events
	  -m {home,away,custom}, --modus {home,away,custom}
							set modus
	  -s, --status          show system status
	  -w, --warning         suppress authentication warnings
	  -v, --version         show version
 
	
To do
-----
Improve authentication/connection error handling

Replicate all functionality from app and/or website ... a long list

Improve overall code whilst I learn python


Notes
-----
Been ages since I have coded and python is new for me so in other words be kind :)

	
License
-------
GPL2
