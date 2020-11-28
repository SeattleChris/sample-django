APPNAME
===============

This is a stand alone Django app that can be installed as a package and integrated in your Django project.

Installable App
---------------

This app models ...

This app can be installed and used in your django project by:

.. code-block:: bash

    $ pip install APPNAME


Edit your `settings.py` file to include `'APPNAME'` in the `INSTALLED_APPS`
listing.

.. code-block:: python

    INSTALLED_APPS = [
        ...

        'APPNAME',
    ]


Edit your project `urls.py` file to import the URLs:


.. code-block:: python

    url_patterns = [
        ...

        path('APPNAME/', include('APPNAME.urls')),
    ]


Finally, add the models to your database:


.. code-block:: bash

    $ ./manage.py makemigrations APPNAME


The "project" Branch
--------------------

The `master branch <https://github.com/seattlechris/APPNAME/tree/master>`_ contains the final code.


Docs & Source
-------------

* Article: https://realpython.com/installable-django-app/
* Source: https://github.com/realpython/APPNAME
* PyPI: https://pypi.org/project/APPNAME/
