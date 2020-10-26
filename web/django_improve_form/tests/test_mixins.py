from django.test import TestCase  # , Client, override_settings, modify_settings, TransactionTestCase, RequestFactory
from unittest import skip
# from django.core.exceptions import ImproperlyConfigured  # , ValidationError, ObjectDoesNotExist
# from django.utils.translation import gettext_lazy as _
# from django.conf import settings
from django.contrib.auth import get_user_model
from .helper_general import MockRequest, AnonymousUser, MockUser, MockStaffUser, MockSuperUser  # UserModel, APP_NAME
# from .helper_views import MimicAsView, USER_DEFAULTS
# from datetime import date, time, timedelta, datetime as dt
# from pprint import pprint
from ..mixins import FormOverrideMixIn, ComputedUsernameMixIn
from .mixin_forms import FocusForm, CriticalForm, ComputedForm, OverrideForm, FormFieldsetForm  # # Base MixIns # #
from .mixin_forms import ComputedUsernameForm, CountryForm  # # Extended MixIns # #

USER_DEFAULTS = {'email': 'user_fake@fake.com', 'password': 'test1234', 'first_name': 'f_user', 'last_name': 'fake_y'}
username_text = '' + \
    '%(start_tag)s<label for="id_username">Username:</label>%(label_end)s<input type="text" name="username" ' + \
    'maxlength="150" autocapitalize="none" autocomplete="username" autofocus required id="id_username">' + \
    '%(input_end)s<span class="helptext">Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.' + \
    '</span>%(end_tag)s\n'
password_text = '' + \
    '%(start_tag)s<label for="id_password1">Password:</label>%(label_end)s<input type="password" name="password1" ' + \
    'autocomplete="new-password" required id="id_password1">%(input_end)s<span class="helptext"><ul><li>Your pass' + \
    'word can’t be too similar to your other personal information.</li><li>Your password must contain at least 8 ' + \
    'characters.</li><li>Your password can’t be a commonly used password.</li><li>Your password can’t be entirely ' + \
    'numeric.</li></ul></span>%(end_tag)s\n' + \
    '%(start_tag)s<label for="id_password2">Password confirmation:</label>%(label_end)s<input type="password" ' + \
    'name="password2" autocomplete="new-password" required id="id_password2">%(input_end)s<span class="helptext">' + \
    'Enter the same password as before, for verification.</span>%(end_tag)s\n'
email_text = '' + \
    '%(start_tag)s<label for="id_email_field">Email:</label>%(label_end)s<input type="email" name="email_field" ' + \
    'maxlength="191" required id="id_email_field">%(end_tag)s\n'
names_text = '' + \
    '%(start_tag)s<label for="id_first_name">First name:</label>%(label_end)s<input type="text" name="first_name" ' + \
    'maxlength="150" id="id_first_name">%(end_tag)s\n' + \
    '%(start_tag)s<label for="id_last_name">Last name:</label>%(label_end)s<input type="text" name="last_name" ' + \
    'maxlength="150" id="id_last_name">%(end_tag)s\n'
computed_text = names_text + password_text + email_text  # + username_text


