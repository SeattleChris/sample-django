from django.test import Client, RequestFactory  # , TestCase,  TransactionTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured  # , ValidationError, NON_FIELD_ERRORS  # , ObjectDoesNotExist
from unittest import skip  # @skip("Not Implemented")
from .helper_general import AnonymousUser  # , MockRequest
# , UserModel, MockRequest, MockUser, MockStaffUser, MockSuperUser, APP_NAME
from pprint import pprint

USER_DEFAULTS = {'email': 'user_fake@fake.com', 'password': 'test1234', 'first_name': 'f_user', 'last_name': 'fake_y'}
OTHER_USER = {'email': 'other@fake.com', 'password': 'test1234', 'first_name': 'other_user', 'last_name': 'fake_y'}


class TestFormLoginRequired:
    url_name = ''  # 'url_name' for the desired path '/url/to/view'
    # url = reverse(url_name)
    login_cred = {'username': '', 'password': ''}    # defined in fixture or with factory in setUp()
    viewClass = None
    expected_template = getattr(viewClass, 'template_name', '')
    expected_form = ''
    expected_error_field = ''
    login_redirect = '/login/'
    success_redirect = ''
    bad_data = {}
    good_data = {}

    def test_call_view_deny_anonymous(self):
        """Login is required for either get or post. """
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, self.login_redirect)
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(response, self.login_redirect)

    def test_call_view_load(self):
        """After login, can get the form. """
        self.client.login(**self.login_cred)
        response = self.client.get(self.url)
        # self.assertContains()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, self.expected_template)

    def test_call_view_fail_blank(self):
        """Submitting a blank form should get a form error. """
        self.client.login(**self.login_cred)
        data = {}  # blank data dictionary (on purpose)
        response = self.client.post(self.url, data)
        self.assertFormError(response, self.expected_form, self.expected_error_field, 'This field is required.')
        # etc. ...

    def test_call_view_fail_invalid(self):
        """Submitting an invalid form should get a form error. """
        self.client.login(**self.login_cred)
        response = self.client.post(self.url, self.bad_data)
        self.assertFormError(response, self.expected_form, self.expected_error_field, 'This field is required.')

    def test_call_view_success_invalid(self):
        """Submitting a valid form should give expected redirect. """
        self.client.login(**self.login_cred)
        response = self.client.post(self.url, self.bad_data)
        self.assertRedirects(response, self.success_redirect)


class MimicAsView:
    url_name = ''  # find in app.urls
    viewClass = None  # find in app.views
    query_order_by = None  # expected tuple or list if order_by is needed.
    request_as_factory = True  # Otherwise use Client.

    def setup_view(self, method, req_kwargs=None, template_name=None, *args, **init_kwargs):
        """A view instance that mimics as_view() returned callable. For args and kwargs match format as reverse(). """
        req_kwargs = req_kwargs or {}
        if isinstance(method, str):
            method = method.lower()
        allowed_methods = getattr(self.viewClass, 'http_method_names', {'get', })
        allowed_methods = set(ea.lower() for ea in allowed_methods)
        if method not in allowed_methods:  # or not getattr(self.viewClass, method, None)
            raise ValueError("Method '{}' not recognized as an allowed method string. ".format(method))
        if self.request_as_factory:
            factory = RequestFactory()
            request = getattr(factory, method)('/', **req_kwargs)
        else:
            c = Client()
            request = getattr(c, method)(self.url_name, **req_kwargs)
            self.my_client = c
        # TODO: Should MimicAsView be updated to actually call the view get method?
        key = 'template_name'
        template_name = template_name or getattr(self, key, None) or getattr(self.viewClass, key, None)
        view = self.viewClass(template_name=template_name, **init_kwargs)
        # emulate View.setup()
        view.request = request
        view.args = args
        view.kwargs = init_kwargs
        return view

    def prep_http_method(self, method):
        """To emulate View.as_view() we could do this on EACH http method. Normally as_view is only made with one. """
        method.view_class = self.viewClass
        method.init_kwargs = self.kwargs
        return method

    def setup_three_datasets(self, data_names=('first', 'second', 'third', )):
        """Three instances of model data that can, but is not required, to be related to a user. """
        Model = None
        # May need a category model that is Many-to-Many or otherwise connected with our data Model.
        Category = None
        # Setup the needed parameters.
        cat_const = {}
        cat_vars = []
        consts = {}
        variants = []
        # Create the data
        categories = [Category.objects.create(**cat_const, name=var) for var in cat_vars]
        data = []
        for var in variants:
            data = [Model.objects.create(**consts, var_name=var, category=ea) for ea in categories]
        return data

    def client_visit_view(self, good_text, bad_text=None, url_name=None):
        url_name = url_name or self.url_name
        if not isinstance(url_name, str):
            raise TypeError("Need a string for the url_name. ")
        if not isinstance(good_text, str):
            raise TypeError("Must have a string for 'good_text' parameter. ")
        if bad_text is not None and not isinstance(bad_text, str):
            raise TypeError("If included, must have a string for 'bad_text' parameter. ")
        url = reverse(url_name)
        c = Client()
        response = c.get(url)
        self.assertEqual(response.status_code, 200)
        if bad_text:
            self.assertNotContains(response, bad_text)
        self.assertContains(response, good_text)


