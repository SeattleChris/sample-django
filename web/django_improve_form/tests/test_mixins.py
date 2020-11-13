from django.test import TestCase  # , Client, override_settings, modify_settings, TransactionTestCase, RequestFactory
from unittest import skip
from django.core.exceptions import ImproperlyConfigured, ValidationError, NON_FIELD_ERRORS  # , ObjectDoesNotExist
from django.urls.exceptions import NoReverseMatch
from django.forms.utils import pretty_name, ErrorDict  # , ErrorList
from django.forms import (CharField, BooleanField, EmailField, HiddenInput, MultipleHiddenInput,
                          RadioSelect, CheckboxSelectMultiple, CheckboxInput, Textarea, Select, SelectMultiple)
from django.contrib.auth import get_user_model  # , views
from django.urls import reverse  # , reverse_lazy
from django.utils.datastructures import MultiValueDict
from django.utils.html import format_html  # conditional_escape,
# from django.utils.safestring import mark_safe
from django_registration import validators
from .helper_general import MockRequest, AnonymousUser, MockUser, MockStaffUser, MockSuperUser  # UserModel, APP_NAME
from .mixin_forms import FocusForm, CriticalForm, ComputedForm, OverrideForm, FormFieldsetForm  # # Base MixIns # #
from .mixin_forms import ComputedUsernameForm, CountryForm  # # Extended MixIns # #
from ..mixins import FormOverrideMixIn, ComputedUsernameMixIn
from copy import deepcopy


USER_DEFAULTS = {'email': 'user_fake@fake.com', 'password': 'test1234', 'first_name': 'f_user', 'last_name': 'fake_y'}
OTHER_USER = {'email': 'other@fake.com', 'password': 'test1234', 'first_name': 'other_user', 'last_name': 'fake_y'}
NAME_LENGTH = 'maxlength="150" '
USER_ATTRS = 'autocapitalize="none" autocomplete="username" '
FOCUS = 'autofocus '  # TODO: Deal with HTML output for a field (besides username) that has 'autofocus' on a field?
REQUIRED = 'required '
MULTIPLE = ' multiple'
DEFAULT_RE = {ea: f"%({ea})s" for ea in ['start_tag', 'label_end', 'input_end', 'end_tag', 'name', 'pretty', 'attrs']}
DEFAULT_RE['input_type'] = 'text'  # TODO: ? required ?
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
TOS_TXT = '%(start_tag)s<label for="id_tos_field">I have read and agree to the Terms of Service:</label>' + \
    '%(label_end)s<input type="checkbox" name="tos_field" required id="id_tos_field">%(end_tag)s\n'
HIDDEN_TXT = '<input type="hidden" name="%(name)s" value="%(initial)s" id="id_%(name)s">'
START_LABEL = '%(start_tag)s<label for="id_%(name)s">%(pretty)s:</label>%(label_end)s'
DEFAULT_TXT = START_LABEL + \
    '<input type="%(input_type)s" name="%(name)s" %(attrs)s%(required)sid="id_%(name)s">%(end_tag)s\n'
AREA_TXT = START_LABEL + \
    '<textarea name="%(name)s" %(attrs)s%(required)sid="id_%(name)s">\n%(initial)s</textarea>%(end_tag)s\n'
SELECT_TXT = START_LABEL + \
    '<select name="%(name)s" %(required)sid="id_%(name)s"%(multiple)s>\n%(options)s</select>%(end_tag)s\n'
OPTION_TXT = '  <option value="%(val)s">%(display_choice)s</option>\n\n'
CHECK_TXT = '%(start_tag)s<label>%(pretty)s:</label>%(label_end)s<ul id="id_%(name)s">\n%(options)s</ul>%(end_tag)s\n'
RADIO_TXT = '%(start_tag)s<label for="id_%(name)s_0">%(pretty)s:</label>%(label_end)s' + \
    '<ul id="id_%(name)s">\n%(options)s</ul>%(end_tag)s\n'
OTHER_OPTION_TXT = '    <li><label for="id_%(name)s_%(num)s"><input type="%(input_type)s" name="%(name)s" ' + \
    'value="%(val)s" %(required)sid="id_%(name)s_%(num)s">\n %(display_choice)s</label>\n\n</li>\n'
FIELD_FORMATS = {'username': USERNAME_TXT, 'password1': PASSWORD1_TXT, 'password2': PASSWORD2_TXT, 'tos_field': TOS_TXT}


class FormTests:
    form_class = None
    user_type = 'anonymous'  # 'superuser' | 'staff' | 'user' | 'anonymous'
    mock_users = True

    def setUp(self):
        self.user = self.make_user()
        self.form = self.make_form_request()
        # field_order = list(self.form.base_fields.keys())
        # self.form.order_fields(field_order)

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
        if 'username' not in user_setup:
            user_setup['username'] = user_setup.get('email', '')
        if self.user_type == 'anonymous':  # Technically already handled.
            return AnonymousUser()
        elif self.user_type == 'superuser':
            temp = {'is_staff': True, 'is_superuser': True}
            user_setup.update(temp)
            user = UserModel.objects.create_superuser(**user_setup)
        elif self.user_type == 'staff':
            temp = {'is_staff': True, 'is_superuser': False}
            user_setup.update(temp)
            user = UserModel.objects.create_user(**user_setup)
        elif self.user_type == 'user':
            temp = {'is_staff': False, 'is_superuser': False}
            user_setup.update(temp)
            user = UserModel.objects.create_user(**user_setup)
        elif self.user_type == 'inactive':
            temp = {'is_staff': False, 'is_superuser': False, 'is_active': False}
            user_setup.update(temp)
            user = UserModel.objects.create_user(**user_setup)
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

    def get_format_attrs(self, name, field):
        """For the given named field, get the attrs as determined by the field and widget settings. """
        attrs, result = {}, []
        if field.initial and not isinstance(field.widget, Textarea):
            attrs['value'] = str(field.initial)
        attrs.update(field.widget_attrs(field.widget))
        result = ''.join(f'{key}="{val}" ' for key, val in attrs.items())
        if issubclass(self.form.__class__, FormOverrideMixIn):
            # TODO: Expand for actual output when using FormOverrideMixIn, or a sub-class of it.
            result += '%(attrs)s'  # content '%(attrs)s'
        else:
            result = '%(attrs)s' + result  # '%(attrs)s' content
        return result

    def get_expected_format(self, setup):
        field_formats = FIELD_FORMATS.copy()
        form_list = []
        if issubclass(self.form_class, ComputedUsernameMixIn):
            name_for_email = self.form.name_for_email or self.form._meta.model.get_email_field() or 'email'
            name_for_user = self.form.name_for_user or self.form._meta.model.USERNAME_FIELD or 'username'
            if 'email' in field_formats:
                field_formats[name_for_email] = field_formats.pop('email')
            if 'username' in field_formats:
                field_formats[name_for_user] = field_formats.pop('username')
            order = ['first_name', 'last_name', name_for_email, name_for_user, 'password1', 'password2', ]
            self.form.order_fields(order)
        hidden_list = []
        # print("======================= GET EXPECTED FORMAT ===============================")
        for name, field in self.form.fields.items():
            if isinstance(field.widget, (HiddenInput, MultipleHiddenInput, )):
                hide_re = {'name': name, 'initial': field.initial}
                txt = HIDDEN_TXT % hide_re
                hidden_list.append(txt)
                continue
            cur_replace = DEFAULT_RE.copy()
            cur_replace.update({'name': name, 'pretty': field.label or pretty_name(name)})
            cur_replace['required'] = REQUIRED if field.required else ''
            if field.disabled:
                cur_replace['required'] += 'disabled '
            cur_replace['attrs'] = self.get_format_attrs(name, field)
            # print(self.__class__.__name__, name, field.label, 'attrs:', cur_replace['attrs'], '|', field.widget.attrs, )
            if isinstance(field, EmailField) and name not in field_formats:
                cur_replace['input_type'] = 'email'
            elif isinstance(field.widget, Textarea):
                cur_replace['initial'] = getattr(field, 'initial', None) or ''
                attrs = ''
                cols = field.widget.attrs.get('cols', None)
                rows = field.widget.attrs.get('rows', None)
                if cols:
                    attrs += f'cols="{cols}" '
                if rows:
                    attrs += f'rows="{rows}" '
                cur_replace['attrs'] = attrs
                field_formats[name] = AREA_TXT
            elif isinstance(field.widget, (CheckboxSelectMultiple, RadioSelect)):
                input_type = 'radio' if isinstance(field.widget, RadioSelect) else 'checkbox'
                required = REQUIRED if field.required else ''
                if isinstance(field.widget, CheckboxSelectMultiple):
                    required = ''
                options_re = {'name': name, 'required': required, 'input_type': input_type}
                option_list = []
                for num, each in enumerate(field.choices):
                    val, display = each
                    opt_replace = options_re.copy()
                    opt_replace.update({'num': str(num), 'val': str(val), 'display_choice': str(display)})
                    option = OTHER_OPTION_TXT % opt_replace
                    option_list.append(option)
                cur_replace['options'] = ''.join(option_list)
                field_formats[name] = RADIO_TXT if isinstance(field.widget, RadioSelect) else CHECK_TXT
            elif isinstance(field, BooleanField) or isinstance(field.widget, CheckboxInput):
                cur_replace['input_type'] = 'checkbox'
                cur_replace['attrs'] = ''
            elif isinstance(field.widget, (Select, SelectMultiple)):
                option_list = []
                for num, each in enumerate(field.choices):
                    val, display = each
                    option = OPTION_TXT % {'val': val, 'display_choice': display}
                    option_list.append(option)
                cur_replace['options'] = ''.join(option_list)
                cur_replace['multiple'] = MULTIPLE
                if not isinstance(field.widget, SelectMultiple):
                    cur_replace['multiple'] = ''
                    cur_replace['required'] = ''
                field_formats[name] = SELECT_TXT

            txt = field_formats.get(name, DEFAULT_TXT) % cur_replace
            form_list.append(txt)
        str_hidden = ''.join(hidden_list)
        if len(form_list) > 0:
            last_row = form_list[-1]
            default_re = DEFAULT_RE.copy()
            default_re.update({'attrs': '%(attrs)s', 'end_tag': str_hidden + '%(end_tag)s'})
            form_list[-1] = last_row % default_re
        else:
            form_list.append(str_hidden)
        expected = ''.join(form_list) % setup
        return expected.strip()

    def log_html_diff(self, expected, actual, full=True):
        exp = expected.split('\n')
        out = actual.split('\n')
        line_count = max(len(out), len(exp))
        exp += [''] * (line_count - len(exp))
        out += [''] * (line_count - len(out))
        mid_break = "***********{}***********"
        tail = "\n--------------------------------- Expected vs Actual -------------------------------------------"
        conflicts = []
        for a, b in zip(exp, out):
            matching = a == b
            result = (a, mid_break.format('*' if matching else '** ERROR **'), b, tail)
            if full:
                conflicts.append(result)
            elif not matching:
                conflicts.append(result)
        for row in conflicts:
            print('\n'.join(row))
        return conflicts

    def test_made_user(self, user=None):
        """Confirm the expected user_type was made, using the expected mock or actual user model setup. """
        user_attr = dict(is_active=True, is_authenticated=True, is_anonymous=False, is_staff=False, is_superuser=False)
        attr_by_type = {
            'anonymous': {'is_active': False, 'is_authenticated': False, 'is_anonymous': True},
            'superuser': {'is_staff': True, 'is_superuser': True},
            'staff': {'is_staff': True, 'is_superuser': False},
            'user': {'is_staff': False, 'is_superuser': False},
            'inactive': {'is_staff': False, 'is_superuser': False, 'is_active': False},
            }
        user_attr.update(attr_by_type.get(self.user_type, {}))
        lookup_type = {'anonymous': AnonymousUser, 'superuser': MockSuperUser, 'staff': MockStaffUser, 'user': MockUser}
        user_class = lookup_type.get(self.user_type, None)
        if not self.mock_users and not self.user_type == 'anonymous':
            user_class = get_user_model()
        user = user or self.user
        self.assertIsNotNone(getattr(self, 'user', None))
        self.assertIsNotNone(user_class)
        self.assertIsInstance(user, user_class)
        for key, value in user_attr.items():
            self.assertEqual(value, getattr(self.user, key, None))

    def test_as_table(self):
        """All forms should return HTML table rows when .as_table is called. """
        output = self.form.as_table().strip()
        setup = {'start_tag': '<tr><th>', 'label_end': '</th><td>', 'input_end': '<br>', 'end_tag': '</td></tr>'}
        setup.update(attrs='')
        # override_attrs = 'size="15" ' if issubclass(self.form_class, FormOverrideMixIn) else ''
        # setup.update(attrs=override_attrs)
        if issubclass(self.form_class, FormOverrideMixIn):
            size_default = self.form.get_overrides().get('_default_', {}).get('size', None)
            override_attrs = '' if not size_default else f'size="{size_default}" '
            setup.update(attrs=override_attrs)
        expected = self.get_expected_format(setup)
        if output != expected:
            form_class = self.form.__class__.__name__
            print(f"//////////////////////////////// {form_class} AS_TABLE /////////////////////////////////////")
            if issubclass(self.form_class, ComputedUsernameMixIn):
                print("*** is sub class of ComputedUsernameMixIn ***")
            self.log_html_diff(expected, output, full=False)
        self.assertNotEqual('', output)
        self.assertEqual(expected, output)

    def test_as_ul(self):
        """All forms should return HTML <li>s when .as_ul is called. """
        output = self.form.as_ul().strip()
        setup = {'start_tag': '<li>', 'end_tag': '</li>', 'label_end': ' ', 'input_end': ' ', 'attrs': ''}
        # override_attrs = 'size="15" ' if issubclass(self.form_class, FormOverrideMixIn) else ''
        # setup.update(attrs=override_attrs)
        if issubclass(self.form_class, FormOverrideMixIn):
            size_default = self.form.get_overrides().get('_default_', {}).get('size', None)
            override_attrs = '' if not size_default else f'size="{size_default}" '
            setup.update(attrs=override_attrs)
        expected = self.get_expected_format(setup)
        if output != expected:
            form_class = self.form.__class__.__name__
            print(f"//////////////////////////////// {form_class} AS_UL /////////////////////////////////////")
            if issubclass(self.form_class, ComputedUsernameMixIn):
                print("*** is sub class of ComputedUsernameMixIn ***")
            self.log_html_diff(expected, output, full=False)  # , full=False)
        self.assertNotEqual('', output)
        self.assertEqual(expected, output)

    def test_as_p(self):
        """All forms should return HTML <p>s when .as_p is called. """
        output = self.form.as_p().strip()
        setup = {'start_tag': '<p>', 'end_tag': '</p>', 'label_end': ' ', 'input_end': ' '}
        setup.update(attrs='')
        # override_attrs = 'size="15" ' if issubclass(self.form_class, FormOverrideMixIn) else ''
        # setup.update(attrs=override_attrs)
        if issubclass(self.form_class, FormOverrideMixIn):
            size_default = self.form.get_overrides().get('_default_', {}).get('size', None)
            override_attrs = '' if not size_default else f'size="{size_default}" '
            setup.update(attrs=override_attrs)
        override_attrs = 'size="15" ' if issubclass(self.form_class, FormOverrideMixIn) else ''
        setup.update(attrs=override_attrs)
        expected = self.get_expected_format(setup)
        if output != expected:
            form_class = self.form.__class__.__name__
            print(f"//////////////////////////////// {form_class} AS_P /////////////////////////////////////")
            if issubclass(self.form_class, ComputedUsernameMixIn):
                print("*** is sub class of ComputedUsernameMixIn ***")
            self.log_html_diff(expected, output, full=False)
        self.assertNotEqual('', output)
        self.assertEqual(expected, output)

    @skip("Not Implemented")
    def test_html_output(self):
        """All forms should have a working _html_output method. ? Should it conform to the same API? """
        pass

    def find_focus_field(self):
        """Returns a list of all fields that have been given an HTML attribute of 'autofocus'. """
        fields = self.get_current_fields()
        found_names = []
        for field_name, field in fields.items():
            has_focus = field.widget.attrs.get('autofocus', None)
            if has_focus:
                found_names.append(field_name)
        return found_names

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

    def test_focus_not_on_hidden(self):
        """Focus is never assigned to a hidden field when targeted. """
        target = 'hide_field'
        field = self.form.fields.get(target, None)
        result_name = self.form.assign_focus_field(target)
        focused = self.find_focus_field()

        self.assertTrue(isinstance(getattr(field, 'widget', None), (HiddenInput, MultipleHiddenInput, )))
        self.assertIn(target, self.form.fields)
        self.assertEqual(1, len(focused))
        self.assertNotEqual(target, focused[0])
        self.assertNotEqual(target, result_name)

    def test_focus_not_on_disabled(self):
        """Focus is never assigned to a disabled field when targeted. """
        target = 'disable_field'
        field = self.form.fields.get(target, None)
        result_name = self.form.assign_focus_field(target)
        focused = self.find_focus_field()

        self.assertTrue(field.disabled)
        self.assertIn(target, self.form.fields)
        self.assertEqual(1, len(focused))
        self.assertNotEqual(target, focused[0])
        self.assertNotEqual(target, result_name)

    def test_remove_previous_focus(self):
        """All fields that previously had focus should have it removed when giving focus to another field. """
        target_1 = 'generic_field'
        result_1 = self.form.assign_focus_field(target_1)
        focused_1 = self.find_focus_field()

        target_2 = 'another_field'
        result_2 = self.form.assign_focus_field(target_2)
        focused_2 = self.find_focus_field()

        self.assertNotEqual(target_1, target_2)
        self.assertIn(target_1, self.form.fields)
        self.assertEqual(1, len(focused_1))
        self.assertEqual(target_1, focused_1[0])
        self.assertEqual(target_1, result_1)
        self.assertIn(target_2, self.form.fields)
        self.assertEqual(1, len(focused_2))
        self.assertEqual(target_2, focused_2[0])
        self.assertEqual(target_2, result_2)