class FormTests:
    form_class = None
    user_type = 'anonymous'  # 'superuser' | 'staff' | 'user' | 'anonymous'
    mock_users = True

    def setUp(self):
        self.user = self.make_user()
        self.form = self.make_form_request()

    def make_form_request(self, method='GET', **kwargs):
        """Constructs a mocked request object with the method, and applies the kwargs. """
        initial = kwargs.pop('initial', {})
        prefix = kwargs.pop('prefix', None)
        data = kwargs.pop('data', {})
        kwargs.setdefault('FILES', kwargs.pop('files', {}))
        request = MockRequest(**kwargs)
        request.method = method.upper()
        if request.method == 'PUT':
            method = 'POST'
        setattr(request, method, data)
        request.user = self.user
        self.request = request
        form_kwargs = {'initial': initial, 'prefix': prefix}
        if self.request.method in ('POST', 'PUT'):
            form_kwargs.update({'data': self.request.POST, 'files': self.request.FILES, })
        form = self.form_class(**form_kwargs)
        return form

    def _make_real_user(self, user_type=None, **user_setup):
        UserModel = get_user_model()
        user = None
        if self.user_type == 'anonymous':
            user = AnonymousUser()
        elif self.user_type == 'superuser':
            temp = {'is_staff': True, 'is_superuser': True}
            user_setup.update(temp)
            user = UserModel.objects.create(**user_setup)
            user.save()
        elif self.user_type == 'staff':
            temp = {'is_staff': True, 'is_superuser': False}
            user_setup.update(temp)
            user = UserModel.objects.create(**user_setup)
            user.save()
        elif self.user_type == 'user':
            temp = {'is_staff': False, 'is_superuser': False}
            user_setup.update(temp)
            user = UserModel.objects.create(**user_setup)
            user.save()
        elif self.user_type == 'inactive':
            temp = {'is_staff': False, 'is_superuser': False, 'is_active': False}
            user_setup.update(temp)
            user = UserModel.objects.create(**user_setup)
            user.save()
        return user

    def make_user(self, user_type=None, mock_users=None, **kwargs):
        """Returns a user object. Uses defaults that can be overridden by passed parameters. """
        user_type = user_type or self.user_type
        mock_users = self.mock_users if mock_users is None else mock_users
        if user_type == 'anonymous':
            return AnonymousUser()
        user_setup = USER_DEFAULTS.copy()
        user_setup.update(kwargs)
        if not self.mock_users:
            return self._make_real_user(user_type, **user_setup)
        type_lookup = {'superuser': MockSuperUser, 'staff': MockStaffUser, 'user': MockUser}
        user = type_lookup[user_type](**user_setup)
        return user

    def test_as_table(self):
        """All forms should return HTML table rows when .as_table is called. """
        output = self.form.as_table().strip()
        expected = '<tr><th><label for="id_generic_field">Generic field:</label></th>'
        if issubclass(self.form_class, ComputedUsernameMixIn):
            setup = {'start_tag': '<tr><th>', 'label_end': '</th><td>', 'input_end': '<br>', 'end_tag': '</td></tr>'}
            expected = computed_text % setup
            expected = expected.strip()
        else:
            expected += '<td><input type="text" name="generic_field"%(attrs)srequired id="id_generic_field"></td></tr>'
        override_attrs = ' size="15" ' if issubclass(self.form_class, FormOverrideMixIn) else ' '
        expected = expected % {'attrs': override_attrs}
        if output != expected:
            form_class = self.form.__class__.__name__
            print(f"//////////////////////////////// {form_class} AS_TABLE /////////////////////////////////////")
            if issubclass(self.form_class, ComputedUsernameMixIn):
                print("*** is sub class of ComputedUsernameMixIn ***")
            print(output)
        # regex_match = ''  # '^<tr' ... '</tr>'
        # all_rows = all()  # every line break starts and ends with the HTML tr tags.
        self.assertNotEqual('', output)
        self.assertEqual(expected, output)

    def test_as_ul(self):
        """All forms should return HTML <li>s when .as_ul is called. """
        output = self.form.as_ul().strip()
        expected = '<li><label for="id_generic_field">Generic field:</label> '
        if issubclass(self.form_class, ComputedUsernameMixIn):
            expected = computed_text % {'start_tag': '<li>', 'end_tag': '</li>', 'label_end': ' ', 'input_end': ' '}
            expected = expected.strip()
        else:
            expected += '<input type="text" name="generic_field"%(attrs)srequired id="id_generic_field"></li>'
        override_attrs = ' size="15" ' if issubclass(self.form_class, FormOverrideMixIn) else ' '
        expected = expected % {'attrs': override_attrs}
        if output != expected:
            form_class = self.form.__class__.__name__
            print(f"//////////////////////////////// {form_class} AS_UL /////////////////////////////////////")
            if issubclass(self.form_class, ComputedUsernameMixIn):
                print("*** is sub class of ComputedUsernameMixIn ***")
            print(output)
        # regex_match = ''  # '^<li' ... '</li'
        # all_rows = all()  # every line break starts and ends with the HTML li tags.
        self.assertNotEqual('', output)
        self.assertEqual(expected, output)

    def test_as_p(self):
        """All forms should return HTML <p>s when .as_p is called. """
        output = self.form.as_p().strip()
        expected = '<p><label for="id_generic_field">Generic field:</label> '
        if issubclass(self.form_class, ComputedUsernameMixIn):
            expected = computed_text % {'start_tag': '<p>', 'end_tag': '</p>', 'label_end': ' ', 'input_end': ' '}
            expected = expected.strip()
        else:
            expected += '<input type="text" name="generic_field"%(attrs)srequired id="id_generic_field"></p>'
        override_attrs = ' size="15" ' if issubclass(self.form_class, FormOverrideMixIn) else ' '
        expected = expected % {'attrs': override_attrs}
        if output != expected:
            form_class = self.form.__class__.__name__
            print(f"//////////////////////////////// {form_class} AS_P /////////////////////////////////////")
            if issubclass(self.form_class, ComputedUsernameMixIn):
                print("*** is sub class of ComputedUsernameMixIn ***")
            print(output)
        # regex_match = ''  # '^<p' ... '</p'
        # all_rows = all()  # every line break starts and ends with the HTML p tags.
        self.assertNotEqual('', output)
        self.assertEqual(expected, output)

    @skip("Not Implemented")
    def test_html_output(self):
        """All forms should have a working _html_output method. ? Should it conform to the same API? """
        pass

    def find_focus_field(self):
        """Returns a list of all fields that have been given an HTML attribute of 'autofocus'. """
        fields = self.get_current_fields()
        found = []
        for field_name, field in fields.items():
            has_focus = field.widget.attrs.get('autofocus', None)
            if has_focus:
                found.append(field_name)
        return found

    def get_current_fields(self):
        """The form currently outputs these fields. """
        return self.form.fields.copy()

    def test_focus(self, name=None):
        """Always True if the assign_focus_field method is absent. Otherwise checks if configured properly. """
        focus_func = getattr(self.form, 'assign_focus_field', None)
        fields = self.get_current_fields()
        if focus_func:
            name = name or getattr(self.form, 'named_focus', None)
            expected = focus_func(name, fields)
        else:
            expected = 'username' if 'username' in fields else None
            expected = name or expected or None
            if not expected:
                self.assertTrue(True)
                return
        focus_list = self.find_focus_field()
        self.assertEqual(1, len(focus_list))
        self.assertEqual(expected, focus_list[0])


class FocusTests(FormTests, TestCase):
    form_class = FocusForm


class CriticalTests(FormTests, TestCase):
    form_class = CriticalForm


class ComputedTests(FormTests, TestCase):
    form_class = ComputedForm


class OverrideTests(FormTests, TestCase):
    form_class = OverrideForm


class FormFieldsetTests(FormTests, TestCase):
    form_class = FormFieldsetForm


class ComputedUsernameTests(FormTests, TestCase):
    form_class = ComputedUsernameForm


class CountryTests(FormTests, TestCase):
    form_class = CountryForm
