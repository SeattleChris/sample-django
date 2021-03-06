from django.test import Client  # , TestCase
from unittest import skip
from django.apps import apps
from django.conf import settings
from django.urls import reverse
from django.contrib.admin.sites import AdminSite
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Permission
# from django.contrib.auth.forms import UserChangeForm  # , UserCreationForm
from django.contrib.sessions.models import Session as Session_contrib
from django.contrib.contenttypes.models import ContentType
# from django.forms import ValidationError
# from datetime import date, time, timedelta  # , datetime as dt
from os import environ
# from copy import deepcopy
# from types import GeneratorType
from django.utils.module_loading import import_string
from .helper_general import MockRequest, MockUser, MockSuperUser  # UserModel, AnonymousUser,  MockStaffUser,
# Resource = import_string('APPNAME.models.Resource')
# ResourceAdmin = import_string('APPNAME.admin.ResourceAdmin')

APP_NAME = __package__.split('.')[0]
main_admin = import_string(APP_NAME + '.admin.admin')
request = MockRequest()
request.user = MockSuperUser()
fail_req = MockRequest()
fail_req.user = MockUser()


class AdminSetupTests:
    """General expectations of the Admin. """

    def test_admin_set_for_all_expected_models(self):
        """Make sure all models can be managed in the admin. """
        models = apps.get_models()
        registered_admins_dict = main_admin.site._registry
        registered_models = list(registered_admins_dict.keys())
        # All UserHC (imported as User here) management done by proxy models: StaffUser and StudentUser
        # models.remove(User)
        # The following models are from packages we do not need to test.
        models.remove(LogEntry)
        models.remove(Permission)
        models.remove(ContentType)
        models.remove(Session_contrib)
        for model in models:
            self.assertIn(model, registered_models)

    @skip("Not Implemented")
    def test_createsu_command(self):
        """Our custom command to create a Superuser as an initial admin """
        # TODO: Write tests for when there is no superuser.
        # This seemed to not work when using this command on PythonAnywhere the first time
        pass


