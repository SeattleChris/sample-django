from django.test import TestCase  # , Client, override_settings, modify_settings, TransactionTestCase, RequestFactory
from unittest import skip
from django.core.exceptions import ImproperlyConfigured  # , ValidationError, ObjectDoesNotExist
from django.forms.utils import pretty_name
# from django.utils.translation import gettext_lazy as _
# from django.conf import settings
# from django.utils.html import conditional_escape  # , format_html
from django.contrib.auth import get_user_model
from .helper_general import MockRequest, AnonymousUser, MockUser, MockStaffUser, MockSuperUser  # UserModel, APP_NAME
# from .helper_views import MimicAsView, USER_DEFAULTS
# from datetime import date, time, timedelta, datetime as dt
# from pprint import pprint
from ..mixins import FormOverrideMixIn, ComputedUsernameMixIn
from .mixin_forms import FocusForm, CriticalForm, ComputedForm, OverrideForm, FormFieldsetForm  # # Base MixIns # #
from .mixin_forms import ComputedUsernameForm, CountryForm  # # Extended MixIns # #
from django_registration import validators
from copy import deepcopy

USER_DEFAULTS = {'email': 'user_fake@fake.com', 'password': 'test1234', 'first_name': 'f_user', 'last_name': 'fake_y'}
NAME_LENGTH = 'maxlength="150" '
USER_ATTRS = 'autocapitalize="none" autocomplete="username" '
FOCUS = 'autofocus '
REQUIRED = 'required '
DEFAULT_RE = {ea: '%(' + ea + ')s' for ea in ['start_tag', 'label_end', 'input_end', 'end_tag', 'name', 'name_pretty']}
USERNAME_TXT = '' + \
    '%(start_tag)s<label for="id_username">Username:</label>%(label_end)s<input type="text" name="username" ' + \
    '%(name_length)s%(user_attrs)s%(focus)srequired id="id_username">' + \
    '%(input_end)s<span class="helptext">Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.' + \
    '</span>%(end_tag)s\n'
USERNAME_TXT = USERNAME_TXT % dict(name_length=NAME_LENGTH, user_attrs=USER_ATTRS, focus=FOCUS, **DEFAULT_RE)
PASSWORD1_TXT = '' + \
    '%(start_tag)s<label for="id_password1">Password:</label>%(label_end)s<input type="password" name="password1" ' + \
    'autocomplete="new-password" required id="id_password1">%(input_end)s<span class="helptext"><ul><li>Your pass' + \
    'word can’t be too similar to your other personal information.</li><li>Your password must contain at least 8 ' + \
    'characters.</li><li>Your password can’t be a commonly used password.</li><li>Your password can’t be entirely ' + \
    'numeric.</li></ul></span>%(end_tag)s\n'
PASSWORD2_TXT = '' + \
    '%(start_tag)s<label for="id_password2">Password confirmation:</label>%(label_end)s<input type="password" ' + \
    'name="password2" autocomplete="new-password" required id="id_password2">%(input_end)s<span class="helptext">' + \
    'Enter the same password as before, for verification.</span>%(end_tag)s\n'
EMAIL_TXT = '' + \
    '%(start_tag)s<label for="id_email_field">Email:</label>%(label_end)s<input type="email" name="email_field" ' + \
    'maxlength="191" required id="id_email_field">%(end_tag)s\n'
names_text = '' + \
    '%(start_tag)s<label for="id_first_name">First name:</label>%(label_end)s<input type="text" name="first_name" ' + \
    '%(name_length)sid="id_first_name">%(end_tag)s\n' + \
    '%(start_tag)s<label for="id_last_name">Last name:</label>%(label_end)s<input type="text" name="last_name" ' + \
    '%(name_length)sid="id_last_name">%(end_tag)s\n'
TOS_TXT = '%(start_tag)s<label for="id_tos_field">I have read and agree to the Terms of Service:</label>' + \
    '%(label_end)s<input type="checkbox" name="tos_field" required id="id_tos_field">%(end_tag)s\n'
# DEFAULT_TXT = '%(start_tag)s<label for="id_generic_field">Generic field:</label>%(label_end)s' + \
#     '<input type="text" name="generic_field"%(attrs)srequired id="id_generic_field">%(end_tag)s\n'
DEFAULT_TXT = '%(start_tag)s<label for="id_%(name)s">%(name_pretty)s:</label>%(label_end)s' + \
    '<input type="text" name="%(name)s"%(attrs)s%(required)sid="id_%(name)s">%(end_tag)s\n'
