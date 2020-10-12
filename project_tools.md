# Project Tools

These are a variety of code snippets, utilities, content for mock-up and/or initial templates, and other resources that can be useful for both initial and ongoing Django projects. While these pieces do not warrant their own installable packages, the function snippets or resources that are useful for any given project can be copied and adapted as appropriate.

This is primarily structured to point towards the key aspects included in this collection. Much of these are likely short or fairly easy to explore. They generally are collected here when developing other projects, but considered useful to easily reference later. So it can be expected this is not a complete documentation of all components or aspects of those components.

## Boilerplate Content

Static resources and Templates:

* A CSS reset, such as [Meyer's Reset](http://meyerweb.com/eric/tools/css/reset/), is usually the best practice.
* Included is also a CSS normalize file, and an style file that builds on top of that.
* As a placeholder for a typical site logo, there is `logo.svg`, and some other options from placeholder.com
* There is a simple `favicon.ico`, as a placeholder that should also be replaced before production.
* The `web/templates/generic` directory has both a `base.html` and `home.html` that can be modified & expanded.
  * These link to the static resources mentioned.
  * There is an example of using `placeholder.it` images for mock-ups.
* If using the `django-registration` package, the templates in `web/templates/django_registration` are useful starts.
