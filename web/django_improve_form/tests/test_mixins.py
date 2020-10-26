from django.test import TestCase  # , Client, override_settings, modify_settings, TransactionTestCase, RequestFactory
from unittest import skip
# from django.core.exceptions import ImproperlyConfigured  # , ValidationError
# from django.utils.translation import gettext_lazy as _
# from django.contrib.auth import get_user_model
# from .helper_views import MimicAsView, USER_DEFAULTS
from .helper_general import MockRequest, AnonymousUser, MockUser, MockStaffUser, MockSuperUser  # UserModel, APP_NAME
# from django.conf import settings
# from django.core.exceptions import ObjectDoesNotExist
# from datetime import date, time, timedelta, datetime as dt
# from pprint import pprint
from .mixin_forms import FocusForm, CriticalForm, ComputedForm, OverrideForm, FormFieldsetForm  # # Base MixIns # #
from .mixin_forms import ComputedUsernameForm, CountryForm  # # Extended MixIns # #
# from .mixin_forms import OverrideFieldsetForm, UsernameFocusForm, ComputedCountryForm  # # MixIn Interactions # #

USER_DEFAULTS = {'email': 'user_fake@fake.com', 'password': 'test1234', 'first_name': 'f_user', 'last_name': 'fake_y'}


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
        from .helper_general import UserModel

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
        output = self.form.as_table().split('\n')  # Fortunately it is convention to have a line for each row.
        print(output)
        # regex_match = ''  # '^<tr' ... '</tr>'
        # all_rows = all()  # every line break starts and ends with the HTML tr tags.
        self.assertNotEqual([], output)

    def test_as_ul(self):
        """All forms should return HTML <li>s when .as_ul is called. """
        output = self.form.as_table().split('\n')  # Fortunately it is convention to have a line for each row.
        print(output)
        # regex_match = ''  # '^<li' ... '</li'
        # all_rows = all()  # every line break starts and ends with the HTML li tags.
        self.assertNotEqual([], output)

    def test_as_p(self):
        """All forms should return HTML <p>s when .as_p is called. """
        output = self.form.as_table().split('\n')  # Fortunately it is convention to have a line for each row.
        print(output)
        # regex_match = ''  # '^<p' ... '</p'
        # all_rows = all()  # every line break starts and ends with the HTML p tags.
        self.assertNotEqual([], output)

    @skip("Not Implemented")
    def test_html_output(self):
        """All forms should have a working _html_output method. ? Should it conform to the same API? """
        pass

    def find_focus_field(self, match=None):
        """Returns a list of all fields that have been given an HTML attribute of 'autofocus'. """
        output_fields = self.get_current_fields()
        found = []
        for field_name, field in output_fields.items():
            has_focus = field.widget.attrs.get('autofocus', None)
            if has_focus:
                found.push(field_name)
        # if not match or len(found) > 1:
        #     return found
        # elif len(found) == 1:
        #     return match == found[0]
        # else:
        #     return None
        return found

    def get_current_fields(self):
        """The form currently outputs these fields. """
        pass


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