class BaseRegisterTests(MimicAsView):
    url_name = None
    viewClass = None
    expected_form = None
    user_type = 'anonymous'  # 'superuser' | 'admin' | 'user' | 'inactive' | 'anonymous'
    request_method = 'get'
    request_kwargs = {}

    def setUp(self):
        # self.viewClass.model = getattr(self.viewClass, 'model', None) or get_user_model()
        # self.expected_form.Meta.model = getattr(self.expected_form.Meta, 'model', None) or get_user_model()
        user_kwargs = {} if self.request_method not in ('post', 'put') else {'password_count': 2}
        user, user_setup = self.setup_user(**user_kwargs)
        req_kwargs = self.request_kwargs.copy()
        if self.request_method in ('post', 'put') and 'data' not in req_kwargs:
            req_kwargs.update(data=user_setup)
        self.view = self.setup_view(self.request_method, req_kwargs)
        self.view.request.user = user
        if self.user_type != 'anonymous' and hasattr(self.view, 'get_object'):
            self.view.object = user  # TODO: Should MimicAsView be updated to actually call the view get method?

    def setup_user(self, initial=1, exclude=(), extra={}, password_count=1, **kwargs):
        """Returns dict of user settings. Use password_count=2 for password confirmation inputs. """
        initial_lookup = {1: USER_DEFAULTS.copy(), 2: OTHER_USER.copy()}
        if isinstance(initial, int):
            initial = initial_lookup[initial]
        elif not isinstance(initial, dict):
            raise ImproperlyConfigured("If not passing an integer, the initial parameter should be a dictionary. ")
        if exclude:
            initial = {key: value for key, value in initial.items() if key not in exclude}
        initial.update(extra)
        if password_count == 2:
            old_password = initial.pop('password')
            initial.setdefault('password1', old_password)
            initial.setdefault('password2', old_password)
        user_setup = initial.copy()
        user = None
        lookup_user_settings = {
            'superuser': {'is_staff': True, 'is_superuser': True},
            'admin': {'is_staff': True, 'is_superuser': False},
            'user': {'is_staff': False, 'is_superuser': False},
            'inactive': {'is_staff': False, 'is_superuser': False, 'is_active': False},
            }
        if self.user_type == 'anonymous':
            user = AnonymousUser()
        else:
            UserModel = get_user_model()
            user_setup.update(lookup_user_settings.get(self.user_type, {}))
            user = UserModel.objects.create(**user_setup)
            user.save()
        return user, initial

    def test_get_context_data(self):
        expected_defaults = self.viewClass.default_context
        context = self.view.get_context_data()
        self.assertIsInstance(context['view'], self.viewClass)
        self.assertIsInstance(context['form'], self.expected_form)
        for key, val in expected_defaults.items():
            self.assertEqual(context[key], val)

    @skip("Not working yet. Not Implemented")
    def test_register(self):
        pw_fake = 'TestPW!42'
        data = OTHER_USER.copy()
        data.pop('password')
        data.update({name: pw_fake for name in ('password1', 'password2')})
        req_kwargs = {'data': data, 'session': 'fakesessionname'}
        self.post_view = self.setup_view('post', req_kwargs)
        form = self.post_view.get_form()
        print("======================== TESTS - REGISTER =======================")
        pprint(form)
        print("-------------------------------------------")
        pprint(self.post_view.request)
        print("-------------------------------------------")
        pprint(self.view.request)
        print("-------------------------------------------")
        # form.cleaned_data = {'password1': pw_fake, 'password2': pw_fake}
        register = self.post_view.register(form)
        pprint(register)