class CriticalTests(FormTests, TestCase):
    form_class = CriticalForm

    def test_raise_on_missing_critical(self):
        """If the field is missing or misconfigured, it should raise ImproperlyConfigured. """
        name_for_field = 'absent_field'
        field_opts = {'names': (name_for_field, 'absent'), 'alt_field': '', 'computed': False}
        critical_fields = {'absent_field': field_opts}
        with self.assertRaises(ImproperlyConfigured):
            self.form.fields_for_critical(critical_fields)

    def test_get_critical_from_existing_fields(self):
        """After fields have been formed, get_critical_field should return from fields, not from base_fields. """
        name = 'generic_field'
        opts = {'names': (name, ), 'alt_field': '', 'computed': False}
        expected_field = self.form.fields.get(name, None)
        actual_name, actual_field = self.form.get_critical_field(opts['names'])
        self.assertEqual(name, actual_name)
        self.assertEqual(expected_field, actual_field)

    def get_generic_name(self, name='generic_field'):
        return name if name in self.form.fields else ''

    def test_callable_name_get_critical_field(self):
        """It should work on the returned value if a name in names is a callable. """
        special = self.get_generic_name
        name, field = self.form.get_critical_field(special)
        expected_name = special()
        expected_field = self.form.fields[expected_name]
        self.assertEqual(expected_name, name)
        self.assertEqual(expected_field, field)

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

    def test_manage_tos_field(self):
        """Confirm tos_field is only present when configured to add the field. """
        name = self.form.name_for_tos or 'tos_field'
        initial_is_off = self.form.tos_required is False
        name_in_initial = name in self.form.fields
        found = self.form.fields.get(name, None)
        original_critical = deepcopy(self.form.critical_fields)

        self.form.tos_required = True
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

    def test_validators_attach(self):
        """Confirm that the custom validator on this Form is called and applies the expected validator. """
        field_name = 'generic_field'
        expected = validators.validate_confusables
        field = self.form.fields.get(field_name, None)
        all_validators = field.validators if field else []
        self.assertIn(expected, all_validators)


