from django.test import TestCase  # , Client, override_settings, modify_settings, TransactionTestCase, RequestFactory
# from unittest import skip
# from django.core.exceptions import ImproperlyConfigured  # , ValidationError
# from django.utils.translation import gettext_lazy as _
# from django.contrib.auth import get_user_model
# from .helper_views import MimicAsView, USER_DEFAULTS
# from .helper_general import AnonymousUser, MockUser  # MockRequest, UserModel, MockStaffUser, MockSuperUser, APP_NAME
# from django.conf import settings
# from django.core.exceptions import ObjectDoesNotExist
# from datetime import date, time, timedelta, datetime as dt
# from pprint import pprint
from .mixin_forms import FocusForm, CriticalForm, ComputedForm, OverrideForm, FormFieldsetForm  # # Base MixIns # #
from .mixin_forms import ComputedUsernameForm, CountryForm  # # Extended MixIns # #
# from .mixin_forms import OverrideFieldsetForm, UsernameFocusForm, ComputedCountryForm  # # MixIn Interactions # #


class FormTests:
    form_class = None

    def setUp(self):
        self.form = self.form_class()


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
