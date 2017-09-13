Freeworld syncer
================

A script that allows you to sync packages from RPM Fusion (such as
``chromium-freeworld``) with their Fedora counterparts (such as ``chromium``).

Currently **very raw development phase**, not tested much except for chromium.
Features will be added as needed.


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

   $ python freeworld-syncer.py --pkgname chromium koji
   Koji check for chromium and chromium-freeworld
   fc28: chromium-60.0.3112.113-1.fc28 None (red)
   fc27: chromium-60.0.3112.113-1.fc27 chromium-freeworld-60.0.3112.113-1.fc27 (green)
   fc26: chromium-60.0.3112.113-1.fc26 chromium-freeworld-60.0.3112.113-1.fc26 (green)
   fc25: chromium-60.0.3112.113-1.fc25 chromium-freeworld-60.0.3112.113-1.fc25 (green)
   el7: chromium-60.0.3112.113-2.el7 None (red)


git command
~~~~~~~~~~~

Merges changes from Fedora to RPM Fusion dist-git. It only works if the changes
can be merged without conflicts.

Example::

   $ python freeworld-syncer.py --pkgname chromium git --branch master
   Git sync for chromium and chromium-freeworld
   
   Setting up git-scm in ./scm...
   Fetching origin
   Fetching fedora
   Already on 'master'
   Your branch is ahead of 'origin/master' by 5 commits.
     (use "git push" to publish your local commits)
   HEAD is now at 2843feb Merge Fedora, 60.0.3112.113-2
   Merging master from Fedora to RPM Fusion...
   Already on 'master'
   Your branch is up-to-date with 'origin/master'.
   Auto-merging chromium-freeworld.spec
   Auto-merging .gitignore
   Merge made by the 'recursive' strategy.
    .gitignore                                        |   1 +
    chromium-61.0.3163.79-MOAR-GCC-FIXES.patch        |  35 +++
    ...
    15 files changed, 767 insertions(+), 42 deletions(-)
    create mode 100644 chromium-61.0.3163.79-MOAR-GCC-FIXES.patch
    ...
   Getting sources...
   HEAD is now at 661f204 fix patch
   HEAD is now at a4c8b2c XXX merge
   Getting https://commondatastorage.googleapis.com/chromium-browser-official/chromium-61.0.3163.79.tar.xz to ./chromium-61.0.3163.79.tar.xz
   ./chromium-61.0.3163.79.tar.xz already exists, skipping download
   Getting https://dl.google.com/dl/edgedl/chrome/policy/policy_templates.zip to ./policy_templates.zip
   ./policy_templates.zip already exists, skipping download
   Deprecation warning: kojiconfig is deprecated. Instead, kojiprofile should be used.
   File already uploaded: policy_templates.zip
   File already uploaded: depot_tools.git-master.tar.gz
   File already uploaded: chromium-61.0.3163.79.tar.xz
   Source upload succeeded. Don't forget to commit the sources file
   Squashing source change to merge commit...
   [master 73bc035] Merge Fedora, chromium-61.0.3163.79-1
    Date: Wed Sep 13 17:02:23 2017 +0200
   
   Ready in ./scm/chromium-freeworld
   Inspect the commit and push manually at will

Tests
-----

Run the tests with ``pytest``::

   $ python3.6 -m venv __env__
   $ . __env__/bin/activate
   (__env__) $ python -m pip install -r requirements.txt
   (__env__) $ python -m pytest


License
-------

This code has been dedicated to the Public Domain, it is licensed with
`CC0 1.0 Universal Public Domain
Dedication <https://creativecommons.org/publicdomain/zero/1.0/>`__,
full text of the license is available in the LICENSE file in this
repository.
