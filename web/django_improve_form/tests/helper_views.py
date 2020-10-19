from django.test import Client, RequestFactory  # , TestCase,  TransactionTestCase
from django.urls import reverse
# from django.conf import settings
from django.utils.module_loading import import_string
# from unittest import skip  # @skip("Not Implemented")
# from datetime import time, timedelta, datetime as dt  # date,
# Resource = import_string('APPNAME.models.Resource')
UserModel = import_string('django.contrib.auth.models.User')
AnonymousUser = import_string('django.contrib.auth.models.AnonymousUser')
USER_DEFAULTS = {'email': 'user_fake@fake.com', 'password': 'test1234', 'first_name': 'f_user', 'last_name': 'fake_y'}
OTHER_USER = {'email': 'other@fake.com', 'password': 'test1234', 'first_name': 'other_user', 'last_name': 'fake_y'}


class MockRequest:
    pass


class MockUser:
    is_active = True
    is_authenticated = True
    is_anonymous = False
    is_staff = False
    is_superuser = False


class MockStaffUser(MockUser):
    is_staff = True
    is_superuser = False


class MockSuperUser(MockUser):
    is_staff = True
    is_superuser = True

    def has_perm(self, perm):
        return True


request = MockRequest()
request.user = MockSuperUser()


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

    def setup_view(self, method, req_kwargs=None, template_name=None, *args, **init_kwargs):
        """A view instance that mimics as_view() returned callable. For args and kwargs match format as reverse(). """
        req_kwargs = req_kwargs or {}
        if isinstance(method, str):
            method = method.lower()
        allowed_methods = getattr(self.viewClass, 'http_method_names', {'get', })
        if method not in allowed_methods or not getattr(self.viewClass, method, None):
            raise ValueError("Method '{}' not recognized as an allowed method string. ".format(method))
        factory = RequestFactory()
        request = getattr(factory, method)('/', **req_kwargs)

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
