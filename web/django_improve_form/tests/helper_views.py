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
    login_ability_needed = False
    request_method = 'get'
    request_kwargs = {}

    def setup_view(self, method, req_kwargs=None, template_name=None, *args, **init_kwargs):
        """A view instance that mimics as_view() returned callable. For args and kwargs match format as reverse(). """
        method = method or self.request_method
        if isinstance(method, str):
            method = method.lower()
        allowed_methods = getattr(self.viewClass, 'http_method_names', {'get', })
        allowed_methods = set(ea.lower() for ea in allowed_methods)
        if method not in allowed_methods:  # or not getattr(self.viewClass, method, None)
            raise ValueError("Method '{}' not recognized as an allowed method string. ".format(method))
        if method in ('post', 'put'):
            req_kwargs = self.setup_post_request(req_kwargs)
        req_kwargs = req_kwargs or {}
        if self.request_as_factory and not self.login_ability_needed:
            factory = RequestFactory()
            request = getattr(factory, method)('/', **req_kwargs)
        else:
            request = getattr(self.client, method)(reverse(self.url_name), **req_kwargs)
        # TODO: Should MimicAsView be updated to actually call the view get method?
        key = 'template_name'
        template_name = template_name or getattr(self, key, None) or getattr(self.viewClass, key, None)
        view = self.viewClass(template_name=template_name, **init_kwargs)
        # emulate View.setup()
        view.request = request
        view.args = args
        view.kwargs = init_kwargs
        return view

    def setup_post_request(self, initial=None, exclude=(), extra=(), **kwargs):
        """Returns request kwargs, with some form submission data, for a POST request. """
        req_kwargs = self.request_kwargs.copy() if initial is None else initial
        files = req_kwargs.get('files', {})
        files.update(kwargs.get('files', {}))
        if files:
            req_kwargs['files'] = files
        data = req_kwargs.get('data', {})
        data.update(kwargs.get('data', {}))
        if exclude:
            data = {k: v for k, v in data.items() if k not in exclude}
        extra_kwargs = {}
        if isinstance(extra, dict):
            extra_kwargs = extra
        elif extra:
            extra_kwargs = {name: kwargs[name] for name in extra if name in kwargs}
            # needed_names = [name for name in extra if name not in extra_kwargs]
        data.update(extra_kwargs)
        req_kwargs['data'] = data
        return req_kwargs

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

    def setUp(self):
        # self.viewClass.model = getattr(self.viewClass, 'model', None) or get_user_model()
        # self.expected_form.Meta.model = getattr(self.expected_form.Meta, 'model', None) or get_user_model()
        user = self.make_user()
        req_kwargs = self.request_kwargs.copy()
        if self.request_method in ('post', 'put') and 'data' not in req_kwargs:
            user_kwargs = {'form_only': True}
            if self.user_type != 'anonymous':
                user_kwargs.update(initial=2)
            user_setup = self.setup_user(**user_kwargs)
            req_kwargs.update(data=user_setup)
        self.view = self.setup_view(self.request_method, req_kwargs)
        self.view.request.user = user
        if self.user_type != 'anonymous' and hasattr(self.view, 'get_object'):
            self.view.object = user  # TODO: Should MimicAsView be updated to actually call the view get method?

    def setup_user(self, initial=1, exclude=(), extra={}, form_only=False, **kwargs):
        """Returns dict of user settings. Use password_count=2 for password confirmation inputs. """
        initial_lookup = {1: USER_DEFAULTS, 2: OTHER_USER}
        if isinstance(initial, int):
            initial = initial_lookup[initial]
        elif not isinstance(initial, dict):
            raise ImproperlyConfigured("If not passing an integer, the initial parameter should be a dictionary. ")
        user_setup = initial.copy()
        if exclude:
            user_setup = {key: value for key, value in user_setup.items() if key not in exclude}
        user_setup.update(extra)
        if form_only:
            old_password = user_setup.pop('password', '')
            user_setup.setdefault('password1', old_password)
            user_setup.setdefault('password2', old_password)
        return user_setup

    def make_user(self, user_type=None, **kwargs):
        """For the given settings in kwargs, create and return a User object. """
        user_type = self.user_type if user_type is None else user_type
        lookup_user_settings = {
            'superuser': {'is_staff': True, 'is_superuser': True},
            'admin': {'is_staff': True, 'is_superuser': False},
            'user': {'is_staff': False, 'is_superuser': False},
            'inactive': {'is_staff': False, 'is_superuser': False, 'is_active': False},
            }
        if user_type == 'anonymous':
            user = AnonymousUser()
        else:
            UserModel = get_user_model()
            kwargs = self.setup_user(**kwargs)
            kwargs.update(lookup_user_settings.get(user_type, {}))
            user = UserModel.objects.create(**kwargs)
            user.save()
        return user

    def test_get_context_data(self):
        expected_defaults = self.viewClass.default_context
        context = self.view.get_context_data()
        self.assertIsInstance(context['view'], self.viewClass)
        self.assertIsInstance(context['form'], self.expected_form)
        for key, val in expected_defaults.items():
            self.assertEqual(context[key], val)

    def update_to_post_form(self):
        """Called if needing an HTTP POST request on the form when we currently only have a GET. """
        pw_fake = 'TestPW!42'
        data = OTHER_USER.copy()
        data.pop('password')
        pw_data = {name: pw_fake for name in ('password1', 'password2')}
        data.update(pw_data)
        req_kwargs = {'data': data}
        self.view = self.setup_view('post', req_kwargs)
        form = self.view.get_form()
        if getattr(form, 'cleaned_data', None) is None:
            form.cleaned_data = pw_data
        return form

    def test_form_process(self):
        """Does the given form with submitted data validate? """
        self.old_view = self.view
        print(f"==================== {self.view.__class__.__name__} TEST FORM PROCESS ==========================")
        if self.request_method not in ('post', 'put'):
            form = self.update_to_post_form()
        else:
            form = self.view.get_form()
        pprint(form)
        pprint(dir(form))
        print("-----------------------------------------------")
        if not form.is_valid():
            pprint(form.errors)
        else:
            print("VALID FORM! ")
        # pprint(dir(self.view))
        new_user = 'NOT CREATED YET'
        try:
            new_user = form.save()
        except Exception as e:
            print("Got an exception on saving. ")
            pprint(e)
        print(new_user)
        pass
        if self.view != self.old_view:
            self.view = self.old_view

    @skip("Not working yet. Not Implemented")
    def test_register(self):
        self.old_view = self.view
        if self.request_method not in ('post', 'put'):
            form = self.update_to_post_form()
        else:
            form = self.view.get_form()
        print(f"======================== {self.view.__class__.__name__} TESTS - REGISTER =======================")
        pprint(getattr(form, 'request', 'FORM REQUEST NOT FOUND'))
        pprint(getattr(self.view, 'request', 'View REQUEST NOT FOUND'))
        pprint(getattr(self.view.request, 'session', 'SESSION NOT FOUND'))
        print("-------------------------------------------")
        pprint(form)
        print("-------------------------------------------")
        pprint(self.view.request)
        print("-------------------------------------------")
        pprint(dir(self.view.request))
        print("-------------------------------------------")
        register = self.view.register(form)
        # register = self.view.register(form)
        pprint(register)

        pass
        if self.view != self.old_view:
            self.view = self.old_view

    @skip("Not Implemented")
    def test_other(self):
        """Placeholder for other tests. """
        pass