class ComputedTests(FormTests, TestCase):
    form_class = ComputedForm

    def test_use_existing_computed_field_dict(self):
        """The get_computed_field_names method should include the names when computed_fields is already determined. """
        if isinstance(self.form.computed_fields, list):
            self.form.computed_fields = self.form.get_computed_fields(self.form.computed_fields)
        self.form.fields.update(self.form.computed_fields)  # only names in fields included in get_computed_field_names.
        result_names = self.form.get_computed_field_names([], self.form.fields)

        self.assertIsInstance(self.form.computed_fields, dict)
        self.assertIn('test_field', result_names)

    def test_raise_on_corrupt_computed_fields(self):
        """The computed_field_names method raises ImproperlyConfigured when computed_fields is an unexpected type. """
        initial = self.form.computed_fields
        self.form.computed_fields = 'This is a broken value'
        with self.assertRaises(ImproperlyConfigured):
            self.form.get_computed_field_names([], self.form.fields)
        self.form.computed_fields = None
        with self.assertRaises(ImproperlyConfigured):
            self.form.get_computed_field_names([], self.form.fields)
        self.form.computed_fields = initial

    def test_construct_values_raises_for_missing_fields(self):
        """Raises ImproperlyConfigured for missing cleaned_data on targeted field_names in constructing values. """
        message = "There must me one or more field names to compute a value. "
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            self.form.construct_value_from_values()
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            self.form.construct_value_from_values('')
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            self.form.construct_value_from_values([])

    def test_construct_values_raises_for_missing_cleaned_data(self):
        """Raises ImproperlyConfigured for missing cleaned_data on targeted field_names in constructing values. """
        constructor_fields = ('first', 'second', 'last', )
        if hasattr(self.form, 'cleaned_data'):
            del self.form.cleaned_data
        message = "This method can only be evaluated after 'cleaned_data' has been populated. "
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            self.form.construct_value_from_values(constructor_fields)

    def test_construct_values_skips_already_caught_errors(self):
        """Return None from construct_value_from_values method if the relevant fields already have recorded errors. """
        constructor_fields = ('first', 'second', 'last', )
        values = ['FirstValue', 'SecondValue', 'LastValue']
        expected = None  # Normal is: '_'.join(ea for ea in values if ea).casefold()
        cleaned_data = getattr(self.form, 'cleaned_data', {})
        cleaned_data.update(dict(zip(constructor_fields[:-1], values[:-1])))
        self.form.cleaned_data = cleaned_data
        original_errors = deepcopy(self.form._errors)
        if self.form._errors is None:
            self.form._errors = ErrorDict()  # mimic full_clean: _error is an ErrorDict
        self.form.add_error('last', 'An error for testing')
        actual = self.form.construct_value_from_values(constructor_fields)

        self.assertIsNone(actual)
        self.assertEqual(expected, actual)

        self.form._errors = original_errors

    def test_construct_values_raises_missing_cleaned_no_error(self):
        """Return None from construct_value_from_values method if the relevant fields already have recorded errors. """
        constructor_fields = ('first', 'second', 'last', )
        values = ['FirstValue', 'SecondValue', 'LastValue']
        cleaned_data = getattr(self.form, 'cleaned_data', {})
        cleaned_data.update(dict(zip(constructor_fields[:-1], values[:-1])))
        self.form.cleaned_data = cleaned_data
        err = "This computed value can only be evaluated after fields it depends on have been cleaned. "
        err += "The field order must have the computed field after fields used for its value. "
        with self.assertRaisesMessage(ImproperlyConfigured, err):
            self.form.construct_value_from_values(constructor_fields)

    def test_construct_values_raises_on_invalid_normalize(self):
        """The normalize parameter can be None or a callback function, otherwise raise ImproperlyConfigured. """
        constructor_fields = ('first', 'second', 'last', )
        values = ['first_value', 'second_value', 'last_value']
        cleaned_data = getattr(self.form, 'cleaned_data', {})
        cleaned_data.update(dict(zip(constructor_fields, values)))
        self.form.cleaned_data = cleaned_data
        normalize = 'not a valid normalize function'
        message = "The normalize parameter must be a callable or None. "
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            self.form.construct_value_from_values(constructor_fields, normalize=normalize)

    def test_construct_values_as_expected(self):
        """Get the expected response when given valid inputs when constructing values. """
        constructor_fields = ('first', 'second', 'last', )
        values = ['FirstValue', 'SecondValue', 'LastValue']
        expected = '_**_'.join(ea for ea in values if ea).casefold()
        cleaned_data = getattr(self.form, 'cleaned_data', {})
        cleaned_data.update(dict(zip(constructor_fields, values)))
        self.form.cleaned_data = cleaned_data
        actual = self.form.construct_value_from_values(constructor_fields, '_**_')
        simple = self.form.construct_value_from_values(constructor_fields)

        self.assertEqual(expected, actual)
        self.assertEqual('firstvalue_**_secondvalue_**_lastvalue', actual)
        self.assertEqual('_'.join(values).casefold(), simple)
        self.assertEqual('firstvalue_secondvalue_lastvalue', simple)

    def test_construct_values_no_join_artifact_if_empty_value(self):
        """Raises ImproperlyConfigured for missing cleaned_data on targeted field_names in constructing values. """
        constructor_fields = ('first', 'second', 'last', )
        values = ['FirstValue', 'SecondValue', 'LastValue']
        values[1] = ''
        expected = '_'.join(ea for ea in values if ea).casefold()
        cleaned_data = getattr(self.form, 'cleaned_data', {})
        cleaned_data.update(dict(zip(constructor_fields, values)))
        self.form.cleaned_data = cleaned_data
        actual = self.form.construct_value_from_values(constructor_fields)

        self.assertEqual('', self.form.cleaned_data['second'])
        self.assertEqual(expected, actual)
        self.assertEqual('firstvalue_lastvalue', actual)

    def test_construct_values_calls_passed_normalize_function(self):
        """When a function is passed for normalize, it is used in constructing values. """
        constructor_fields = ('first', 'second', 'last', )
        values = ['FiRsT_FaLue', 'sEcOnd_vAlUE', 'LaST_VaLue']
        expected = '_'.join(ea for ea in values if ea).casefold()
        cleaned_data = getattr(self.form, 'cleaned_data', {})
        cleaned_data.update(dict(zip(constructor_fields, values)))
        self.form.cleaned_data = cleaned_data
        def normal_lower(val): return val.lower()
        def normal_upper(val): return val.upper()
        lower = self.form.construct_value_from_values(constructor_fields, normalize=normal_lower)
        upper = self.form.construct_value_from_values(constructor_fields, normalize=normal_upper)

        self.assertEqual(expected.lower(), lower)
        self.assertEqual(expected.upper(), upper)

    def test_cleaned_data_modified_by_clean_computed_fields(self):
        """A computed field's custom compute method is called when appropriate in the _clean_computed_fields method. """
        name = 'test_field'
        field = self.form.computed_fields.get(name)  # getattr(self.form, name) for BoundField instance for Field.
        value = self.form.compute_test_field()
        value = field.clean(value)
        expected = self.form.test_func(value)
        if isinstance(self.form.computed_fields, (list, tuple)):
            self.form.computed_fields = self.form.get_computed_fields([name])
        original_errors = deepcopy(self.form._errors)
        if self.form._errors is None:
            self.form._errors = ErrorDict()  # mimic full_clean: _error is an ErrorDict
        self.form.cleaned_data = getattr(self.form, 'cleaned_data', {})  # mimic full_clean: cleaned_data is present
        original = self.form.cleaned_data.get(name, None)
        compute_errors = self.form._clean_computed_fields()
        actual = self.form.cleaned_data.get(name, '')

        self.assertFalse(compute_errors)
        self.assertNotEqual(original, actual)
        self.assertNotEqual(original, expected)
        self.assertEqual(expected, actual)

        self.form._errors = original_errors

    def test_field_compute_method_called_in_clean_computed_fields(self):
        """A computed field's custom compute method is called when appropriate in the _clean_computed_fields method. """
        name = 'test_field'
        expected = 'compute_confirmed'
        self.form.test_value = expected
        modified = self.form.test_func(expected)
        original_func = deepcopy(self.form.test_func)
        def pass_through(value): return value
        self.form.test_func = pass_through
        if isinstance(self.form.computed_fields, (list, tuple)):
            self.form.computed_fields = self.form.get_computed_fields([name])
        original_errors = deepcopy(self.form._errors)
        if self.form._errors is None:
            self.form._errors = ErrorDict()  # mimic full_clean: _error is an ErrorDict
        self.form.cleaned_data = getattr(self.form, 'cleaned_data', {})  # mimic full_clean: cleaned_data is present
        compute_errors = self.form._clean_computed_fields()
        actual = self.form.cleaned_data.get(name, None)

        self.assertFalse(compute_errors)
        self.assertEqual(expected, actual)

        self.form.test_func = original_func
        restored = self.form.test_func(expected)
        self.assertEqual(modified, restored)
        self.form._errors = original_errors

    def test_field_clean_method_called_in_clean_computed_fields(self):
        """A computed field's custom clean method is called when appropriate in the _clean_computed_fields method. """
        name = 'test_field'
        expected = 'clean_confirmed'
        original_func = deepcopy(self.form.test_func)
        def replace_value(value): return expected
        self.form.test_func = replace_value
        if isinstance(self.form.computed_fields, (list, tuple)):
            self.form.computed_fields = self.form.get_computed_fields([name])
        field = self.form.computed_fields.get(name)  # getattr(self.form, name)
        # initial_value = self.get_initial_for_field(field, name)
        value = getattr(self.form, 'compute_%s' % name)()
        value = field.clean(value)
        original_errors = deepcopy(self.form._errors)
        if self.form._errors is None:
            self.form._errors = ErrorDict()  # mimic full_clean: _error is an ErrorDict
        cleaned_data = getattr(self.form, 'cleaned_data', {})
        cleaned_data.update({name: value})  # make sure the original cleaned_data for the field is set.
        self.form.cleaned_data = cleaned_data  # ensure cleaned_data is present (mimic full_clean)
        compute_errors = self.form._clean_computed_fields()
        actual = self.form.cleaned_data.get(name, None)

        self.assertFalse(compute_errors)
        self.assertEqual(expected, actual)
        self.assertNotEqual(expected, value)
        self.assertNotEqual(expected, self.form.test_value)

        self.form.test_func = original_func
        self.form._errors = original_errors

    def test_validation_errors_assigned_in_clean_computed_fields(self):
        """Test output of _clean_computed_fields. Should be an ErrorDict with computed field name(s) as key(s). """
        name = 'test_field'
        message = "This is the test error on test_field. "
        response = ValidationError(message)
        expected_compute_errors = ErrorDict({name: response})  # similar to return of _clean_computed_fields
        original_func = deepcopy(self.form.test_func)
        def make_error(value): raise response
        self.form.test_func = make_error
        if isinstance(self.form.computed_fields, (list, tuple)):
            self.form.computed_fields = self.form.get_computed_fields([name])
        self.form.cleaned_data = getattr(self.form, 'cleaned_data', {})  # mimic full_clean: cleaned_data is present
        actual_compute_errors = self.form._clean_computed_fields()

        self.assertDictEqual(expected_compute_errors, actual_compute_errors)

        self.form.test_func = original_func

    def test_validation_error_for_compute_error(self):
        """The Form's clean method calls _clean_computed_fields method and response populates Form._errors. """
        name = 'test_field'
        message = "This is the test error on test_field. "
        response = ValidationError(message)
        # expected_compute_errors = ErrorDict({name: response})  # similar to return of _clean_computed_fields
        original_errors = deepcopy(self.form._errors)
        expected_errors = ErrorDict()  # similar to Form.full_clean
        expected_errors[name] = self.form.error_class()
        expected_errors[name].append(response)  # similar to add_error(None, message) in _clean_computed...
        clean_message_on_compute_errors = "Error occurred with the computed fields. "
        clean_error_on_compute_errors = ValidationError(clean_message_on_compute_errors)
        expected_errors[NON_FIELD_ERRORS] = self.form.error_class(error_class='nonfield')  # first add_error(None, err)
        expected_errors[NON_FIELD_ERRORS].append(clean_error_on_compute_errors)  # similar to add_error(None, string)

        original_func = deepcopy(self.form.test_func)
        def make_error(value): raise response
        self.form.test_func = make_error
        if isinstance(self.form.computed_fields, (list, tuple)):
            self.form.computed_fields = self.form.get_computed_fields([name])
        if self.form._errors is None:
            self.form._errors = ErrorDict()  # mimic full_clean: _error is an ErrorDict
        original_cleaned_data = getattr(self.form, 'cleaned_data', None)
        self.form.cleaned_data = getattr(self.form, 'cleaned_data', {})  # mimic full_clean: cleaned_data is present
        self.form._clean_form()  # adds to Form._error if ValidationError raised by Form.clean.

        self.assertNotEqual(original_errors, self.form._errors)
        self.assertEqual(expected_errors, self.form._errors)

        if original_cleaned_data is None:
            del self.form.cleaned_data
        else:
            self.form.cleaned_data = original_cleaned_data
        self.form._errors = original_errors
        self.form.test_func = original_func

    def test_cleaned_data_for_compute_error(self):
        """The cleaned_data is removed of data for computed_fields if there is an error from _clean_computed_fields. """
        name = 'test_field'
        message = "This is the test error on test_field. "
        original_errors = deepcopy(self.form._errors)
        response = ValidationError(message)
        original_func = deepcopy(self.form.test_func)
        def make_error(value): raise response
        self.form.test_func = make_error
        if isinstance(self.form.computed_fields, (list, tuple)):
            self.form.computed_fields = self.form.get_computed_fields([name])
        computed_names = list(self.form.computed_fields.keys())
        field_names = list(self.form.fields.keys())
        field_data = {f_name: f"input_{f_name}_{i}" for i, f_name in enumerate(field_names)}
        if self.form._errors is None:
            self.form._errors = ErrorDict()  # mimic full_clean: _error is an ErrorDict
        original_cleaned_data = deepcopy(getattr(self.form, 'cleaned_data', None))
        populated_cleaned_data = deepcopy(original_cleaned_data or {})
        populated_cleaned_data.update(field_data)
        populated_cleaned_data.update({name: f"value_{f_name}_{i}" for i, f_name in enumerate(computed_names)})
        self.form.cleaned_data = populated_cleaned_data.copy()  # ensure cleaned_data is present (mimic full_clean)

        with self.assertRaises(ValidationError):
            self.form.clean()
        final_cleaned_data = self.form.cleaned_data

        self.assertIn(name, computed_names)
        self.assertNotIn(name, field_names)
        self.assertIn(name, populated_cleaned_data)
        self.assertNotIn(name, final_cleaned_data)
        self.assertNotEqual(original_cleaned_data, final_cleaned_data)
        self.assertNotEqual(populated_cleaned_data, final_cleaned_data)

        if original_cleaned_data is None:
            del self.form.cleaned_data
        else:
            self.form.cleaned_data = original_cleaned_data
        self.form._errors = original_errors
        self.form.test_func = original_func

    def test_cleaned_data_for_compute_success(self):
        """The Form's clean process populates cleaned_data with computed_fields data when there are no errors. """
        name = 'test_field'
        if isinstance(self.form.computed_fields, (list, tuple)):
            self.form.computed_fields = self.form.get_computed_fields([name])
        computed_names = list(self.form.computed_fields.keys())
        field_names = list(self.form.fields.keys())
        field_data = {f_name: f"input_{f_name}_{i}" for i, f_name in enumerate(field_names)}
        field_data.update({name: f"value_{f_name}_{i}" for i, f_name in enumerate(computed_names)})
        original_errors = deepcopy(self.form._errors)
        if self.form._errors is None:
            self.form._errors = ErrorDict()  # mimic full_clean: _error is an ErrorDict
        original_cleaned_data = deepcopy(getattr(self.form, 'cleaned_data', None))
        populated_cleaned_data = deepcopy(original_cleaned_data or {})
        populated_cleaned_data.update(field_data)
        self.form.cleaned_data = populated_cleaned_data.copy()  # ensure cleaned_data is present (mimic full_clean)
        final_cleaned_data = self.form.clean()

        self.assertIn(name, computed_names)
        self.assertNotIn(name, field_names)
        self.assertIn(name, populated_cleaned_data)
        self.assertIn(name, final_cleaned_data)
        self.assertNotEqual(original_cleaned_data, final_cleaned_data)

        if original_cleaned_data is None:
            del self.form.cleaned_data
        else:
            self.form.cleaned_data = original_cleaned_data
        self.form._errors = original_errors

    def test_clean_moves_computed_fields_to_fields(self):
        """If no errors, clean method adds all compute_fields to fields. """
        name = 'test_field'
        if isinstance(self.form.computed_fields, (list, tuple)):
            self.form.computed_fields = self.form.get_computed_fields([name])
        computed_names = list(self.form.computed_fields.keys())
        field_names = list(self.form.fields.keys())
        field_data = {f_name: f"input_{f_name}_{i}" for i, f_name in enumerate(field_names)}
        field_data.update({name: f"value_{f_name}_{i}" for i, f_name in enumerate(computed_names)})
        original_data = self.form.data
        original_fields = self.form.fields
        original_computed_fields = self.form.computed_fields
        original_errors = getattr(self.form, '_errors', None)
        original_cleaned_data = getattr(self.form, 'cleaned_data', None)
        self.form.data = original_data.copy()
        self.form.fields = original_fields.copy()
        self.form.computed_fields = original_computed_fields.copy()
        self.form._errors = ErrorDict() if original_errors is None else original_errors.copy()  # mimic full_clean
        populated_cleaned_data = deepcopy(original_cleaned_data or {})
        populated_cleaned_data.update(field_data)
        self.form.cleaned_data = populated_cleaned_data.copy()  # ensure cleaned_data is present (mimic full_clean)
        final_cleaned_data = self.form.clean()

        self.assertIn(name, computed_names)
        self.assertNotIn(name, field_names)
        self.assertEqual(1, len(computed_names))
        self.assertIn(name, self.form.fields)
        self.assertNotEqual(original_cleaned_data, final_cleaned_data)

        self.form.data = original_data
        self.form.fields = original_fields
        self.form.computed_fields = original_computed_fields
        self.form._errors = original_errors
        self.form.cleaned_data = original_cleaned_data
        if original_errors is None:
            del self.form._errors
        if original_cleaned_data is None:
            del self.form.cleaned_data


