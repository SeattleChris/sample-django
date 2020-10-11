# sample-django

This is useful for testing stand alone Django Apps.
This is a simplified Django project with some helpful utilities to aid in investigating
apps in a simple and more isolated structure.

## Utility Files

The following files may need additional modifications for a given stand alone Django app we are making or testing.

* boot_django.py - sets up & configure Django settings as needed for the stand alone Django app.
* djangoshell.py - start a shell that is aware of our configured Django project including the stand alone app.
* makemigrations.py - creates the migration files needed for the stand alone Django app models.
* migrate.py - performs table migrations so the database is setup as needed.
* load_tests.py - can run all or some tests.Used by package manager to get its test suite, and by tox to run its tests.

## Making an Installable Django App as a Package Published to PyPI

An installable Django app needs to be made into a package. This generally means it should be made into an egg, wheel, or source distribution. These are built with setup tools.

Overview Steps:

* Create an app with the standard django-admin commands. Develop as desired & confirm it works.
* Develop tests for the app. Confirm they are working.
* Move the app code to a new directory at the root of the repo. This directory name can match the app name.
* Do a global search for APPNAME and replace it with the stand alone app name.
* Confirm project changes:
  * settings should include the app in the installed_apps list
  * urls should include the app urls.
* Confirm utility files changes: `makemigrations.py`, `load_tests.py`, `boot_django.py`
* Modify `setup.cfg` with the appropriate name and url, and possibly other settings.
* Install the local package:
  * `pipenv install -e .`
  * TODO: UPDATE PIP COMMAND LINE HERE
* Confirm the project works, recognizing the app from the installed packages.
* Create a repo for the standalone Django app. Move all app code and expected typical support files.
* Update `setup.cfg` with the new repo for url, and any other changes needed.
* Publish to PyPI (see section below).

Expected typical support files:

* README.rst - general information about the package (README.md is possible with extra parameters).
* setup.cfg - has metadata and options sections for clearly structured build and description of the package.
* setup.py - shim to execute the setup.cfg file.
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
