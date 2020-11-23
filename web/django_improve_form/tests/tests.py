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


class HalfFailModel(FailModel):
    ignore = {'custom_username', }

    def get_email_field_name(self):
        return 'email_field'


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

    def test_user_works_address_fail(self):
        """Most fields on Model, email and username on UserModel, address_names not found. """
        models = []
        name_for_email, name_for_user = None, None
        for model in (self.model, self.user_model):
            if hasattr(model, 'get_email_field_name') and hasattr(model, 'USERNAME_FIELD'):
                models.append(model)
        target = models[0]
        name_for_email = target.get_email_field_name()
        name_for_user = target.USERNAME_FIELD
        initial = [*self.constructor_names, *self.early_names]
        settings = [self.username_flag_name, "password1", "password2", *self.extra_names]
        expected_fields = [*initial, *settings]
        expected_alt = [name_for_email, name_for_user]  # self.username_flag_name, *self.extra_names,
        expected_missing = [
            'billing_address_1', 'billing_address_2',
            'billing_city', 'billing_country_area', 'billing_postcode',
            'billing_country_code',
            ]
        actual_fields, actual_alt, actual_missing = make_names(*self.get_name_args())

        self.assertEqual(expected_fields, actual_fields)
        self.assertEqual(expected_alt, actual_alt)
        self.assertEqual(expected_missing, actual_missing)

    @skip("Not Implemented")
    def test_profile_address(self):
        """The address fields are on the Profile model. """
        self.address_on_profile_name = ProfileModel()
        models = []
        name_for_email, name_for_user = None, None
        for model in (self.model, self.user_model):
            if hasattr(model, 'get_email_field_name') and hasattr(model, 'USERNAME_FIELD'):
                models.append(model)
        if not models:
            if not name_for_email:
                message = "The model or User model must have a 'get_email_field_name' method. "
            else:
                message = "The model or User model must have a 'USERNAME_FIELD' property. "
            with self.assertRaisesMessage(ImproperlyConfigured, message):
                make_names(*self.get_name_args())
            return
        else:
            target = models[0]
            name_for_email = target.get_email_field_name()
            name_for_user = target.USERNAME_FIELD

        initial = [*self.constructor_names, *self.early_names]
        settings = [self.username_flag_name, "password1", "password2", *self.extra_names]
        expected_fields = [*initial, *settings]
        expected_alt = [name_for_email, name_for_user]  # self.username_flag_name, *self.extra_names,
        # address_names = [
        #     'billing_address_1', 'billing_address_2',
        #     'billing_city', 'billing_country_area', 'billing_postcode',
        #     'billing_country_code',
        #     ]
        expected_missing = []
        actual_fields, actual_alt, actual_missing = make_names(*self.get_name_args())
        print("================== test_profile_address: Results ========================")
        print(expected_fields, '\n\n', expected_alt, '\n\n', expected_missing, '\n')
        print("---------------------------------\n")
        print(actual_fields, '\n\n', actual_alt, '\n\n', actual_missing, '\n')

        self.assertEqual(expected_fields, actual_fields)
        self.assertEqual(expected_alt, actual_alt)
        self.assertEqual(expected_missing, actual_missing)

    @skip("Not Implemented")
    def test_no_user_like_model(self):
        """Both the 'model_class' and 'user_model_class' are lacking the expected User model methods. """
        self.user_model_class = FailModel
        self.user_model = FailModel()
        models = []
        for model in (self.model, self.user_model):
            if hasattr(model, 'get_email_field_name') and hasattr(model, 'USERNAME_FIELD'):
                models.append(model)
        self.assertFalse(models)
        message = "The model or User model must have a 'get_email_field_name' method. "
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            make_names(*self.get_name_args())

    @skip("Not Implemented")
    def test_no_username_ref_model(self):
        """Both the 'model_class' and 'user_model_class' are lacking the 'USERNAME_FIELD' reference. """
        self.user_model_class = HalfFailModel
        self.user_model = HalfFailModel()
        models = []
        for model in (self.model, self.user_model):
            if hasattr(model, 'get_email_field_name') and hasattr(model, 'USERNAME_FIELD'):
                models.append(model)
        self.assertFalse(models)
        message = "The model or User model must have a 'USERNAME_FIELD' property. "
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            make_names(*self.get_name_args())

    @skip("Not Implemented")
    def test_no_settings_passed(self):
        """If the third parameter for 'make_names' function is not a str, tuple, or list, then use an empty list. """
        self.username_flag_name = None
        models = []
        name_for_email, name_for_user = None, None
        for model in (self.model, self.user_model):
            if hasattr(model, 'get_email_field_name') and hasattr(model, 'USERNAME_FIELD'):
                models.append(model)
        if not models:
            if not name_for_email:
                message = "The model or User model must have a 'get_email_field_name' method. "
            else:
                message = "The model or User model must have a 'USERNAME_FIELD' property. "
            with self.assertRaisesMessage(ImproperlyConfigured, message):
                make_names(*self.get_name_args())
            return
        else:
            target = models[0]
            name_for_email = target.get_email_field_name()
            name_for_user = target.USERNAME_FIELD

        initial = [*self.constructor_names, *self.early_names]
        settings = ["password1", "password2", *self.extra_names]  # Since it is None, not self.username_flag_name
        expected_fields = [*initial, *settings]
        expected_alt = [name_for_email, name_for_user]
        address_names = [
            'billing_address_1', 'billing_address_2',
            'billing_city', 'billing_country_area', 'billing_postcode',
            'billing_country_code',
            ]
        expected_missing = address_names
        actual_fields, actual_alt, actual_missing = make_names(*self.get_name_args())
        print("================== test_no_settings_passed: Results ========================")
        print(expected_fields, '\n\n', expected_alt, '\n\n', expected_missing, '\n')
        print("---------------------------------\n")
        print(actual_fields, '\n\n', actual_alt, '\n\n', actual_missing, '\n')

        self.assertEqual(expected_fields, actual_fields)
        self.assertEqual(expected_alt, actual_alt)
        self.assertEqual(expected_missing, actual_missing)

    @skip("Not Implemented")
    def test_misc_feature(self):
        """Docs """

        pass

    # @skip("Not Implemented")
    # def test_no_user_like_model(self):
    #     """Both the 'model_class' and 'user_model_class' are lacking the expected User model methods. """
    #     self.user_model_class = FailModel
    #     self.user_model = FailModel()
    #     models = []
    #     for model in (self.model, self.user_model):
    #         if hasattr(model, 'get_email_field_name') and hasattr(model, 'USERNAME_FIELD'):
    #             models.append(model)
    #     self.assertFalse(models)
    #     message = "The model or User model must have a 'get_email_field_name' method. "
    #     with self.assertRaisesMessage(ImproperlyConfigured, message):
    #         make_names(*self.get_name_args())

# End tests.py