class AdminModelManagement:
    """Tests for Model create or modify in the Admin site. """
    Model = None
    AdminClass = None
    FormClass = None
    model_fields_not_in_admin = ['id', 'date_added', 'date_modified', ]  # list related models
    associated = [
        {
            'model': Model,
            'consts': {},
            'variations': [],  # either a list of stings to combine with 'var_name', or a list of dicts.
            'var_name': None,  # if a string, then for 'ea' in variations will be replaced with {var_name: ea}.
            'mod': '',  # As this is the main model, if defined, this field will hold a unique string of m_<num>.
        },
        {
            'model': None,
            'consts': {},
            'variations': [],  # either a list of stings to combine with 'var_name', or a list of dicts.
            'var_name': None,  # if a string, then for 'ea' in variations will be replaced with {var_name: ea}.
            'related_name': '',  # As an associated model, this is the parameter name for main Model.
        },
        {
            'model': None,
            'consts': {},
            'variations': [],  # either a list of stings to combine with 'var_name', or a list of dicts.
            'var_name': None,  # if a string, then for 'ea' in variations will be replaced with {var_name: ea}.
            'related_name': '',  # As an associated model, this is the parameter name for main Model.
        },
        ]

    def make_model_data(self, data, mod_opts=None):
        opts = []
        if isinstance(data, dict):
            if not data.get('model', None):
                return mod_opts
            cur_vars = data.get('mod_vars', [])
            if data.get('var_name', None):
                cur_vars = [{data['var_name']: v} for v in cur_vars]
            consts = data.get('consts', {})
            cur_opts = [consts] if not cur_vars else [dict(**v, **consts) for v in cur_vars]
            related_name = data.get('related_name', None)
            if not related_name:
                return cur_opts
            for r in cur_opts:
                obj = data['model'].objects.create(**r)
                opts += [dict(**{related_name: obj}, **m) for m in mod_opts]
        elif data and isinstance(data, list):
            if not mod_opts:
                mod_opts = []  # Current list of main model options, Eventually it will have all possible combos.
            for ea in data:
                mod_opts = self.make_modelset(ea, mod_opts=mod_opts)
            model = data[0]['model']
            mod = data[0].get('mod', None)  # used if a unique name or other string is needed for each model.
            for i, opt in enumerate(mod_opts):
                if mod:
                    opt.update({mod: f"m_{i}"})
                opts.append(model.objects.create(**opt))
        return opts

    def test_admin_uses_correct_admin(self):
        """The admin site should use the expected AdminClass for the Model. """
        registered_admins_dict = main_admin.site._registry
        model_admin = registered_admins_dict.get(self.Model, None)
        self.assertIsInstance(model_admin, self.AdminClass)

    def test_admin_uses_expected_form(self):
        """The admin for this model utilizes the expected form class. """
        current_admin = self.AdminClass(model=self.Model, admin_site=AdminSite())
        form = getattr(current_admin, 'form', None)
        self.assertEqual(form, self.FormClass)

    def test_admin_has_model_fields(self):
        """The AdminClass should use all the expected fields of the Model. """
        current_admin = self.AdminClass(model=self.Model, admin_site=AdminSite())
        admin_fields = []
        if current_admin.fields:
            for ea in current_admin.fields:
                if not isinstance(ea, (list, tuple)):
                    ea = [ea]
                admin_fields.extend(ea)
        if current_admin.fieldsets:
            for ea in current_admin.fieldsets:
                admin_fields.extend(ea[1].get('fields', []))
        admin_fields = tuple(admin_fields)
        model_fields = [field.name for field in self.Model._meta.get_fields(include_parents=False)]
        model_fields = [ea for ea in model_fields if ea not in self.model_fields_not_in_admin]
        model_fields = tuple(model_fields)
        self.assertTupleEqual(admin_fields, model_fields)

    def get_login_kwargs(self):
        """Deprecated? If we need an admin login, this will be the needed dictionary to pass as kwargs. """
        password = environ.get('SUPERUSER_PASS', '')
        admin_user_email = environ.get('SUPERUSER_EMAIL', settings.ADMINS[0][1])
        # User.objects.create_superuser(admin_user_email, admin_user_email, password)
        return {'username': admin_user_email, 'password': password}

    def response_after_login(self, url, client):
        """Deprecated? If the url requires a login, perform a login and follow the redirect. """
        get_response = client.get(url)
        if 'url' in get_response:  # Login, then try the url again.
            login_kwargs = self.get_login_kwargs()
            client.post(get_response.url, login_kwargs)
            get_response = client.get(url)
        return get_response

    def test_admin_can_create_first_model(self):
        """The first Model can be made in empty database (even if later models compute values from existing).  """
        c = Client(user=MockSuperUser())
        add_url = ' '.join((APP_NAME, self.Model.__name__, 'add'))
        add_url = reverse(add_url)
        # login_kwargs = self.get_login_kwargs()
        # login_try = c.login(**login_kwargs)
        kwargs = {'name': 'test_create'}
        # Update kwargs with info requested for the admin form to create a model.
        post_response = c.post(add_url, kwargs, follow=True)
        found = self.Model.objects.filter(name=kwargs['name']).first()
        # self.assertTrue(login_try)
        self.assertEqual(post_response.status_code, 200)
        self.assertIsNotNone(found)
        self.assertIsInstance(found, self.Model)

    def get_expected_column_values(self, *args, **kwargs):
        """Method for determining what the expected values for computed column display in an Admin view. """
        expected = []
        associated = kwargs.get('associated', getattr(self, 'associated', [{}]))
        # TODO: Magic goes here.
        value_lookup = kwargs.get('value_lookup', [])
        for collect in value_lookup:
            result = '_'.join((associated[i][prop][j] for i, prop, j in collect))
            expected.append(result)
        return expected

    def get_computed_column_info(self, expected_values=[], associated=None, col_name=''):
        """Returns an iterable of expected, actual pairs, given the expected and data creating information. """
        data_models = self.make_model_data(associated)
        current_admin = self.AdminClass(model=self.Model, admin_site=AdminSite())
        get_col = getattr(current_admin, col_name)
        return zip(expected_values, (get_col(ea) for ea in data_models))

    def test_computed_column_values(self, *args, **kwargs):
        """Confirm results if the Admin displays certain columns with a computed or modified output. """
        # determine parameters to generate expected_values.
        expected_values = getattr(self, 'expected_values', None)
        expected_values = expected_values or self.get_expected_column_values(*args, **kwargs)
        associated = kwargs.get('associated', getattr(self, 'associated', {}))
        col_name = kwargs.get('col_name', getattr(self, 'col_name', ''))
        test_pairs = self.get_computed_column_info(expected_values, associated, col_name)
        for expected, actual in test_pairs:
            self.assertEqual(expected, actual)

    def test_computed_value_default_value(self, *args, **kwargs):
        """If certain conditions result in a default for a computed value, then check this functionality here. """
        # setup parameters that trigger a default value condition.
        expected_values = getattr(self, 'expected_default_values', None)
        expected_values = expected_values or self.get_expected_column_values(*args, **kwargs)
        associated = kwargs.get('associated', getattr(self, 'associated_for_default', {}))
        col_name = kwargs.get('col_name', getattr(self, 'col_name', ''))
        test_pairs = self.get_computed_column_info(expected_values, associated, col_name)
        for expected, actual in test_pairs:
            self.assertEqual(expected, actual)

    def test_not_implemented_get_version_matrix(self):
        current_admin = self.AdminClass(model=self.Model, admin_site=AdminSite())
        with self.assertRaises(NotImplementedError):
            current_admin.get_version_matrix()


