# sample-django

This is useful for testing stand alone Django Apps.
This is a simplified Django project with some helpful utilities to aid in investigating
apps in a simple and more isolated structure.

## Making an Installable Django App as a Package Published to PyPI

a README.rst is expected for stand alone packages on PyPI. (a README.md file is possible with extra parameters).

Expected typical support files:

README.rst - general information about the package (README.md is possible with extra parameters).
setup.cfg - has metadata and options sections for clearly structured build and description of the package.
pyproject.toml - See [Brett Cannon's article](https://snarky.ca/what-the-heck-is-pyproject-toml/)

See the sample docs in this repository.

## Publishing as a package hosted on PyPI

We can use [Twine](https://twine.readthedocs.io/en/latest/) to build and upload (there are other options).

```Shell
python -m pip install -U wheel twine setuptools
python setup.py sdist
python setup.py bdist_wheel
twine upload dist/*
```