class OverrideTests(FormTests, TestCase):
    form_class = OverrideForm
    alt_field_info = {
        'alt_test_feature': {
            'first': {
                    'label': "Alt First Label",
                    'help_text': '',
                    'initial': 'alt_first_initial', },
            'last': {
                    'label': None,
                    'initial': 'alt_last_initial',
                    'help_text': '', },
            },
        'alt_test_no_method': {
            'second': {
                    'label': "Alt Second Label",
                    'help_text': '',
                    'initial': 'alt_second_initial', },
            'generic_field': {
                    'label': None,
                    'initial': 'alt_generic_field_initial',
                    'help_text': '', },
            },
        }
    formfield_attrs_overrides = {
        '_default_': {'size': 15, 'cols': 20, 'rows': 4, },
        'first': {'maxlength': '191', 'size': '20', },
        'second': {'maxlength': '2', 'size': '2', },  # 'size': '2',
        'last': {'maxlength': '2', 'size': '5', },
        }

    def setUp(self):
        super().setUp()
        fd = self.form.fields
        test_initial = {'first': fd['first'].initial, 'second': fd['second'].initial, 'last': fd['last'].initial}
        test_initial['generic_field'] = fd['generic_field'].initial
        test_data = MultiValueDict()
        test_data.update({name: f"test_value_{name}" for name in test_initial})
        self.test_initial = test_initial
        self.test_data = test_data

    def test_set_alt_data_single(self):
        """Get expected results when passing name, field, value, but not data. """
        name, value = 'generic_field', 'alt_data_value'
        field = self.form.fields.get(name, None)
        self.assertIsNotNone(field, "Unable to find the expected field in current fields. ")

        original_form_data = self.form.data
        test_data = self.test_data.copy()
        test_data.update({name: self.test_initial[name]})
        test_data._mutable = False
        self.form.data = test_data
        initial_data = test_data.copy()
        expected_data = test_data.copy()
        expected_data.update({name: value})

        initial_val = self.form.get_initial_for_field(field, name)
        data_name = self.form.add_prefix(name)
        data_val = field.widget.value_from_datadict(self.form.data, self.form.files, data_name)
        use_alt_value = not field.has_changed(initial_val, data_val)
        expected_value = value if use_alt_value else initial_data.get(name)
        expected_result = {name: value} if use_alt_value else {}
        result = self.form.set_alt_data(data=None, name=name, field=field, value=value)

        self.assertEqual(self.test_initial[name], initial_val)
        self.assertEqual(initial_data[name], data_val)
        self.assertEqual(expected_value, self.form.data[name])
        self.assertDictEqual(expected_result, result)
        for key in initial_data:
            self.assertEqual(expected_data[key], self.form.data[key])
        self.assertEqual(len(expected_data), len(self.form.data))
        self.assertTrue(use_alt_value)

        self.form.data = original_form_data

    def test_set_alt_data_collection(self):
        """Get expected results when passing data but not any for name, field, value. """
        names = list(self.test_data.keys())[1:-1]
        alt_values = {name: f"alt_value_{name}" for name in self.test_initial}  # some, but not all, will be used.

        original_form_data = self.form.data
        test_data = self.test_data.copy()
        test_data.update({name: val for name, val in self.test_initial.items() if name not in names})
        test_data._mutable = False
        self.form.data = test_data
        initial_data = test_data.copy()
        expected_result = {name: val for name, val in alt_values.items() if name not in names}
        expected_data = test_data.copy()
        expected_data.update(expected_result)

        expect_updates = any(self.data_is_initial(name) for name in initial_data)
        test_input = {name: (self.form.fields[name], val) for name, val in alt_values.items()}
        result = self.form.set_alt_data(test_input)

        self.assertDictEqual(expected_result, result)
        self.assertDictEqual(expected_data, self.form.data)
        self.assertNotEqual(initial_data, self.form.data)
        self.assertTrue(expect_updates)
        self.assertIsNot(test_data, self.form.data)

        self.form.data = original_form_data

    def data_is_initial(self, name):
        field = self.form.fields[name]
        return not field.has_changed(self.test_initial.get(name), self.form.data.get(name))

    def test_set_alt_data_mutable(self):
        """After running set_alt_data that triggers changes, the Form's data attribute should have _mutable = False. """
        # from pprint import pprint
        original_test_initial = self.test_initial
        original_form_data = self.form.data
        initial = self.test_initial
        test_data = self.test_data.copy()
        test_data.update({name: initial[name] for name in list(initial.keys())[1:-1]})  # two fields for alt_values
        test_data._mutable = False
        self.form.data = test_data
        initial_data = test_data.copy()

        alt_values = {name: f"alt_value_{name}" for name in initial}  # some, but not all, will be used.
        unchanged_fields = {name: val for name, val in test_data.items() if val == initial[name]}
        expected_result = {name: alt_values[name] for name in unchanged_fields}
        expected_data = test_data.copy()
        expected_data.update(expected_result)

        expect_updates = any(self.data_is_initial(name) for name in initial_data)
        test_input = {name: (self.form.fields[name], val) for name, val in alt_values.items()}
        result = self.form.set_alt_data(test_input)
        had_updates = any(value != self.form.data[name] for name, value in initial_data.items())
        # print("====================== test_set_alt_data_mutable =======================")
        # pprint(expected_result)
        # print("--------------------------------------------------")
        # pprint(result)
        # print("--------------------------------------------------")
        # pprint(expected_data)
        # print("--------------------------------------------------")
        # pprint(self.form.data)
        # print("------------------END SECTION---------------------------")
        # pprint(initial)
        # print("--------------------------------------------------")
        # pprint(test_data)
        # print("========================= SET ALT DATA ==========================================")
        for name, val in expected_data.items():
            # print(name, " :  ", initial[name], "\n")
            # print(val)
            # print("-----------------------------------------------")
            # print(self.form.data[name])
            # print("***********************************************")
            self.assertEqual(val, self.form.data[name])
        self.assertTrue(expect_updates)
        self.assertTrue(had_updates)
        self.assertFalse(getattr(self.form.data, '_mutable', True))
        self.assertDictEqual(expected_result, result)
        self.assertDictEqual(expected_data, self.form.data)

        self.form.data = original_form_data
        self.test_initial = original_test_initial

    def test_set_alt_data_unchanged(self):
        """If all fields are not changed, then the Form's data is not overwritten. """
        original_form_data = self.form.data
        test_data = self.test_data.copy()
        test_data._mutable = False
        self.form.data = test_data
        initial_data = test_data.copy()

        alt_values = {name: f"alt_value_{name}" for name in self.test_initial}
        test_input = {name: (self.form.fields[name], val) for name, val in alt_values.items()}
        expect_updates = any(self.data_is_initial(name) for name in initial_data)
        result = self.form.set_alt_data(test_input)
        had_updates = any(self.form.data[name] != value for name, value in initial_data.items())

        self.assertFalse(expect_updates)
        self.assertFalse(had_updates)
        self.assertDictEqual({}, result)
        self.assertDictEqual(initial_data, self.form.data)
        self.assertIs(test_data, self.form.data)

        self.form.data = original_form_data

    @skip("Not Implemented")
    def test_good_practice_attrs(self):
        """Need feature tests. Already has coverage through other processes. """
        # FormOverrideMixIn.good_practice_attrs
        pass

    @skip("Not Implemented")
    def test_get_overrides(self):
        """Need feature tests. Already has coverage through other processes. """
        # FormOverrideMixIn.get_overrides
        pass

    def test_update_condition_true(self):
        """For a field name condition_<name> method returning true, updates the result as expected. """
        original_alt_info = getattr(self.form, 'alt_field_info', None)
        expected_label = 'alt_test_feature'
        test_method = getattr(self.form, 'condition_' + expected_label, None)
        alt_info = getattr(self, 'alt_field_info', None)
        expected = alt_info.get(expected_label, None)
        self.form.alt_field_info = alt_info
        self.form.test_condition_response = True
        actual = self.form.get_alt_field_info()

        self.assertIsNotNone(alt_info)
        self.assertIsNotNone(test_method)
        self.assertTrue(test_method())
        self.assertIsNotNone(expected)
        self.assertIn(expected_label, alt_info)
        self.assertEqual(expected, actual)

        self.form.test_condition_response = False
        self.form.alt_field_info = original_alt_info
        if original_alt_info is None:
            del self.form.alt_field_info

    def test_update_condition_false(self):
        """For a field name condition_<name> method returning False, does NOT update the result. """
        original_alt_info = getattr(self.form, 'alt_field_info', None)
        expected_label = 'alt_test_feature'
        test_method = getattr(self.form, 'condition_' + expected_label, None)
        alt_info = getattr(self, 'alt_field_info', None)
        expected = {}
        self.form.alt_field_info = alt_info
        self.form.test_condition_response = False
        actual = self.form.get_alt_field_info()

        self.assertIsNotNone(alt_info)
        self.assertIsNotNone(test_method)
        self.assertFalse(test_method())
        self.assertIsNotNone(expected)
        self.assertIn(expected_label, alt_info)
        self.assertEqual(expected, actual)

        self.form.test_condition_response = False
        self.form.alt_field_info = original_alt_info
        if original_alt_info is None:
            del self.form.alt_field_info

    def test_update_condition_not_defined(self):
        """If a condition_<name> method is not defined, then assume False and do NOT update the result. """
        original_alt_info = getattr(self.form, 'alt_field_info', None)
        expected_label = 'alt_test_no_method'
        label_for_used_attrs = 'alt_test_feature'
        test_method = getattr(self.form, 'condition_' + expected_label, None)
        alt_info = getattr(self, 'alt_field_info', None)
        expected = alt_info.get(label_for_used_attrs, None)
        self.form.alt_field_info = alt_info
        self.form.test_condition_response = True
        actual = self.form.get_alt_field_info()

        self.assertIsNotNone(alt_info)
        self.assertIsNone(test_method)
        self.assertIsNotNone(expected)
        self.assertIn(expected_label, alt_info)
        self.assertEqual(expected, actual)

        self.form.test_condition_response = False
        self.form.alt_field_info = original_alt_info
        if original_alt_info is None:
            del self.form.alt_field_info

    @skip("Not Implemented")
    def test_get_flat_fields_setting(self):
        """Need feature tests. Already has coverage through other processes. """
        # FormOverrideMixIn.get_flat_fields_setting
        pass

    @skip("Not Implemented")
    def test_handle_modifiers(self):
        """Need feature tests. Already has coverage through other processes. """
        # FormOverrideMixIn.handle_modifiers
        pass

    def test_unchanged_handle_removals(self):
        """Unchanged fields if 'remove_field_names' and 'removed_fields' are empty. """
        original_fields = self.form.fields
        fields = original_fields.copy()
        self.form.removed_fields = {}
        self.form.remove_field_names = []
        result = self.form.handle_removals(fields)

        self.assertEqual(len(original_fields), len(result))
        self.assertEqual(0, len(self.form.removed_fields))
        self.assertEqual(0, len(self.form.remove_field_names))
        self.assertDictEqual(original_fields, result)
        self.assertIs(fields, result)

    def test_handle_removals_missing_remove_field_names(self):
        """Raises ImproperlyConfigured. Should not be called in ComputedFieldsMixIn, otherwise property was set. """
        original_fields = self.form.fields
        fields = original_fields.copy()
        if hasattr(self.form, 'remove_field_names'):
            del self.form.remove_field_names

        with self.assertRaises(ImproperlyConfigured):
            self.form.handle_removals(fields)

    def test_handle_removals_missing_removed_fields(self):
        """Unchanged fields. Form does not have removed_fields property initially, but it is added. """
        original_fields = self.form.fields
        fields = original_fields.copy()
        self.form.remove_field_names = []
        if hasattr(self.form, 'removed_fields'):
            del self.form.removed_fields
        result = self.form.handle_removals(fields)

        self.assertTrue(hasattr(self.form, 'removed_fields'))
        self.assertEqual(len(original_fields), len(result))
        self.assertEqual(0, len(self.form.removed_fields))
        self.assertEqual(0, len(self.form.remove_field_names))
        self.assertDictEqual(original_fields, result)
        self.assertIs(fields, result)

    def test_handle_removals_remove_field_names(self):
        """Fields whose name is in remove_field_names are removed from fields (with no form data). """
        original_fields = self.form.fields
        fields = original_fields.copy()
        remove_names = ['second', 'last']
        expected_fields = {name: field for name, field in fields.items() if name not in remove_names}
        self.form.removed_fields = {}
        self.form.remove_field_names = remove_names
        result = self.form.handle_removals(fields)

        self.assertEqual(len(original_fields), len(result) + len(remove_names))
        self.assertEqual(len(remove_names), len(self.form.removed_fields))
        self.assertEqual(0, len(self.form.remove_field_names))
        self.assertDictEqual(expected_fields, result)
        self.assertIs(fields, result)

    def test_handle_removals_named_fields_not_in_data(self):
        """Fields whose name is in remove_field_names, but not named in form data, are removed from fields. """
        original_fields = self.form.fields
        fields = original_fields.copy()
        remove_names = ['second', 'last']
        original_data = self.form.data
        data = original_data.copy()
        data.appendlist(remove_names[1], 'test_data_last')
        data._mutable = False
        self.form.data = data
        expected_fields = {name: field for name, field in fields.items() if name != remove_names[0]}
        self.form.removed_fields = {}
        self.form.remove_field_names = remove_names
        result = self.form.handle_removals(fields)

        self.assertEqual(len(original_fields), len(result) + len(remove_names) - 1)
        self.assertEqual(len(remove_names) - 1, len(self.form.removed_fields))
        self.assertEqual(1, len(self.form.remove_field_names))
        self.assertDictEqual(expected_fields, result)
        self.assertIs(fields, result)

        self.form.data = original_data

    def test_handle_removals_add_if_named_in_attribute(self):
        """False goal. The removed_fields are only moved to fields by having a value in the submitted form data. """
        self.assertFalse(False)

    def test_handle_removals_add_if_named_in_data(self):
        """Needed fields currently in removed_fields are added to the Form's fields. """
        original_data = self.form.data
        original_fields = self.form.fields
        fields = original_fields.copy()
        remove_names = ['second', 'last']
        self.form.removed_fields = {name: fields.pop(name) for name in remove_names if name in fields}
        self.form.remove_field_names = []
        expected_fields = dict(**fields, **self.form.removed_fields)
        test_data = original_data.copy()
        test_data.update({name: f"value_{name}" for name in remove_names})
        test_data._mutable = False
        self.form.data = test_data
        result = self.form.handle_removals(fields)

        self.assertEqual(len(original_fields), len(result))
        self.assertEqual(0, len(self.form.removed_fields))
        self.assertEqual(0, len(self.form.remove_field_names))
        self.assertDictEqual(expected_fields, result)
        self.assertDictEqual(original_fields, result)
        self.assertIs(fields, result)

        self.data = original_data

    def test_handle_removals_add_only_if_not_in_remove(self):
        """False goal, adding takes precedence. Adding only triggered because a value is inserted in form data. """
        self.assertFalse(False)

    # @skip("Not Implemented")
    def test_prep_overrides(self):
        """Applies overrides of field widget attrs if name is in overrides. """
        # from pprint import pprint
        original_data = self.form.data
        test_data = original_data.copy()
        test_data._mutable = False
        self.form.data = test_data  # copied only to allow tear-down reverting to original.
        original_fields = self.form.fields
        test_fields = original_fields.copy()
        self.form.fields = test_fields  # copied to allow tear-down reverting to original.
        original_get_overrides = self.form.get_overrides
        def replace_overrides(): return self.formfield_attrs_overrides
        self.form.get_overrides = replace_overrides
        original_alt_field_info = getattr(self.form, 'alt_field_info', None)
        self.form.alt_field_info = {}
        overrides = self.formfield_attrs_overrides.copy()
        DEFAULT = overrides.pop('_default_')
        expected_attrs = {}
        for name, field in test_fields.items():
            attrs = field.widget.attrs.copy()
            if isinstance(field.widget, (RadioSelect, CheckboxSelectMultiple, CheckboxInput, )):
                pass  # update if similar section in prep_fields is updated.
            attrs.update(overrides.get(name, {}))
            # TODO: setup structure for using default or defined version for all CharFields.
            no_resize = overrides.get(name, {}).pop('no_size_override', False)
            no_resize = True if isinstance(field.widget, (HiddenInput, MultipleHiddenInput)) else no_resize
            if no_resize:
                expected_attrs[name] = attrs
                continue  # None of the following size overrides are applied for this field.
            if isinstance(field.widget, Textarea):
                width_attr_name = 'cols'
                default = DEFAULT.get('cols', None)
                display_size = attrs.get('cols', None)
                if 'rows' in DEFAULT:
                    height = attrs.get('rows', None)
                    height = min((DEFAULT['rows'], int(height))) if height else DEFAULT['rows']
                    attrs['rows'] = str(height)
                if default:  # For textarea, we always override. The others depend on different conditions.
                    display_size = display_size or default
                    display_size = min((int(display_size), int(default)))
            elif issubclass(field.__class__, CharField):
                width_attr_name = 'size'  # 'size' is only valid for input types: email, password, tel, text
                default = DEFAULT.get('size', None)  # Cannot use float("inf") as an int.
                display_size = attrs.get('size', None)
            else:  # This field does not have a size setting.
                width_attr_name, default, display_size = None, None, None
            input_size = attrs.get('maxlength', None)
            possible_size = [int(ea) for ea in (display_size or default, input_size) if ea]
            # attrs['size'] = str(int(min(float(display_size), float(input_size))))  # Can't use float("inf") as an int.
            if possible_size and width_attr_name:
                attrs[width_attr_name] = str(min(possible_size))
            expected_attrs[name] = attrs
        # print("======================== test_prep_overrides ============================")
        # formfield_attrs_overrides = {
        #     '_default_': {'size': 15, 'cols': 20, 'rows': 4, },
        #     'first': {'maxlength': 191, 'size': 20, },
        #     'second': {'maxlength': 2, },  # 'size': 2,
        #     'last': {'maxlength': 2, 'size': 5, },
        #     }
        result_fields = self.form.prep_fields()
        result_attrs = {name: field.widget.attrs.copy() for name, field in result_fields.items()}

        first_maxlength = expected_attrs['first']['maxlength']  # overrides['first']['maxlength']
        first_size = expected_attrs['first']['size']  # overrides['first']['size']
        second_maxlength = expected_attrs['second']['maxlength']  # overrides['second']['maxlength']
        last_maxlength = expected_attrs['last']['maxlength']  # overrides['last']['maxlength']
        last_size = expected_attrs['last']['size']  # overrides['last']['size']
        # tests
        self.assertEqual(first_maxlength, result_fields['first'].widget.attrs.get('maxlength', None))
        self.assertEqual(first_size, result_fields['first'].widget.attrs.get('size', None))
        self.assertEqual(second_maxlength, result_fields['second'].widget.attrs.get('maxlength', None))
        self.assertEqual(last_maxlength, result_fields['last'].widget.attrs.get('maxlength', None))
        self.assertEqual(last_size, result_fields['last'].widget.attrs.get('size', None))
        for key, val in expected_attrs.items():
            # print(key, "\n")
            # pprint(val)
            # print("--------------------------------------------------------------------------------")
            # pprint(result_attrs[key])
            # print("********************************************************************************")
            self.assertEqual(val, result_attrs[key])
        self.assertDictEqual(expected_attrs, result_attrs)
        # tear-down: reset back to original state.
        self.form.alt_field_info = original_alt_field_info
        if original_alt_field_info is None:
            del self.form.alt_field_info
        self.form.fields = original_fields
        self.form.data = original_data
        self.form.get_overrides = original_get_overrides

    @skip("Not Implemented")
    def test_prep_textarea(self):
        """Applies expected measurements for a textarea form input. """
        pass

    @skip("Not Implemented")
    def test_prep_charfield_size(self):
        """Applies expected measurements for a charfield form input. """
        pass

    @skip("Not Implemented")
    def test_prep_not_size(self):
        """Does not apply measurements if it is not an appropriate form input type. """
        pass

    # @skip("Not Implemented")
    def test_prep_field_properties(self):
        """If field name is in alt_field_info, the field properties are modified as expected (field.<thing>). """
        # from pprint import pprint
        original_data = self.form.data
        test_data = original_data.copy()
        # modify values in data
        test_data._mutable = False
        self.form.data = test_data
        original_fields = self.form.fields
        test_fields = original_fields.copy()
        # modify fields
        self.form.fields = test_fields
        test_fields_info = {name: field.__dict__.copy() for name, field in test_fields.items()}
        original_get_overrides = self.form.get_overrides
        def skip_overrides(): return {}
        self.form.get_overrides = skip_overrides
        original_alt_field_info = getattr(self.form, 'alt_field_info', None)
        self.form.alt_field_info = self.alt_field_info
        self.form.test_condition_response = True
        expected_fields_info = test_fields_info.copy()
        # print("======================== test_prep_field_properties ============================")
        # {'alt_test_feature': {
        #     'first': {
        #             'label': "Alt First Label",
        #             'help_text': '',
        #             'initial': 'alt_first_initial', },
        #     'last': {
        #             'label': None,
        #             'initial': 'alt_last_initial',
        #             'help_text': '', },
        #     }}
        result_fields = self.form.prep_fields()
        result_fields_info = {name: field.__dict__.copy() for name, field in result_fields.items()}

        modified_info = self.alt_field_info['alt_test_feature']
        first_label = modified_info['first']['label']
        first_initial = modified_info['first']['initial']
        last_initial = modified_info['last']['initial']
        for name, opts in modified_info.items():
            expected_fields_info[name].update(opts)
        # tests
        self.assertEqual(first_label, result_fields['first'].label)
        self.assertEqual(first_initial, result_fields['first'].initial)
        self.assertEqual(last_initial, result_fields['last'].initial)
        for key, val in expected_fields_info.items():
            # print(key, "\n")
            # pprint(val)
            # print("--------------------------------------------------------------------------------")
            # pprint(result_fields_info[key])
            # print("********************************************************************************")
            self.assertEqual(val, result_fields_info[key])
        self.assertDictEqual(expected_fields_info, result_fields_info)
        # tear-down: reset back to original state.
        self.form.test_condition_response = False
        self.form.alt_field_info = original_alt_field_info
        if original_alt_field_info is None:
            del self.form.alt_field_info
        self.form.fields = original_fields
        self.form.data = original_data
        self.form.get_overrides = original_get_overrides

    @skip("Not Implemented")
    def test_prep_new_data(self):
        """If alt_field_info is modifying a value that may also be in Form.data, then call set_alt_data method. """
        pass

    @skip("Not Implemented")
    def test_prep_fields(self):
        """All modifications for Form.fields is done in place, reassignment is not required. """
        pass

    @skip("Not Implemented")
    def test_prep_fields_called_html_output(self):
        """The prep_fields method is called by _html_output because of definition in FormOverrideMixIn. """
        pass