# class AdminClassDayListFilterTests(TestCase):
#     # related_models = (ClassOfferAdmin, RegistrationAdmin)
#     student_profile_attribute = 'student'  # 'profile' if only one profile model.
#     staff_profile_attribute = 'staff'  # 'profile' if only one profile model.

#     def test_admin_classoffer_lookup(self):
#         Registration = self.Model
#         RegistrationAdmin = self.AdminModel
#         ClassOffer = self.Related_Model
#         ClassOfferAdmin = self.AdminRelated
#         Session = self.Parent_Model_a
#         Subject = self.Parent_Model_b
#         ClassDayListFilter = self.Admin_ListFilter

#         key_day, name = date.today(), 'sess1'
#         publish = key_day - timedelta(days=7*3+1)
#         sess1 = Session.objects.create(name=name, key_day_date=key_day, max_day_shift=6, publish_date=publish)
#         subj = Subject.objects.create(version=Subject.VERSION_CHOICES[0][0], name="test_subj")
#         kwargs = {'subject': subj, 'session': sess1, 'start_time': time(19, 0)}
#         classoffers = [ClassOffer.objects.create(class_day=k, **kwargs) for k, v in ClassOffer.DOW_CHOICES if k % 2]
#         expected_lookup = ((k, v) for k, v in ClassOffer.DOW_CHOICES if k % 2)

#         current_admin = ClassOfferAdmin(model=ClassOffer, admin_site=AdminSite())
#         day_filter = ClassDayListFilter(request, {}, ClassOffer, current_admin)
#         lookup = day_filter.lookups(request, current_admin)

#         self.assertEqual(len(classoffers), 3)
#         self.assertEqual(ClassOffer.objects.count(), 3)
#         self.assertIsInstance(lookup, GeneratorType)
#         self.assertEqual(list(expected_lookup), list(lookup))

#     def test_admin_classoffer_queryset(self):
#         Registration = self.Model
#         RegistrationAdmin = self.AdminModel
#         ClassOffer = self.Related_Model
#         ClassOfferAdmin = self.AdminRelated
#         Session = self.Parent_Model_a
#         Subject = self.Parent_Model_b
#         ClassDayListFilter = self.Admin_ListFilter

#         key_day, name = date.today(), 'sess1'
#         publish = key_day - timedelta(days=7*3+1)
#         sess1 = Session.objects.create(name=name, key_day_date=key_day, max_day_shift=6, publish_date=publish)
#         subj = Subject.objects.create(version=Subject.VERSION_CHOICES[0][0], name="test_subj")
#         kwargs = {'subject': subj, 'session': sess1, 'start_time': time(19, 0)}
#         classoffers = [ClassOffer.objects.create(class_day=k, **kwargs) for k, v in ClassOffer.DOW_CHOICES if k % 2]
#         expected_lookup_list = [(k, v) for k, v in ClassOffer.DOW_CHOICES if k % 2]

#         current_admin = ClassOfferAdmin(model=ClassOffer, admin_site=AdminSite())
#         day_filter = ClassDayListFilter(request, {}, ClassOffer, current_admin)
#         model_qs = current_admin.get_queryset(request)
#         expected_qs = model_qs.filter(class_day__in=(k for k, v in expected_lookup_list))
#         qs = day_filter.queryset(request, model_qs)

#         self.assertEqual(len(classoffers), 3)
#         self.assertSetEqual(set(expected_qs), set(qs))

