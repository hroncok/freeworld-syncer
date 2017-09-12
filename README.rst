Freeworld syncer
================

A script that allows you to sync packages from RPM Fusion (such as
``chromium-freeworld``) with their Fedora counterparts (such as ``chromium``).

Currently **very raw development phase**, it has limited CLI interface
and can only do a few things. Features will be added as needed.


Installation
------------

There is none, run it from Python 3.6+ virtual environment::

   $ python3.6 -m venv __env__
   $ . __env__/bin/activate
   (__env__) $ python -m pip install -r requirements.txt
   (__env__) $ python freeworld-syncer.py


Usage
-----

Run it with `--help` to get more information.


koji command
~~~~~~~~~~~~

Displays the version built in Kojis side by side. Uses colors and exit code to
show what's wrong.

Example::

   $ python freeworld-syncer.py koji --pkgname chromium
   Koji check for chromium and chromium-freeworld
   fc28: chromium-60.0.3112.113-1.fc28 None (red)
   fc27: chromium-60.0.3112.113-1.fc27 chromium-freeworld-60.0.3112.113-1.fc27 (green)
   fc26: chromium-60.0.3112.113-1.fc26 chromium-freeworld-60.0.3112.113-1.fc26 (green)
   fc25: chromium-60.0.3112.113-1.fc25 chromium-freeworld-60.0.3112.113-1.fc25 (green)
   el7: chromium-60.0.3112.113-2.el7 None (red)


Tests
-----

Run the tests with ``pytest``::

   $ python3.6 -m venv __env__
   $ . __env__/bin/activate
   (__env__) $ python -m pip install -r requirements.txt
   (__env__) $ python -m pytest --flake8 *.py -v


License
-------

This code has been dedicated to the Public Domain, it is licensed with
`CC0 1.0 Universal Public Domain
Dedication <https://creativecommons.org/publicdomain/zero/1.0/>`__,
full text of the license is available in the LICENSE file in this
repository.