class FormFieldsetTests(FormTests, TestCase):
    form_class = FormFieldsetForm


class ComputedUsernameTests(FormTests, TestCase):
    form_class = ComputedUsernameForm
    user_type = 'user'  # 'superuser' | 'staff' | 'user' | 'anonymous'
    mock_users = False

    def test_temp(self):
        self.assertEqual('username', self.form._meta.model.USERNAME_FIELD)
        self.assertEqual('email', self.form._meta.model.get_email_field_name())
        self.assertEqual('username', self.form.name_for_user)
        self.assertEqual('email', self.form.name_for_email)
        self.assertIn(self.form._meta.model.get_email_field_name(), self.form.fields)
        self.assertNotIn('email_field', self.form.fields)

    @skip("Not Implemented")
    def test_raises_on_not_user_model(self):
        """Raises ImproperlyConfigured if an appropriate User like model cannot be discovered. """
        # get_form_user_model: uses django.contrib.auth.get_user_model
        pass

    def test_raises_on_constructor_fields_error(self):
        """Raises ImproperlyConfigured if constructor_fields property is not a list or tuple of strings. """
        self.form.constructor_fields = None
        message = "Expected a list of field name strings for constructor_fields. "
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            self.form.confirm_required_fields()

    def test_raises_on_missing_needed_fields(self):
        """Raises ImproperlyConfigured if missing any fields from constructor, username, email, and flag_field. """
        test_name = "impossible_creature_not_present"
        self.form.constructor_fields = [*self.form.constructor_fields, test_name]
        message = "The fields for email, username, and constructor must be set in fields. "
        self.assertNotIn(test_name, self.form.base_fields)
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            self.form.confirm_required_fields()

    def validators_effect_required(self, field, func, *args, **kwargs):
        """Gets the effect that running the validator method has on the field's required attribute. """
        NOT_EXIST = '_MISSING_'
        original_required = getattr(field, 'required', NOT_EXIST)
        field.required = False
        func(*args, **kwargs)
        after_false = field.required
        field.required = True
        func(*args, **kwargs)
        after_true = field.required
        result = None
        if after_false and after_true:
            result = True
        elif not after_false and not after_true:
            result = False
        elif after_false and not after_true:
            result = 'Flip'
        field.required = original_required
        if original_required == NOT_EXIST:
            del field.required
        return result

    def validators_applied_count(self, field, func, *args, **kwargs):
        """Returns how many validators are applied to a given field. """
        original_validators = field.validators
        field.validators = []
        func(*args, **kwargs)
        result = len(field.validators)
        field.validators = original_validators
        return result

    def test_username_validators(self):
        """The validators from name_for_user_validators are applied as expected. """
        name = self.form.name_for_user
        field_source = self.form.fields if name in self.form.fields else self.form.base_fields
        field = field_source.get(name, None)
        self.assertIsNotNone(field)
        expected = 2
        count_strict = expected + 1
        original_strict = getattr(self.form, 'strict_username', None)
        self.form.strict_username = False
        func = self.form.name_for_user_validators
        actual = self.validators_applied_count(field, func, field_source)
        required_not_strict = self.validators_effect_required(field, func, field_source)
        self.form.strict_username = True
        actual_strict = self.validators_applied_count(field, func, field_source)
        required_strict = self.validators_effect_required(field, func, field_source)

        self.assertIsNone(required_not_strict)
        self.assertEqual(expected, actual)
        self.assertIsNone(required_strict)
        self.assertEqual(count_strict, actual_strict)

        self.form.strict_username = original_strict
        if original_strict is None:
            del self.form.strict_username

    def test_email_validators(self):
        """The validators from name_for_email_validators are applied as expected. """
        name = self.form.name_for_email
        field = self.form.fields[name]
        expected = 2
        count_strict = expected + 1
        original_strict = getattr(self.form, 'strict_email', None)
        self.form.strict_email = False
        func = self.form.name_for_email_validators
        # email_opts = {'names': (field_name, 'email'), 'alt_field': 'email_field', 'computed': False}
        # email_opts.update({'name': field_name, 'field': field})
        actual = self.validators_applied_count(field, func, self.form.fields)
        required_not_strict = self.validators_effect_required(field, func, self.form.fields)
        self.form.strict_email = True
        actual_strict = self.validators_applied_count(field, func, self.form.fields)
        required_strict = self.validators_effect_required(field, func, self.form.fields)

        self.assertTrue(required_not_strict)
        self.assertEqual(expected, actual)
        self.assertTrue(required_strict)
        self.assertEqual(count_strict, actual_strict)

        self.form.strict_email = original_strict
        if original_strict is None:
            del self.form.strict_email

    def test_constructor_fields_used_when_email_fails(self):
        """If email already used, uses constructor_fields to make a username in username_from_email_or_names. """
        self.form.name_for_user = self.form._meta.model.USERNAME_FIELD
        self.form.name_for_email = self.form._meta.model.get_email_field_name()
        existing_email = self.user.email
        new_info = {'first_name': "Newbie", 'last_name': "Newsome", 'email': existing_email}
        original_data = self.form.data
        test_data = original_data.copy()
        test_data.update(new_info)
        test_data._mutable = False
        self.form.data = test_data
        self.form.is_bound = True
        self.form.cleaned_data = new_info.copy()

        names = (new_info[field_name] for field_name in self.form.constructor_fields)
        expected = '_'.join(names).casefold()
        UserModel = get_user_model()
        cur_user = self.user
        found_user = UserModel.objects.get(username=cur_user.username)

        self.assertEqual(cur_user, found_user)
        for key, value in new_info.items():
            self.assertIn(key, self.form.cleaned_data)
            if key in (self.form.name_for_user, self.form.name_for_email):
                continue
            self.assertNotEqual(getattr(self.user, key, None), value)
        result = self.form.username_from_email_or_names(self.form.name_for_user, self.form.name_for_email)
        self.assertEqual(expected, result)

        self.form.data = original_data
        del self.form.cleaned_data

    def test_email_from_username_from_email_or_names(self):
        """When email is a valid username, username_from_email_or_names method returns email. """
        self.form.name_for_user = self.form._meta.model.USERNAME_FIELD
        self.form.name_for_email = self.form._meta.model.get_email_field_name()

        new_info = OTHER_USER.copy()
        original_data = self.form.data
        test_data = original_data.copy()
        test_data.update(new_info)
        test_data._mutable = False
        self.form.data = test_data
        self.form.is_bound = True
        self.form.cleaned_data = new_info.copy()

        expected = new_info['email']
        UserModel = get_user_model()

        self.assertEqual(1, UserModel.objects.count())
        self.assertEqual(self.user, UserModel.objects.first())
        for key in (self.form.name_for_user, self.form.name_for_email):
            new_info.get(key, None) != getattr(self.user, key, '')
        for key, value in new_info.items():
            self.assertIn(key, self.form.cleaned_data)
        result = self.form.username_from_email_or_names(self.form.name_for_user, self.form.name_for_email)
        self.assertEqual(expected, result)

        self.form.data = original_data
        del self.form.cleaned_data

    def test_interface_compute_name_for_user(self):
        """The compute_name_for_user method, when not overwritten, calls the default username_from_email_or_names. """
        self.form.name_for_user = self.form._meta.model.USERNAME_FIELD
        self.form.name_for_email = self.form._meta.model.get_email_field_name()
        expected = "Unique test response value"

        def confirm_func(username_field_name=None, email_field_name=None): return expected
        original_func = self.form.username_from_email_or_names
        self.form.username_from_email_or_names = confirm_func
        actual = self.form.compute_name_for_user()
        self.form.username_from_email_or_names = original_func

        self.assertEqual(expected, actual)

    def get_or_make_links(self, link_names):
        """If reverse is able to find the link_name, return it. Otherwise return a newly created one. """
        link_names = link_names if isinstance(link_names, (list, tuple)) else [link_names]
        urls = []
        for name in link_names:
            try:
                url = reverse(name)
            except NoReverseMatch as e:
                print(e)
                url = None
                # if name == 'password_reset':
                #     path('test-password/', views.PasswordChangeView.as_view(template_name='update.html'), name=name)
                # else:
                #     pass
            urls.append(url)
        # print(urls)
        return urls

    def mock_get_login_message(self, urls, link_text=None, link_only=False, reset=False):
        if not isinstance(link_text, (tuple, list)):
            link_text = (link_text, link_text)
        link_text = [ea if ea else None for ea in link_text]
        login_link = format_html('<a href="{}">{}</a>', urls[0], link_text[0] or 'login')
        reset_link = format_html('<a href="{}">{}</a>', urls[1], link_text[1] or 'reset the password')
        expected = None
        if link_only:
            expected = reset_link if reset else login_link
        else:
            message = "You can {} to your existing account".format(login_link)
            if reset:
                message += " or {} if needed".format(reset_link)
            message += ". "
            expected = message
        return expected

    def test_message_link_only_no_text(self):
        """The get_login_message response for link_only and no text passed returns as expected. """
        # self.form.get_login_message(link_text=None, link_only=False, reset=False)
        kwargs = dict(link_text=None, link_only=False, reset=False)
        kwargs['link_only'] = True
        # print("============================ TEST MESSAGE LINK METHODS ===============================")
        urls = self.get_or_make_links(('login', 'password_reset'))
        for url in urls:
            self.assertIsNotNone(url)
        expected = self.mock_get_login_message(urls, **kwargs)
        actual = self.form.get_login_message(**kwargs)

        self.assertEqual(expected, actual)

    def test_message_link_only_with_text(self):
        """The get_login_message response for link_only and no text passed returns as expected. """
        kwargs = dict(link_text=None, link_only=False, reset=False)
        kwargs['link_only'] = True
        kwargs['link_text'] = 'This is the text for the test - test_message_link_only_with_text'
        urls = self.get_or_make_links(('login', 'password_reset'))
        for url in urls:
            self.assertIsNotNone(url)
        expected = self.mock_get_login_message(urls, **kwargs)
        actual = self.form.get_login_message(**kwargs)

        self.assertEqual(expected, actual)

    def test_message_reset_link_only_no_text(self):
        """The get_login_message response for link_only and no text passed returns as expected. """
        # self.form.get_login_message(link_text=None, link_only=False, reset=False)
        kwargs = dict(link_text=None, link_only=False, reset=False)
        kwargs['link_only'] = True
        kwargs['reset'] = True
        # print("============================ TEST MESSAGE LINK METHODS ===============================")
        urls = self.get_or_make_links(('login', 'password_reset'))
        for url in urls:
            self.assertIsNotNone(url)
        expected = self.mock_get_login_message(urls, **kwargs)
        actual = self.form.get_login_message(**kwargs)

        self.assertEqual(expected, actual)

    def test_message_reset_link_only_with_text(self):
        """The get_login_message response for link_only and no text passed returns as expected. """
        kwargs = dict(link_text=None, link_only=False, reset=False)
        kwargs['link_only'] = True
        kwargs['reset'] = True
        kwargs['link_text'] = 'This is the text for the test - test_message_link_only_with_text'
        urls = self.get_or_make_links(('login', 'password_reset'))
        for url in urls:
            self.assertIsNotNone(url)
        expected = self.mock_get_login_message(urls, **kwargs)
        actual = self.form.get_login_message(**kwargs)

        self.assertEqual(expected, actual)

    def test_message_default_no_text(self):
        """The get_login_message response for link_only and no text passed returns as expected. """
        kwargs = dict(link_text=None, link_only=False, reset=False)
        urls = self.get_or_make_links(('login', 'password_reset'))
        for url in urls:
            self.assertIsNotNone(url)
        expected = self.mock_get_login_message(urls, **kwargs)
        actual = self.form.get_login_message(**kwargs)

        self.assertEqual(expected, actual)

    def test_message_default_with_text(self):
        """The get_login_message response for link_only and no text passed returns as expected. """
        kwargs = dict(link_text=None, link_only=False, reset=False)
        link_names = ('login', 'password_reset')
        text_template = 'The {} test text - test_message_default_with_text'
        kwargs['link_text'] = [text_template.format(name) for name in link_names]
        urls = self.get_or_make_links(link_names)
        for url in urls:
            self.assertIsNotNone(url)
        expected = self.mock_get_login_message(urls, **kwargs)
        actual = self.form.get_login_message(**kwargs)

        self.assertEqual(expected, actual)

    def test_message_reset_no_text(self):
        """The get_login_message response for link_only and no text passed returns as expected. """
        kwargs = dict(link_text=None, link_only=False, reset=False)
        kwargs['reset'] = True
        urls = self.get_or_make_links(('login', 'password_reset'))
        for url in urls:
            self.assertIsNotNone(url)
        expected = self.mock_get_login_message(urls, **kwargs)
        actual = self.form.get_login_message(**kwargs)

        self.assertEqual(expected, actual)

    def test_message_reset_with_text(self):
        """The get_login_message response for link_only and no text passed returns as expected. """
        kwargs = dict(link_text=None, link_only=False, reset=False)
        kwargs['reset'] = True
        link_names = ('login', 'password_reset')
        text_template = 'The {} test text - test_message_default_with_text'
        kwargs['link_text'] = [text_template.format(name) for name in link_names]
        urls = self.get_or_make_links(link_names)
        for url in urls:
            self.assertIsNotNone(url)
        expected = self.mock_get_login_message(urls, **kwargs)
        actual = self.form.get_login_message(**kwargs)

        self.assertEqual(expected, actual)

    @skip("Not Implemented")
    def test_confirmation_username_not_email(self):
        """If the computed username is not the given email, raise ValidationError to get username confirmation. """
        pass

    @skip("Not Implemented")
    def test_confirmed_username(self):
        """If user has already confirmed an atypical username, it is used without further confirmation checks. """
        pass

    @skip("Not Implemented")
    def test_handle_flag_error(self):
        """The Form's clean method raises ValidationError if error found in handle_flag_field method. """
        pass

    @skip("Not Implemented")
    def test_fields_updated_with_computed(self):
        """The computed_fields are added to fields if there is no error in username or other computed fields. """
        pass

    @skip("Not Implemented")
    def test_cleaned_data_worked(self):
        """The Form's clean method returns the expected cleaned_data, after cleaning all fields. """
        pass


