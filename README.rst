Freeworld syncer
================

A script that allows you to sync packages from RPM Fusion (such as
``chromium-freeworld``) with their Fedora counterparts (such as ``chromium``).

Currently **very raw development phase**, it has no CLI interface
and cannot do anything useful yet. Features will be added as needed.


Usage
-----

No meaningful usage yet.


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
