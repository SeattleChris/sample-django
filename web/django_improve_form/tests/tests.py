from django.test import TestCase  # , TransactionTestCase, Client, RequestFactory,
from unittest import skip
from django.core.exceptions import ImproperlyConfigured  # , ValidationError, NON_FIELD_ERRORS  # , ObjectDoesNotExist
# from django.contrib.auth import get_user_model
from .helper_admin import AdminSetupTests  # , AdminModelManagement
from .helper_views import BaseRegisterTests  # , USER_DEFAULTS, MimicAsView,
from ..views import RegisterSimpleFlowView, RegisterActivateFlowView, ModifyUser
from ..views import RegisterModelSimpleFlowView, RegisterModelActivateFlowView
from ..forms import RegisterUserForm, RegisterChangeForm, RegisterModelForm
from ..forms import _assign_available_names, make_names, default_names
# from django.conf import settings
# from django.core.exceptions import ObjectDoesNotExist
# from django.db.models import Q, Max, Subquery
# from django.urls import reverse
# from datetime import date, time, timedelta, datetime as dt


class AdminGeneralModelsTests(AdminSetupTests, TestCase):
    pass


class ModelSimpleFlowTests(BaseRegisterTests, TestCase):
    url_name = 'model_signup'
    viewClass = RegisterModelSimpleFlowView
    expected_form = RegisterModelForm
    user_type = 'anonymous'  # 'superuser' | 'admin' | 'user' | 'inactive' | 'anonymous'


class ModelActivateFlowTests(BaseRegisterTests, TestCase):
    url_name = 'model_initial'
    viewClass = RegisterModelActivateFlowView
    expected_form = RegisterModelForm
    user_type = 'anonymous'  # 'superuser' | 'admin' | 'user' | 'inactive' | 'anonymous'


class SimpleFlowTests(BaseRegisterTests, TestCase):
    url_name = 'django_registration_register'
    viewClass = RegisterSimpleFlowView
    expected_form = RegisterUserForm
    user_type = 'anonymous'  # 'superuser' | 'admin' | 'user' | 'inactive' | 'anonymous'


class ModifyUserTests(BaseRegisterTests, TestCase):
    url_name = 'user_update'
    viewClass = ModifyUser
    expected_form = RegisterChangeForm
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
    url_name = 'initial_signup'
    viewClass = RegisterActivateFlowView
    expected_form = RegisterUserForm
    user_type = 'anonymous'  # 'superuser' | 'admin' | 'user' | 'inactive' | 'anonymous'


DEFAULT_MODEL_NAMES = [
    'extra_one', 'construct_one', 'email_field', 'custom_username', 'early_one', 'construct_two',
    'extra_two', 'construct_three', 'username_field', 'early_two', 'generic_field', 'extra_three',
    ]


class ProfileModel:

    def __init__(self, ignore=(), extra=()):
        c_, names = default_names()
        names = [name for name in names if name not in ignore]
        names = [*names, *extra]
        for name in names:
            setattr(self, name, self.__class__.__name__.lower()[:-5] + '_' + name)
        self.prop = names


class FailModel:
    ignore = {'email_field', 'username_field'}

    def __init__(self, ignore=None, extra=()):
        ignore = self.ignore if ignore is None else ignore
        names = [name for name in DEFAULT_MODEL_NAMES if name not in ignore]
        names = [*names, *extra]
        for name in names:
            setattr(self, name, self.__class__.__name__.lower()[:-5] + '_' + name)
        self.prop = names


class MockModel(FailModel):
    ignore = {'custom_username', }
    USERNAME_FIELD = 'username_field'

    def get_email_field_name(self):
        return 'email_field'


class MakeNamesModelTests(TestCase):

    model_class = FailModel
    user_model_class = MockModel
    model = model_class()
    user_model = user_model_class()
    constructor_names = ['construct_one', 'construct_two', 'construct_three']  # Model field names, or None for defaults
    # early_names = []
    early_names = ['early_one', 'early_two']  # User model fields the form should have BEFORE email, username, password.
    username_flag_name = 'custom_username'  # Set to None if the User model does not have this field type.
    extra_names = ['extra_one', 'extra_two', 'extra_three']  # User model fields the has AFTER email, username, password
    address_names = None  # Assumes defaults or the provided list of model fields. Set to [] for no address.
    address_on_profile_name = None  # ProfileModel  # Set to the model used as profile if it stores the address fields.
    # fields, user_fields, missing = make_names(constructor_names, early_names, username_flag_name, extra_names,
    #                                           address_names, model, user_model, address_on_profile_name)
    # make_names_args = (constructor_names, early_names, username_flag_name, extra_names,
    #                    address_names, model, user_model, address_on_profile_name)

    def get_name_args(self):
        arg_names = ('constructor_names', 'early_names', 'username_flag_name', 'extra_names',
                     'address_names', 'model', 'user_model', 'address_on_profile_name')
        args = [getattr(self, name, None) for name in arg_names]
        return args