class ConfirmationComputedUsernameTests(FormTests, TestCase):
    form_class = ComputedUsernameForm
    user_type = 'user'  # 'superuser' | 'staff' | 'user' | 'anonymous'
    mock_users = False
    form_test_data = OTHER_USER

    def setUp(self):
        self.user = self.make_user()
        self.form = self.make_form_request()
        email_name = getattr(self.form, 'name_for_email', None) or 'email'
        test_data = MultiValueDict()
        test_data.update(self.form_test_data)
        test_data.update({email_name: getattr(self.user, email_name)})
        self.test_data = test_data
        self.form = self.make_form_request(method='POST', data=test_data)

    def test_init(self):
        meta = getattr(self.form, '_meta', None)
        self.assertIsNotNone(meta)
        user_model = getattr(meta, 'model', None)
        self.assertIsNotNone(user_model)
        self.assertEqual(user_model, self.form.user_model)
        expected_name = meta.model.USERNAME_FIELD
        expected_email = meta.model.get_email_field_name()
        expected_flag = self.form.USERNAME_FLAG_FIELD
        self.assertEqual(expected_name, self.form.name_for_user)
        self.assertEqual(expected_email, self.form.name_for_email)
        self.assertIsNotNone(expected_flag)
        self.assertIn(expected_email, self.form.fields)
        self.assertIn(expected_name, self.form.base_fields)
        self.assertNotIn(expected_name, self.form.fields)
        self.assertIn(expected_email, self.test_data)
        self.assertIn(expected_flag, self.form.base_fields)

    def test_as_table(self): pass
    def test_as_ul(self): pass
    def test_as_p(self): pass

    def test_raise_missing_flag_field(self):
        """Raises ImproperlyConfigured if flag field cannot be found for configure_username_confirmation. """
        original_data = self.form.data
        original_fields = self.form.fields
        original_flag = self.form.USERNAME_FLAG_FIELD
        original_cleaned_data = getattr(self.form, 'cleaned_data', None)
        original_errors = getattr(self.form, '_errors', None)
        self.form.data = original_data.copy()
        self.form.fields = original_fields.copy()
        self.form.USERNAME_FLAG_FIELD = 'Not a valid field name'
        self.form.cleaned_data = {self.form.name_for_user: 'test_username', self.form.name_for_email: 'test_email'}
        # self.form._errors = ErrorDict() if original_errors is None else original_errors.copy()
        self.form._errors = None if original_errors is None else original_errors.copy()

        with self.assertRaises(ImproperlyConfigured):
            self.form.configure_username_confirmation()

        self.form.data = original_data
        self.form.fields = original_fields
        self.form.USERNAME_FLAG_FIELD = original_flag
        self.form.cleaned_data = original_cleaned_data
        self.form._errors = original_errors
        if original_cleaned_data is None:
            del self.form.cleaned_data
        if original_errors is None:
            del self.form._errors

    def test_focus_update_for_configure_username_confirmation(self):
        """If the assign_focus_field method is present, then we expect email field to get the focus. """
        original_data = self.form.data
        original_fields = self.form.fields
        original_computed_fields = self.form.computed_fields
        original_cleaned_data = getattr(self.form, 'cleaned_data', None)
        original_errors = getattr(self.form, '_errors', None)
        original_focus = getattr(self.form, 'named_focus', None)
        original_focus_method = getattr(self.form, 'assign_focus_field', None)
        self.form.data = original_data.copy()
        self.form.fields = original_fields.copy()
        self.form.computed_fields = original_computed_fields.copy()
        self.form.cleaned_data = {self.form.name_for_user: 'test_username', self.form.name_for_email: 'test_email'}
        self.form._errors = ErrorDict() if original_errors is None else original_errors.copy()
        self.form.named_focus = ''
        if original_focus_method is None:
            def mock_focus_method(name, *args, **kwargs): return name
            setattr(self.form, 'assign_focus_field', mock_focus_method)
        message = self.form.configure_username_confirmation()
        message = None if not message else message
        expected = self.form.name_for_email
        actual = getattr(self.form, 'named_focus', None)

        self.assertIsNotNone(message)
        self.assertTrue(hasattr(self.form, 'assign_focus_field'))
        self.assertEqual(expected, self.form.assign_focus_field(expected))
        self.assertEqual(expected, actual)

        self.form.data = original_data
        self.form.fields = original_fields
        self.form.computed_fields = original_computed_fields
        self.form.named_focus = original_focus
        self.form.assign_focus_field = original_focus_method
        self.form.cleaned_data = original_cleaned_data
        self.form._errors = original_errors
        if original_focus is None:
            del self.form.named_focus
        if original_focus_method is None:
            del self.form.assign_focus_field
        if original_cleaned_data is None:
            del self.form.cleaned_data
        if original_errors is None:
            del self.form._errors

    def test_configure_username_confirmation(self):
        """The configure_username_confirmation method modifies the data, & fields, and returns expected message. """
        original_data = self.form.data
        original_fields = self.form.fields
        original_computed_fields = self.form.computed_fields
        self.form.data = original_data.copy()
        self.form.fields = original_fields.copy()
        self.form.computed_fields = original_computed_fields.copy()
        # valid = self.form.is_valid()
        self.form.full_clean()
        names = (original_data.get(field_name, None) for field_name in self.form.constructor_fields)
        expected_name = '_'.join(name for name in names if name is not None).casefold()
        normalize = self.form.user_model.normalize_username
        if callable(normalize):
            expected_name = normalize(expected_name)
        expected_flag = 'False'

        self.assertNotIn(self.form.name_for_user, original_data)
        self.assertNotIn(self.form.name_for_user, original_fields)
        self.assertIn(self.form.name_for_user, self.form.data)
        self.assertIn(self.form.name_for_user, self.form.fields)
        self.assertNotIn(self.form.USERNAME_FLAG_FIELD, original_data)
        self.assertNotIn(self.form.USERNAME_FLAG_FIELD, original_fields)
        self.assertIn(self.form.USERNAME_FLAG_FIELD, self.form.data)
        self.assertIn(self.form.USERNAME_FLAG_FIELD, self.form.fields)
        self.assertEqual(expected_name, self.form.data.get(self.form.name_for_user, None))
        self.assertEqual(expected_flag, self.form.data.get(self.form.USERNAME_FLAG_FIELD, None))

        self.form.data = original_data
        self.form.fields = original_fields
        self.form.computed_fields = original_computed_fields

    def test_message_configure_username_confirmation(self):
        """The configure_username_confirmation method adds  'email' and 'username' errors and returns a message. """
        original_data = self.form.data
        original_fields = self.form.fields
        original_computed_fields = self.form.computed_fields
        original_errors = getattr(self.form, '_errors', None)
        original_cleaned_data = getattr(self.form, 'cleaned_data', None)
        original_clean = self.form.clean
        self.form.data = original_data.copy()
        self.form.fields = original_fields.copy()
        self.form.computed_fields = original_computed_fields.copy()
        self.form._errors = ErrorDict() if original_errors is None else original_errors.copy()
        self.form.cleaned_data = {self.form.name_for_user: 'test_username', self.form.name_for_email: 'test_email'}
        def replace_clean(): raise ImproperlyConfigured("Unexpected Clean Method Called. ")
        self.form.clean = replace_clean

        login_link = self.form.get_login_message(link_text='login to existing account', link_only=True)
        expected_email_error = "Use a non-shared email, or {}. ".format(login_link)
        e_note = "Typically people have their own unique email address, which you can update. "
        e_note += "If you share an email with another user, then you will need to create a username for your login. "
        expected_user_error = e_note
        title = "Login with existing account, change to a non-shared email, or create a username. "
        message = "Did you already make an account, or have one because you've had classes with us before? "
        expected_message = format_html(
            "<h3>{}</h3> <p>{} <br />{}</p>",
            title,
            message,
            self.form.get_login_message(reset=True),
            )
        # print("=============== test_configure_username_confirmation ===================")
        actual_message = self.form.configure_username_confirmation()
        actual_email_error = ''.join(self.form._errors.get(self.form.name_for_email))
        actual_user_error = ''.join(self.form._errors.get(self.form.name_for_user))
        # print("-----------------------------------------------------------")
        # pprint(self.form)
        # print("-----------------------------------------------------------")
        # pprint(expected_message)
        # print("*********************************")
        # pprint(actual_message)
        # print("-----------------------------------------------------------")
        # pprint(expected_email_error)
        # print("*********************************")
        # pprint(actual_email_error)
        # print("-----------------------------------------------------------")
        # pprint(expected_user_error)
        # print("*********************************")
        # pprint(actual_user_error)
        # print("-----------------------------------------------------------")

        self.assertEqual(expected_message, actual_message)
        self.assertEqual(expected_email_error, actual_email_error)
        self.assertEqual(expected_user_error, actual_user_error)

        self.form.data = original_data
        self.form.fields = original_fields
        self.form.computed_fields = original_computed_fields
        self.form._errors = original_errors
        self.form.clean = original_clean
        self.form.cleaned_data = original_cleaned_data
        if original_errors is None:
            del self.form._errors
        if original_cleaned_data is None:
            del self.form.cleaned_data

    def test_clean_calls_handle_flag_field(self):
        """If not compute errors, clean method raises ValidationError for non-empty return from handle_flag_field. """
        original_data = self.form.data
        original_fields = self.form.fields
        original_computed_fields = self.form.computed_fields
        original_errors = getattr(self.form, '_errors', None)
        original_cleaned_data = getattr(self.form, 'cleaned_data', None)
        self.form.data = original_data.copy()
        self.form.fields = original_fields.copy()
        self.form.computed_fields = original_computed_fields.copy()
        self.form._errors = ErrorDict() if original_errors is None else original_errors.copy()
        new_cleaned_data = {self.form.name_for_user: 'test_value', self.form.name_for_email: 'test_value'}
        self.form.cleaned_data = new_cleaned_data.copy()
        # expected_error = {self.form.name_for_email: "test email error", self.form.name_for_user: "test user error"}
        expected_error = "The replace_handle_flag_field test return value. "
        def replace_handle_flag_field(email, user): return expected_error
        self.form.handle_flag_field = replace_handle_flag_field
        with self.assertRaisesMessage(ValidationError, expected_error):
            self.form.clean()

        self.form.data = original_data
        self.form.fields = original_fields
        self.form.computed_fields = original_computed_fields
        self.form._errors = original_errors
        self.form.cleaned_data = original_cleaned_data
        if original_errors is None:
            del self.form._errors
        if original_cleaned_data is None:
            del self.form.cleaned_data

    def test_clean_returns_cleaned_data(self):
        """If not compute errors, handle_flag_errors, or other errors, clean returns cleaned_data & updates fields. """
        original_data = self.form.data
        original_fields = self.form.fields
        original_computed_fields = self.form.computed_fields
        original_errors = getattr(self.form, '_errors', None)
        original_cleaned_data = getattr(self.form, 'cleaned_data', None)
        self.form.data = original_data.copy()
        self.form.fields = original_fields.copy()
        self.form.computed_fields = original_computed_fields.copy()
        self.form._errors = ErrorDict() if original_errors is None else original_errors.copy()
        new_cleaned_data = {self.form.name_for_user: 'test_value', self.form.name_for_email: 'test_value'}
        new_cleaned_data[self.form.USERNAME_FLAG_FIELD] = False
        self.form.cleaned_data = new_cleaned_data.copy()
        expected_fields = {**original_fields, **original_computed_fields}

        cleaned_data = self.form.clean()
        self.assertDictEqual(new_cleaned_data, cleaned_data)
        self.assertDictEqual(expected_fields, self.form.fields)

        self.form.data = original_data
        self.form.fields = original_fields
        self.form.computed_fields = original_computed_fields
        self.form._errors = original_errors
        self.form.cleaned_data = original_cleaned_data
        if original_errors is None:
            del self.form._errors
        if original_cleaned_data is None:
            del self.form.cleaned_data

    def test_no_flag_handle_flag_field(self):
        """If there is no flag field, expected return of None. """
        original_flag_name = self.form.USERNAME_FLAG_FIELD
        self.form.USERNAME_FLAG_FIELD = "This is not a valid field name"
        expected = None
        actual = self.form.handle_flag_field(self.form.name_for_email, self.form.name_for_user)

        self.assertEqual(expected, actual)
        self.form.USERNAME_FLAG_FIELD = original_flag_name

    def test_no_error_handle_flag_field(self):
        """If there is no error found during handle_flag_field, expected return of an empty Dict. """
        original_data = self.form.data
        original_fields = self.form.fields
        original_computed_fields = self.form.computed_fields
        original_errors = getattr(self.form, '_errors', None)
        original_cleaned_data = getattr(self.form, 'cleaned_data', None)
        self.form.data = original_data.copy()
        self.form.fields = original_fields.copy()
        self.form.computed_fields = original_computed_fields.copy()
        self.form._errors = ErrorDict() if original_errors is None else original_errors.copy()
        new_cleaned_data = {self.form.name_for_user: 'test_value', self.form.name_for_email: 'test_value'}
        new_cleaned_data[self.form.USERNAME_FLAG_FIELD] = True  # False
        user_field = self.form.computed_fields.pop(self.form.name_for_user, None)
        self.form.fields.update({self.form.name_for_user: user_field})
        email_field = self.form.fields[self.form.name_for_email]
        email_field.initial = new_cleaned_data[self.form.name_for_email]
        self.form.cleaned_data = new_cleaned_data.copy()
        expected = {}
        actual = self.form.handle_flag_field(self.form.name_for_email, self.form.name_for_user)

        self.assertIsNotNone(user_field)
        self.assertFalse(email_field.has_changed(email_field.initial, self.form.cleaned_data[self.form.name_for_email]))
        self.assertEqual(expected, actual)

        self.form.data = original_data
        self.form.fields = original_fields
        self.form.computed_fields = original_computed_fields
        self.form._errors = original_errors
        self.form.cleaned_data = original_cleaned_data
        if original_errors is None:
            del self.form._errors
        if original_cleaned_data is None:
            del self.form.cleaned_data

    def test_username_of_email_exists_handle_flag_field(self):
        """If current email matches an existing username, handle_flag_field returns a Dict with that error. """
        original_data = self.form.data
        original_fields = self.form.fields
        original_computed_fields = self.form.computed_fields
        original_errors = getattr(self.form, '_errors', None)
        original_cleaned_data = getattr(self.form, 'cleaned_data', None)
        self.form.data = original_data.copy()
        self.form.fields = original_fields.copy()
        self.form.computed_fields = original_computed_fields.copy()
        self.form._errors = ErrorDict() if original_errors is None else original_errors.copy()
        email_val = getattr(self.user, self.form.name_for_user, None)
        new_cleaned_data = {self.form.name_for_user: email_val, self.form.name_for_email: email_val}
        new_cleaned_data[self.form.USERNAME_FLAG_FIELD] = False
        user_field = self.form.computed_fields.pop(self.form.name_for_user, None)
        self.form.fields.update({self.form.name_for_user: user_field})
        self.form.cleaned_data = new_cleaned_data.copy()
        expected_message = "You must give a unique email not shared with other users (or create a username). "
        expected = {self.form.name_for_email: expected_message}
        actual = self.form.handle_flag_field(self.form.name_for_email, self.form.name_for_user)

        self.assertIsNotNone(email_val)
        self.assertIsNotNone(user_field)
        self.assertEqual(email_val, self.form.data.get(self.form.name_for_email, None))
        self.assertEqual(expected, actual)

        self.form.data = original_data
        self.form.fields = original_fields
        self.form.computed_fields = original_computed_fields
        self.form._errors = original_errors
        self.form.cleaned_data = original_cleaned_data
        if original_errors is None:
            del self.form._errors
        if original_cleaned_data is None:
            del self.form.cleaned_data

    def test_email_works_as_username_handle_flag_field(self):
        """If current email is a valid username, set username value in cleaned_data. No error returned. """
        original_data = self.form.data
        original_fields = self.form.fields
        original_computed_fields = self.form.computed_fields
        original_errors = getattr(self.form, '_errors', None)
        original_cleaned_data = getattr(self.form, 'cleaned_data', None)
        self.form.data = original_data.copy()
        self.form.fields = original_fields.copy()
        self.form.computed_fields = original_computed_fields.copy()
        self.form._errors = ErrorDict() if original_errors is None else original_errors.copy()
        email_val = self.form_test_data.get(self.form.name_for_email)  # was overwritten for form request.
        new_cleaned_data = {self.form.name_for_user: 'test_value', self.form.name_for_email: email_val}
        new_cleaned_data[self.form.USERNAME_FLAG_FIELD] = False
        user_field = self.form.computed_fields.pop(self.form.name_for_user, None)
        self.form.fields.update({self.form.name_for_user: user_field})
        email_field = self.form.fields[self.form.name_for_email]
        email_field.initial = getattr(self.user, self.form.name_for_user)
        self.form.cleaned_data = new_cleaned_data.copy()
        expected = {}
        actual = self.form.handle_flag_field(self.form.name_for_email, self.form.name_for_user)
        actual_username = self.form.cleaned_data.get(self.form.name_for_user, None)

        self.assertIsNotNone(email_val)
        self.assertIsNotNone(user_field)
        self.assertTrue(email_field.has_changed(email_field.initial, self.form.cleaned_data[self.form.name_for_email]))
        self.assertNotEqual(getattr(self.user, self.form.name_for_user), email_val)
        self.assertNotEqual(new_cleaned_data[self.form.name_for_user], actual_username)
        self.assertEqual(email_val, actual_username)
        self.assertEqual(expected, actual)

        self.form.data = original_data
        self.form.fields = original_fields
        self.form.computed_fields = original_computed_fields
        self.form._errors = original_errors
        self.form.cleaned_data = original_cleaned_data
        if original_errors is None:
            del self.form._errors
        if original_cleaned_data is None:
            del self.form.cleaned_data

    def test_bad_flag_handle_flag_field(self):
        """If they should have unchecked the flag field, return a Dict with that error. """
        original_data = self.form.data
        original_fields = self.form.fields
        original_computed_fields = self.form.computed_fields
        original_errors = getattr(self.form, '_errors', None)
        original_cleaned_data = getattr(self.form, 'cleaned_data', None)
        self.form.data = original_data.copy()
        self.form.fields = original_fields.copy()
        self.form.computed_fields = original_computed_fields.copy()
        self.form._errors = ErrorDict() if original_errors is None else original_errors.copy()
        email_val = self.form_test_data.get(self.form.name_for_email)  # was overwritten for form request.
        new_cleaned_data = {self.form.name_for_user: 'test_value', self.form.name_for_email: email_val}
        new_cleaned_data[self.form.USERNAME_FLAG_FIELD] = True
        user_field = self.form.computed_fields.pop(self.form.name_for_user, None)
        self.form.fields.update({self.form.name_for_user: user_field})
        email_field = self.form.fields[self.form.name_for_email]
        email_field.initial = getattr(self.user, self.form.name_for_user)
        self.form.cleaned_data = new_cleaned_data.copy()
        message = "Un-check the box, or leave empty, if you want to use this email address. "
        expected = {self.form.USERNAME_FLAG_FIELD: message}
        actual = self.form.handle_flag_field(self.form.name_for_email, self.form.name_for_user)
        actual_username = self.form.cleaned_data.get(self.form.name_for_user, None)

        self.assertIsNotNone(email_val)
        self.assertIsNotNone(user_field)
        self.assertTrue(email_field.has_changed(email_field.initial, self.form.cleaned_data[self.form.name_for_email]))
        self.assertNotEqual(getattr(self.user, self.form.name_for_user), email_val)
        self.assertEqual(new_cleaned_data[self.form.name_for_user], actual_username)
        self.assertNotEqual(email_val, actual_username)
        self.assertEqual(expected, actual)

        self.form.data = original_data
        self.form.fields = original_fields
        self.form.computed_fields = original_computed_fields
        self.form._errors = original_errors
        self.form.cleaned_data = original_cleaned_data
        if original_errors is None:
            del self.form._errors
        if original_cleaned_data is None:
            del self.form.cleaned_data


