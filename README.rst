django_improve_form
===============

This is a stand alone Django app that can be installed as a package and integrated in your Django project.

Installable App
---------------

This app models ...

This app can be installed and used in your django project by:

.. code-block:: bash

    $ pip install django_improve_form


Edit your `settings.py` file to include `'django_improve_form'` in the `INSTALLED_APPS`
listing.

.. code-block:: python

    INSTALLED_APPS = [
        ...

        'django_improve_form',
    ]


Edit your project `urls.py` file to import the URLs:


.. code-block:: python

    url_patterns = [
        ...

        path('django_improve_form/', include('django_improve_form.urls')),
    ]


Finally, add the models to your database:


.. code-block:: bash

    $ ./manage.py makemigrations django_improve_form


The "project" Branch
--------------------

The `master branch <https://github.com/seattlechris/django_improve_form/tree/master>`_ contains the final code.


Docs & Source
-------------

* Article: https://realpython.com/installable-django-app/
* Source: https://github.com/realpython/django_improve_form
* PyPI: https://pypi.org/project/django_improve_form/
