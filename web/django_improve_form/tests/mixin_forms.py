from django.test import TestCase  # , Client, override_settings, modify_settings, TransactionTestCase, RequestFactory
# from django.core.exceptions import ImproperlyConfigured  # , ValidationError
# from django.utils.translation import gettext_lazy as _
# from django.contrib.auth import get_user_model
# from .helper_general import AnonymousUser, MockUser  # MockRequest, UserModel, MockStaffUser, MockSuperUser, APP_NAME
# from django.conf import settings
from django.forms import Form  # , ModelForm, BaseModelForm, ModelFormMetaclass
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
    pass


class CriticalForm(CriticalFieldMixIn, Form):
    pass


class ComputedForm(ComputedFieldsMixIn, Form):
    pass


class OverrideForm(FormOverrideMixIn, Form):
    pass


class FormFieldsetForm(FormFieldsetMixIn, Form):
    pass


# # Extended MixIns # #


class ComputedUsernameForm(ComputedFieldsMixIn, UserCreationForm):
    pass


class CountryForm(OverrideCountryMixIn, Form):
    pass


# # MixIn Interactions # #


class OverrideFieldsetForm(FieldsetOverrideMixIn, Form):
    """There is an interaction of Override handle_modifiers and Focus assign_focus_field with FormFieldset features. """
    pass


class UsernameFocusForm(FocusMixIn, ComputedUsernameMixIn, Form):
    """There is an interaction of Focus named_focus in ComputedUsernameMixIn.configure_username_confirmation. """
    pass


class ComputedCountryForm(OverrideCountryMixIn, ComputedFieldsMixIn):
    """The Computed get_critical_field method & computed_fields property are used in OverrideCountryMixIn.__init__. """
    pass


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
