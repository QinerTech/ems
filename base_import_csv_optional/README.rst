.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Group-based permissions for importing CSV files 
===============================================

This module makes importing data from CSV files optional for each user,
allowing it only for those users belonging to a specific group.
Any other user not belonging to such group will not have the "Import" button
available anywhere. The action will even be blocked internally (to prevent
XMLRPC access, for example).


Usage
=====

To allow a user to import data from CSV files, just follow this steps:

* Go to *Settings/Users/Users* menu.
* Enter the user you want to allow.
* Within the "Access Rights" tab and "Technical Settings" group, check the
  option "Allow importing CSV files".


For further information, please visit:

- https://www.odoo.com/forum/help-1


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/server-tools/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/server-tools/issues/new?body=module:%20super_calendar%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Alejandro Santana <alejandrosantana@anubia.es>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.

Icon
----

Iconic fonts used in module icon are Font Awesome: http://fontawesome.io/