#     def test_admin_registration_lookup(self):
#         Registration = self.Model
#         RegistrationAdmin = self.AdminModel
#         ClassOffer = self.Related_Model
#         ClassOfferAdmin = self.AdminRelated
#         Session = self.Parent_Model_a
#         Subject = self.Parent_Model_b
#         ClassDayListFilter = self.Admin_ListFilter

#         key_day, name = date.today(), 'sess1'
#         publish = key_day - timedelta(days=7*3+1)
#         sess1 = Session.objects.create(name=name, key_day_date=key_day, max_day_shift=6, publish_date=publish)
#         subj = Subject.objects.create(version=Subject.VERSION_CHOICES[0][0], name="test_subj")
#         kwargs = {'subject': subj, 'session': sess1, 'start_time': time(19, 0)}
#         classoffers = [ClassOffer.objects.create(class_day=k, **kwargs) for k, v in ClassOffer.DOW_CHOICES if k % 2]
#         expected_lookup = ((k, v) for k, v in ClassOffer.DOW_CHOICES if k % 2)

#         password = environ.get('SUPERUSER_PASS', '')
#         admin_user_email = environ.get('SUPERUSER_EMAIL', settings.ADMINS[0][1])
#         user = User.objects.create_superuser(admin_user_email, admin_user_email, password)
#         user.first_name = "test_super"
#         user.last_name = "test_user"
#         user.save()
#         student = getattr(user, self.student_profile_attribute, None)
#         registrations = [Registration.objects.create(student=student, classoffer=ea) for ea in classoffers]

#         current_admin = RegistrationAdmin(model=Registration, admin_site=AdminSite())
#         day_filter = ClassDayListFilter(request, {}, Registration, current_admin)
#         lookup = day_filter.lookups(request, current_admin)

#         self.assertEqual(len(registrations), 3)
#         self.assertEqual(Registration.objects.count(), 3)
#         self.assertIsInstance(lookup, GeneratorType)
#         self.assertEqual(list(expected_lookup), list(lookup))

#     def test_admin_registration_queryset(self):
#         Registration = self.Model
#         RegistrationAdmin = self.AdminModel
#         ClassOffer = self.Related_Model
#         ClassOfferAdmin = self.AdminRelated
#         Session = self.Parent_Model_a
#         Subject = self.Parent_Model_b
#         ClassDayListFilter = self.Admin_ListFilter

#         key_day, name = date.today(), 'sess1'
#         publish = key_day - timedelta(days=7*3+1)
#         sess1 = Session.objects.create(name=name, key_day_date=key_day, max_day_shift=6, publish_date=publish)
#         subj = Subject.objects.create(version=Subject.VERSION_CHOICES[0][0], name="test_subj")
#         kwargs = {'subject': subj, 'session': sess1, 'start_time': time(19, 0)}
#         classoffers = [ClassOffer.objects.create(class_day=k, **kwargs) for k, v in ClassOffer.DOW_CHOICES if k % 2]
#         expected_lookup = ((k, v) for k, v in ClassOffer.DOW_CHOICES if k % 2)

#         password = environ.get('SUPERUSER_PASS', '')
#         admin_user_email = environ.get('SUPERUSER_EMAIL', settings.ADMINS[0][1])
#         user = User.objects.create_superuser(admin_user_email, admin_user_email, password)
#         student = getattr(user, self.student_profile_attribute, None)
#         registrations = [Registration.objects.create(student=student, classoffer=ea) for ea in classoffers]

#         current_admin = RegistrationAdmin(model=Registration, admin_site=AdminSite())
#         day_filter = ClassDayListFilter(request, {}, Registration, current_admin)
#         model_qs = current_admin.get_queryset(request)
#         expected_qs = model_qs.filter(classoffer__class_day__in=(k for k, v in expected_lookup))
#         qs = day_filter.queryset(request, model_qs)

#         self.assertEqual(len(registrations), 3)
#         self.assertEqual(model_qs.model, Registration)
#         self.assertSetEqual(set(expected_qs), set(qs))


