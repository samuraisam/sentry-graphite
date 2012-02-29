sentry-graphite
===============

An extension for Sentry that increments a key in graphite based on the error.

Install
-------

Install the package via ``pip``::

    pip install sentry-graphite

Add ``sentry_graphite`` to your ``INSTALLED_APPS``::

    from sentry.conf.server import *

    INSTALLED_APPS = INSTALLED_APPS + (
        'sentry_graphite',
    )

If this is the first plugin you are adding to sentry then you will have to modify
the settings file so it imports the correct settings. Your installed apps must look
like the above, adding to the existing installed apps which are imported from
`sentry.conf.server`.

Configuration
-------------

Go to your project's configuration page (Projects -> [Project]) and select the
Graphite tab. Fill out the host, port and desired prefix for Graphite.

Wait for new errors, and you should see keys being incremented in Graphite.
