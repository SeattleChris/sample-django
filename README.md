# sample-django

This is useful for testing stand alone Django Apps.
This is a simplified Django project with some helpful utilities to aid in investigating
apps in a simple and more isolated structure.

## Utility Files

The following should be modified as appropriate for a given stand alone Django app we are making or testing.

* boot_django.py - sets up & configure Django settings as needed for the stand alone Django app.
* djangoshell.py - start a shell that is aware of our configured Django project including the stand alone app.
* makemigrations.py - creates the migration files needed for the stand alone Django app models.
* migrate.py - performs table migrations so the database is setup as needed.
* load_tests.py - can run all or some tests.Used by package manager to get its test suite, and by tox to run its tests.

## Making an Installable Django App as a Package Published to PyPI

An installable Django app needs to be made into a package.
This generally means it should be made into an egg, wheel, or source distribution.
These are built with setup tools.

Expected typical support files:

* README.rst - general information about the package (README.md is possible with extra parameters).
* setup.cfg - has metadata and options sections for clearly structured build and description of the package.
* setup.py -
* pyproject.toml - See [Brett Cannon's article](https://snarky.ca/what-the-heck-is-pyproject-toml/)
* tox.ini - defines which combinations of environments to test.
* [app directory] - holding the actual Django app code.

See the sample docs in this repository.

## Testing various versions with tox

The `tox` tool can help us see if our package works on a variety of environments, such as different Python versions.
For example, to test Python 3.6 & 3.7, combined with testing Django 2.2 & 3.0 (four environments total) use:

```tox.ini
[tox]
envlist = py{36,37}-django220, py{36,37}-django300

[testenv]
deps =
    django220: Django>=2.2,<3
    django300: Django>=3
commands=
    python setup.py test
```

## Publishing as a package hosted on PyPI

PyPI expects an egg, wheel, or source distribution.

We can use [Twine](https://twine.readthedocs.io/en/latest/) to build and upload (there are other options).

```Shell
python -m pip install -U wheel twine setuptools
python setup.py sdist
python setup.py bdist_wheel
twine upload dist/*
```