# class AdminUserHCTests:
#     """Testing mix-in for proxy models of UserHC. Expect updates for: Model, AdminClass, Model_queryset. """
#     Model = None
#     AdminClass = None
#     FormClass = None  # UserChangeForm
#     Model_queryset = None  # If left as None, will use the settings from model_specific_setups for given Model.
#     Model_ChangeForm = None  # If left as None, will use the default Admin UserChangeForm
#     user_setup = {'email': 'fake@site.com', 'password': '1234', 'first_name': 'fa', 'last_name': 'fake', }
#     model_specific_setups = {StaffUser: {'is_teacher': True, }, StudentUser: {'is_student': True, }, }

#     def make_test_users(self):
#         m_setup = self.model_specific_setups
#         users_per_model = min(4, 26 // len(m_setup))
#         alpha = (chr(ord('a') + i) for i in range(0, 26))
#         users = []
#         for model in m_setup:
#             chars = ''.join(next(alpha) for _ in range(users_per_model))
#             kwargs_many = [{k: x + v for k, v in self.user_setup.items()} for x in chars]
#             users += [User.objects.create_user(**kwargs, **m_setup[model]) for kwargs in kwargs_many]
#         return users, users_per_model

#     # def test_admin_uses_correct_admin(self):
#     #     """The admin site should use what was set for AdminClass for the model set in Model. """
#     #     registered_admins_dict = main_admin.site._registry
#     #     model_admin = registered_admins_dict.get(self.Model, None)
#     #     self.assertIsInstance(model_admin, self.AdminClass)

#     # def test_admin_uses_expected_form(self):
#     #     """The admin set for AdminClass utilizes the correct form. """
#     #     current_admin = self.AdminClass(model=self.Model, admin_site=AdminSite())
#     #     form = getattr(current_admin, 'form', None)
#     #     self.assertEqual(form, self.FormClass)

#     def test_get_queryset(self):
#         """Proxy models tend to be a subset of all models. This tests the queryset is as expected. """
#         current_admin = self.AdminClass(model=self.Model, admin_site=AdminSite())
#         users, users_per_model = self.make_test_users()
#         expected_qs = getattr(self, 'Model_queryset', None)
#         if not expected_qs:
#             expected_qs = self.Model.objects.filter(**self.model_specific_setups[self.Model])
#         actual_qs = current_admin.get_queryset(request)

#         self.assertEqual(len(users), users_per_model * len(self.model_specific_setups))
#         self.assertEqual(users_per_model, expected_qs.count())
#         self.assertEqual(users_per_model, actual_qs.count())
#         self.assertSetEqual(set(expected_qs), set(actual_qs))

#     def test_get_form_uses_custom_formfield_attrs_overrides(self):
#         current_admin = self.AdminClass(model=self.Model, admin_site=AdminSite())
#         form = current_admin.get_form(request)
#         fields = form.base_fields
#         expected_values = deepcopy(current_admin.formfield_attrs_overrides)
#         expected_values = {key: value for key, value in expected_values.items() if key in fields}
#         actual_values = {}
#         for name, field_attrs in expected_values.items():
#             if 'size' in field_attrs and 'no_size_override' not in field_attrs:
#                 input_size = float(fields[name].widget.attrs.get('maxlength', float("inf")))
#                 field_attrs['size'] = str(int(min(int(field_attrs['size']), input_size)))  # Modify expected_values
#             actual_values[name] = {key: fields[name].widget.attrs.get(key) for key in field_attrs}

#         self.assertDictEqual(expected_values, actual_values)

#     def test_get_form_modifies_input_size_for_small_maxlength_fields(self):
#         current_admin = self.AdminClass(model=self.Model, admin_site=AdminSite())
#         form = current_admin.get_form(request)
#         expected_values, actual_values = {}, {}
#         for name, field in form.base_fields.items():
#             if not current_admin.formfield_attrs_overrides.get(name, {}).get('no_size_override', False):
#                 display_size = float(field.widget.attrs.get('size', float('inf')))
#                 input_size = int(field.widget.attrs.get('maxlength', 0))
#                 if input_size:
#                     expected_values[name] = str(int(min(display_size, input_size)))
#                     actual_values[name] = field.widget.attrs.get('size', '')

#         self.assertDictEqual(expected_values, actual_values)


# class AdminStaffUserTests(AdminUserHCTests, TestCase):
#     Model = StaffUser
#     AdminClass = StaffUserAdmin
#     Model_queryset = User.objects.filter(is_staff=True)


# class AdminStudentUserTests(AdminUserHCTests, TestCase):
#     Model = StudentUser
#     AdminClass = StudentUserAdmin
#     Model_queryset = User.objects.filter(is_student=True)