REPLACE_TEXT = {'username': USERNAME_TXT, 'password1': PASSWORD1_TXT, 'password2': PASSWORD2_TXT, 'tos_field': TOS_TXT}
REPLACE_TEXT['email'] = EMAIL_TXT
for name in ('first_name', 'last_name'):
    REPLACE_TEXT[name] = DEFAULT_TXT % dict(attrs=' ' + NAME_LENGTH, required='', **DEFAULT_RE)  # TODO: ? required ?
# computed_text = names_text + password_text + EMAIL_TXT  # + username_text


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

    def get_expected_format(self, setup):
        replace_text = REPLACE_TEXT.copy()
        form_list = []
        if issubclass(self.form_class, ComputedUsernameMixIn):
            name_for_email = self.form.name_for_email or 'email'
            name_for_user = self.form.name_for_user or 'username'
            replace_text[name_for_email] = replace_text.pop('email')
            replace_text[name_for_user] = replace_text.pop('username')
            order = ['first_name', 'last_name', 'username', 'password1', 'password2', 'email']
            self.form.order_fields(order)
        for name in self.form.fields:
            default_re = DEFAULT_RE.copy()
            default_re.update({'name': name, 'name_pretty': pretty_name(name), 'attrs': '%(attrs)s'})
            default_re['required'] = REQUIRED if self.form.fields[name].required else ''
            txt = replace_text.get(name, DEFAULT_TXT) % default_re
            form_list.append(txt)
        # if issubclass(self.form_class, ComputedUsernameMixIn):
        #     if 'first_name' in self.form.fields and 'last_name' in self.form.fields:
        #         form_list.append(names_text)
        #     if 'password1' in self.form.fields:
        #         form_list.append(password_text)
        #     if 'email' in self.form.fields:
        #         form_list.append(email_text)
        #     if 'username' in self.form.fields:
        #         form_list.append(username_text)
        #     if 'tos_field' in self.form.fields:
        #         form_list.append(tos_text)
        # if 'generic_field' in self.form.fields:
        #     form_list.append(default_text)
        expected = ''.join(form_list) % setup
        return expected.strip()

    def test_as_table(self):
        """All forms should return HTML table rows when .as_table is called. """
        output = self.form.as_table().strip()
        setup = {'start_tag': '<tr><th>', 'label_end': '</th><td>', 'input_end': '<br>', 'end_tag': '</td></tr>'}
        override_attrs = ' size="15" ' if issubclass(self.form_class, FormOverrideMixIn) else ' '
        setup.update(attrs=override_attrs)
        expected = self.get_expected_format(setup)
        if output != expected:
            form_class = self.form.__class__.__name__
            print(f"//////////////////////////////// {form_class} AS_TABLE /////////////////////////////////////")
            if issubclass(self.form_class, ComputedUsernameMixIn):
                print("*** is sub class of ComputedUsernameMixIn ***")
            print(output)
            print("------------------------------------------------------------------------------------------")
            print(expected)
        # regex_match = ''  # '^<tr' ... '</tr>'
        # all_rows = all()  # every line break starts and ends with the HTML tr tags.
        self.assertNotEqual('', output)
        self.assertEqual(expected, output)

    def test_as_ul(self):
        """All forms should return HTML <li>s when .as_ul is called. """
        output = self.form.as_ul().strip()
        setup = {'start_tag': '<li>', 'end_tag': '</li>', 'label_end': ' ', 'input_end': ' '}
        override_attrs = ' size="15" ' if issubclass(self.form_class, FormOverrideMixIn) else ' '
        setup.update(attrs=override_attrs)
        expected = self.get_expected_format(setup)
        if output != expected:
            form_class = self.form.__class__.__name__
            print(f"//////////////////////////////// {form_class} AS_UL /////////////////////////////////////")
            if issubclass(self.form_class, ComputedUsernameMixIn):
                print("*** is sub class of ComputedUsernameMixIn ***")
            print(output)
            print("------------------------------------------------------------------------------------------")
            print(expected)
        # regex_match = ''  # '^<li' ... '</li'
        # all_rows = all()  # every line break starts and ends with the HTML li tags.
        self.assertNotEqual('', output)
        self.assertEqual(expected, output)

    def test_as_p(self):
        """All forms should return HTML <p>s when .as_p is called. """
        output = self.form.as_p().strip()
        setup = {'start_tag': '<p>', 'end_tag': '</p>', 'label_end': ' ', 'input_end': ' '}
        override_attrs = ' size="15" ' if issubclass(self.form_class, FormOverrideMixIn) else ' '
        setup.update(attrs=override_attrs)
        expected = self.get_expected_format(setup)
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

    def test_raise_on_missing_critical(self):
        """If the field is missing or misconfigured, it should raise ImproperlyConfigured. """
        # self.form.setup_critical_fields({'critical_fields': critical_fields})
        name_for_field = 'absent_field'
        field_opts = {'names': (name_for_field, 'absent'), 'alt_field': '', 'computed': False}
        critical_fields = {'absent_field': field_opts}
        with self.assertRaises(ImproperlyConfigured):
            self.form.fields_for_critical(critical_fields)

    def test_get_critical_from_existing_fields(self):
        """After fields have been formed, get_critical_field should return from fields, not from base_fields. """
        name = 'generic_field'
        opts = {'names': (name, ), 'alt_field': '', 'computed': False}
        # critical_fields = {name: opts}
        # base_ver = self.form.base_fields.get(name, None)
        expected_field = self.form.fields.get(name, None)
        actual_name, actual_field = self.form.get_critical_field(opts['names'])
        self.assertEqual(name, actual_name)
        self.assertEqual(expected_field, actual_field)

    def get_generic_name(self):
        name = 'generic_field'
        if name not in self.form.fields:
            return ''
        return name

    # @skip("Not Implemented")
    def test_callable_name_get_critical_field(self):
        """It should work on the returned value if a name in names is a callable. """
        special = self.get_generic_name
        name, field = self.form.get_critical_field(special)
        expected_name = special()
        expected_field = self.form.fields[expected_name]
        self.assertEqual(expected_name, name)
        self.assertEqual(expected_field, field)

    # @skip("Not Implemented")
    def test_raise_attach_broken(self):
        """If attach_critical_validators cannot access either fields or base_fields, it should raise as needed. """
        orig_fields = deepcopy(self.form.fields)
        orig_base_fields = deepcopy(self.form.base_fields)
        self.form.fields = None
        self.form.base_fields = None
        with self.assertRaises(ImproperlyConfigured):
            self.form.attach_critical_validators()
        self.form.fields = orig_fields
        self.form.base_fields = orig_base_fields

    @skip("Not Implemented OR Not Needed?")
    def test_tos_only_if_configured(self):
        """Confirm it does NOT add the tos_field when not configured to do so. """
        self.form.tos_required = False
        self.form_class.tos_required = False
        self.form = self.make_form_request()
        # initial_kwargs = {}
        # returned_kwargs = self.form.setup_critical_fields(**initial_kwargs)
        # expected = {}
        # actual = self.form.critical_fields
        name = self.form.name_for_tos or 'tos_field'
        found = self.form.fields.get(name, None)
        self.assertIsNone(found)
        # self.assertDictEqual(initial_kwargs, returned_kwargs)
        # self.assertDictEqual(expected, actual)

    # @skip("Not Implemented")
    def test_manage_tos_field(self):
        """Confirm tos_field is only present when configured to add the field. """
        name = self.form.name_for_tos or 'tos_field'
        initial_is_off = self.form.tos_required is False
        name_in_initial = name in self.form.fields
        found = self.form.fields.get(name, None)
        original_critical = deepcopy(self.form.critical_fields)

        self.form.tos_required = True
        # print("=================== TEST ADD TOS FIELD ===========================")
        # print(original_critical)
        # print(self.form.fields)
        expected = deepcopy(original_critical)
        name = getattr(self.form, 'name_for_tos', None) or ''
        tos_opts = {'names': (name, ), 'alt_field': 'tos_field', 'computed': False}
        tos_opts.update({'name': 'tos_field', 'field': self.form_class.tos_field})
        expected.update(name_for_tos=tos_opts)
        initial_kwargs = {}
        returned_kwargs = self.form.setup_critical_fields(**initial_kwargs)
        actual = self.form.critical_fields

        self.assertTrue(initial_is_off)
        self.assertFalse(name_in_initial)
        self.assertIsNone(found)
        self.assertDictEqual(initial_kwargs, returned_kwargs)
        self.assertDictEqual(expected, actual)

        self.form.fields.pop('tos_field', None)
        self.form.tos_required = False
        self.form.critical_fields = original_critical
        reset_kwargs = self.form.setup_critical_fields(**initial_kwargs)
        self.assertDictEqual({}, reset_kwargs)
        # print(reset_kwargs)
        # print(self.form.fields)

    def test_validators_attach(self):
        """Confirm that the custom validator on this Form is called and applies the expected validator. """
        expected = validators.validate_confusables
        field_name = 'generic_field'
        field = self.form.fields.get(field_name, None)
        all_validators = field.validators if field else []
        self.assertIn(expected, all_validators)


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
