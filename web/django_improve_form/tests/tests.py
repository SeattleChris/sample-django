from django.test import TestCase  # , TransactionTestCase, Client, RequestFactory,
from unittest import skip
from .helper_admin import AdminSetupTests  # , AdminModelManagement
from .helper_views import MimicAsView, USER_DEFAULTS
from ..views import RegisterSimpleFlowView, RegisterActivateFlowView, ModifyUser
from ..forms import RegisterUserForm, RegisterChangeForm
from .helper_general import AnonymousUser, UserModel  # , MockRequest, MockUser, MockStaffUser, MockSuperUser
# from django.conf import settings
# from django.core.exceptions import ObjectDoesNotExist
# from django.db.models import Q, Max, Subquery
# from django.urls import reverse
# from datetime import date, time, timedelta, datetime as dt
# from pprint import pprint

# Create your tests here.


class AdminGeneralModelsTests(AdminSetupTests, TestCase):
    pass


class SimpleFlowTests(MimicAsView, TestCase):
    url_name = 'django_registration_register'
    viewClass = RegisterSimpleFlowView
    expected_form = RegisterUserForm

    def setUp(self):
        self.view = self.setup_view('get')
        user = AnonymousUser()
        self.view.request.user = user

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
        # pprint(register)


class ModifyUserTests(MimicAsView, TestCase):
    url_name = 'user_update'
    viewClass = ModifyUser
    expected_form = RegisterChangeForm

    def setUp(self):
        self.view = self.setup_view('get')
        user = UserModel.objects.create(**USER_DEFAULTS)
        user.save()
        self.view.request.user = user
        self.view.object = user  # TODO: Should MimicAsView be updated to actually call the view get method?

    def test_get_object(self):
        expected = self.view.request.user
        actual = self.view.get_object()
        self.assertAlmostEqual(expected, actual)

    def test_get_context_data(self):
        expected_defaults = self.viewClass.default_context
        context = self.view.get_context_data()
        self.assertIsInstance(context['view'], self.viewClass)
        self.assertIsInstance(context['form'], self.expected_form)
        for key, val in expected_defaults.items():
            self.assertEqual(context[key], val)


class ActivateFlowTests(MimicAsView, TestCase):
    url_name = 'initial_signup'
    ViewClass = RegisterActivateFlowView
    expected_form = RegisterUserForm

    def setUp(self):
        self.view = self.setup_view('get')
        user = AnonymousUser()
        self.view.request.user = user

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
        # pprint(register)
