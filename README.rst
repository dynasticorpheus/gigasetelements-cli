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
  
    Gigaset Elements - Command Line Interface

    [-]  User logged in successfully.
    [-]  Authenticated as "first.last@domain.com" with language "nl"
    [-]  Basestation F19B75Z4EDC9F128A1P8C79BFA3178A1
    [-]  Modus set to HOME

Set alarm modus to AWAY and send PushBullet notification::

    $ ./gigasetelements-cli.py -u first.last@domain.com -p mybigsecret -m away -n z9FaKeSCKQDi2cmPUSHB62aiXx5I57eiujTOKENfS34
  
    Gigaset Elements - Command Line Interface

    [-]  User logged in successfully.
    [-]  Authenticated as "first.last@domain.com" with language "nl"
    [-]  Basestation F19B75Z4EDC9F128A1P8C79BFA3178A1
    [-]  Modus set to AWAY
    [-]  PushBullet notification sent

Show system STATUS::

    $ ./gigasetelements-cli.py -u first.last@domain.com -p mybigsecret -s
  
    Gigaset Elements - Command Line Interface

    [-]  User logged in successfully.
    [-]  Authenticated as "first.last@domain.com" with language "nl"
    [-]  Basestation F19B75Z4EDC9F128A1P8C79BFA3178A1
    [-]  Status ok


Help
-----

    $ ./gigasetelements-cli.py -h
  
	
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
