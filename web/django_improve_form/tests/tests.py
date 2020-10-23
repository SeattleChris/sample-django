from django.test import TestCase  # , TransactionTestCase, Client, RequestFactory,
from unittest import skip
# from django.contrib.auth import get_user_model
from .helper_admin import AdminSetupTests  # , AdminModelManagement
from .helper_views import MimicAsView, USER_DEFAULTS
from .helper_general import AnonymousUser, UserModel  # , MockRequest, MockUser, MockStaffUser, MockSuperUser
from ..views import RegisterSimpleFlowView, RegisterActivateFlowView, ModifyUser
from ..views import RegisterModelSimpleFlowView, RegisterModelActivateFlowView
from ..forms import RegisterUserForm, RegisterChangeForm, RegisterModelForm
# from django.conf import settings
# from django.core.exceptions import ObjectDoesNotExist
# from django.db.models import Q, Max, Subquery
# from django.urls import reverse
# from datetime import date, time, timedelta, datetime as dt
from pprint import pprint

# Create your tests here.


class AdminGeneralModelsTests(AdminSetupTests, TestCase):
    pass


class BaseRegisterTests(MimicAsView):
    url_name = 'model_signup'
    viewClass = RegisterModelSimpleFlowView
    expected_form = RegisterModelForm
    user_type = 'anonymous'  # 'superuser' | 'admin' | 'user' | 'inactive' | 'anonymous'

    def setUp(self):
        # self.viewClass.model = getattr(self.viewClass, 'model', None) or get_user_model()
        # self.expected_form.Meta.model = getattr(self.expected_form.Meta, 'model', None) or get_user_model()
        self.view = self.setup_view('get')
        user_setup = USER_DEFAULTS.copy()
        if self.user_type == 'anonymous':
            user = AnonymousUser()
        elif self.user_type == 'superuser':
            temp = {'is_staff': True, 'is_superuser': True}
            user_setup.update(temp)
            user = UserModel.objects.create(**user_setup)
            user.save()
        elif self.user_type == 'admin':
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
        self.view.request.user = user
        if self.user_type != 'anonymous' and hasattr(self.view, 'get_object'):
            self.view.object = user  # TODO: Should MimicAsView be updated to actually call the view get method?

    def test_get_context_data(self):
        expected_defaults = self.viewClass.default_context
        context = self.view.get_context_data()
        self.assertIsInstance(context['view'], self.viewClass)
        self.assertIsInstance(context['form'], self.expected_form)
        for key, val in expected_defaults.items():
            self.assertEqual(context[key], val)

    @skip("Not Implemented")
    def test_register(self):
        form = self.view.get_form()
        register = self.view.register(form)
        print("======================== SIMPLE FLOW TESTS - REGISTER =======================")
        pprint(register)


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

    def setUp(self):
        self.view = self.setup_view('get')
        user = AnonymousUser()
        self.view.request.user = user


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
