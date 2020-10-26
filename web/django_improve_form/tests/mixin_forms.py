from django.test import TestCase  # , Client, override_settings, modify_settings, TransactionTestCase, RequestFactory
# from django.core.exceptions import ImproperlyConfigured  # , ValidationError
# from django.utils.translation import gettext_lazy as _
# from django.contrib.auth import get_user_model
# from .helper_general import AnonymousUser, MockUser  # MockRequest, UserModel, MockStaffUser, MockSuperUser, APP_NAME
# from django.conf import settings
from django.forms import CharField, Form  # , ModelForm, BaseModelForm, ModelFormMetaclass
from django.contrib.auth.forms import UserCreationForm  # , UserChangeForm
from ..mixins import (
    FocusMixIn, CriticalFieldMixIn, ComputedFieldsMixIn, FormOverrideMixIn, FormFieldsetMixIn,
    ComputedUsernameMixIn, OverrideCountryMixIn,
    FieldsetOverrideMixIn,  # FieldsetOverrideComputedMixIn, FieldsetOverrideUsernameMixIn,
    # AddressMixIn, AddressUsernameMixIn,
    )
from .helper_views import BaseRegisterTests  # , USER_DEFAULTS, MimicAsView,
from ..views import RegisterSimpleFlowView, RegisterActivateFlowView, ModifyUser
from ..views import RegisterModelSimpleFlowView, RegisterModelActivateFlowView
# from datetime import date, time, timedelta, datetime as dt
# from pprint import pprint

# # Base MixIns # #


class FocusForm(FocusMixIn, Form):
    generic_field = CharField()


class CriticalForm(CriticalFieldMixIn, Form):
    generic_field = CharField()


class ComputedForm(ComputedFieldsMixIn, Form):
    generic_field = CharField()


class OverrideForm(FormOverrideMixIn, Form):
    generic_field = CharField()


class FormFieldsetForm(FormFieldsetMixIn, Form):
    generic_field = CharField()


# # Extended MixIns # #


class ComputedUsernameForm(ComputedFieldsMixIn, UserCreationForm):
    generic_field = CharField()


class CountryForm(OverrideCountryMixIn, Form):
    generic_field = CharField()


# # MixIn Interactions # #


class OverrideFieldsetForm(FieldsetOverrideMixIn, Form):
    """There is an interaction of Override handle_modifiers and Focus assign_focus_field with FormFieldset features. """
    generic_field = CharField()


class UsernameFocusForm(FocusMixIn, ComputedUsernameMixIn, Form):
    """There is an interaction of Focus named_focus in ComputedUsernameMixIn.configure_username_confirmation. """
    generic_field = CharField()


class ComputedCountryForm(OverrideCountryMixIn, ComputedFieldsMixIn):
    """The Computed get_critical_field method & computed_fields property are used in OverrideCountryMixIn.__init__. """
    generic_field = CharField()


class ModelSimpleFlowTests(BaseRegisterTests, TestCase):
    # url_name = None
    expected_form = None
    viewClass = RegisterModelSimpleFlowView(form_class=expected_form)
    user_type = 'anonymous'  # 'superuser' | 'admin' | 'user' | 'inactive' | 'anonymous'


class ModelActivateFlowTests(BaseRegisterTests, TestCase):
    # url_name = None
    expected_form = None
    viewClass = RegisterModelActivateFlowView(form_class=expected_form)
    user_type = 'anonymous'  # 'superuser' | 'admin' | 'user' | 'inactive' | 'anonymous'


class SimpleFlowTests(BaseRegisterTests, TestCase):
    # url_name = None
    expected_form = None
    viewClass = RegisterSimpleFlowView(form_class=expected_form)
    user_type = 'anonymous'  # 'superuser' | 'admin' | 'user' | 'inactive' | 'anonymous'


class ModifyUserTests(BaseRegisterTests, TestCase):
    # url_name = None
    expected_form = None
    viewClass = ModifyUser(form_class=expected_form)
    user_type = 'user'  # 'superuser' | 'admin' | 'user' | 'inactive' | 'anonymous'

    def test_get_object(self):
        expected = self.view.request.user
        actual = self.view.get_object()
        self.assertAlmostEqual(expected, actual)

    def test_register(self):
        """ModifyUser is expected to NOT have a register method. """
        self.assertFalse(hasattr(self.view, 'register'))
        self.assertFalse(hasattr(self.viewClass, 'register'))


class ActivateFlowTests(BaseRegisterTests, TestCase):
    # url_name = None
    expected_form = None
    viewClass = RegisterActivateFlowView(form_class=expected_form)
    user_type = 'anonymous'  # 'superuser' | 'admin' | 'user' | 'inactive' | 'anonymous'