class CountryTests(FormTests, TestCase):
    form_class = CountryForm

    def empty_good_practice_attrs(self): return {}
    def empty_get_overrides(self): return {}  # return self.form.good_practice_attrs()
    def empty_get_alt_field_info(self): return {}

    def setUp(self):
        # self.user = self.make_user()
        # self.form = self.make_form_request()
        super().setUp()
        self.original_good_practice_attrs = self.form.good_practice_attrs
        self.original_get_overrides = self.form.get_overrides
        self.original_get_alt_field_info = self.form.get_alt_field_info
        self.form.good_practice_attrs = self.empty_good_practice_attrs
        self.form.get_overrides = self.empty_get_overrides
        self.form.get_alt_field_info = self.empty_get_alt_field_info
        # fd = self.form.fields
        # test_initial = {'first': fd['first'].initial, 'second': fd['second'].initial, 'last': fd['last'].initial}
        # test_initial['generic_field'] = fd['generic_field'].initial
        # test_data = MultiValueDict()
        # test_data.update({name: f"test_value_{name}" for name in test_initial})
        # self.test_initial = test_initial
        # self.test_data = test_data

    def test_setup(self):
        """Are the overriden methods the new empty versions? """
        self.assertIsNotNone(getattr(self, 'original_good_practice_attrs', None))
        self.assertIsNotNone(getattr(self, 'original_get_overrides', None))
        self.assertIsNotNone(getattr(self, 'original_get_alt_field_info', None))
        print("================ TEST SETUP ======================")
        print(self.form.good_practice_attrs())
        print(self.form.get_overrides())
        print(self.form.get_alt_field_info())
        print(self.form.good_practice_attrs.__name__)
        print(self.form.get_overrides.__name__)
        print(self.form.get_alt_field_info.__name__)
        self.assertEqual({}, self.form.good_practice_attrs())
        self.assertEqual({}, self.form.get_overrides())
        self.assertEqual({}, self.form.get_alt_field_info())

    @skip("Hold for testing. ")
    def test_as_table(self):
        super().test_as_table()

    @skip("Hold for testing. ")
    def test_as_ul(self):
        super().test_as_ul()
