from django.test import TestCase  # , Client, override_settings, modify_settings, TransactionTestCase, RequestFactory
# from django.core.exceptions import ImproperlyConfigured  # , ValidationError
# from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
# from .helper_general import AnonymousUser, MockUser  # MockRequest, UserModel, MockStaffUser, MockSuperUser, APP_NAME
from django.forms import (Form, CharField, EmailField, BooleanField, ChoiceField, MultipleChoiceField,
                          HiddenInput, Textarea, RadioSelect, CheckboxSelectMultiple, CheckboxInput)
# , ModelForm, BaseModelForm, ModelFormMetaclass
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
from django_registration import validators
# from pprint import pprint

# # Base MixIns # #


class FocusForm(FocusMixIn, Form):
    hide_field = CharField(widget=HiddenInput(), initial='hide_data')
    disable_field = CharField(disabled=True, initial='disable_data')
    generic_field = CharField()
    another_field = CharField(initial='initial_data')


class CriticalForm(CriticalFieldMixIn, Form):
    generic_field = CharField()

    def generic_field_validators(self, fields, **opts):
        field_name = 'generic_field'
        validators_test = [validators.validate_confusables]
        fields[field_name].validators.extend(validators_test)
        return True


class ComputedForm(ComputedFieldsMixIn, Form):
    first = CharField(initial='first_value')
    second = CharField(initial='second_value')
    generic_field = CharField()
    test_field = CharField(initial='original_value')
    last = CharField(initial='last_value')

    computed_fields = ['test_field']
    test_value = 'UNCLEANED_COMPUTED'
    def test_func(self, value): return value[2:].lower()

    def compute_test_field(self):
        """Returns the pre-cleaned value for test_field. """
        return self.test_value

    def clean_test_field(self):
        """Returns a cleaned value for test_field. """
        value = self.cleaned_data.get('test_field', 'xx ')
        return self.test_func(value)


class OverrideForm(FormOverrideMixIn, Form):
    single_choices = [('A', 'Option A'), ('B', 'Option B'), ('C', 'Option C'), ]
    multi_choices = [('A', 'Include A'), ('B', 'Include B'), ('C', 'Include C'), ]

    first = CharField(initial='first_value')
    second = CharField(initial='second_value')
    generic_field = CharField(initial='original_value')
    large_comment = CharField(initial='initial large comment', widget=Textarea(attrs={"rows": 10, "cols": 40}))
    small_comment = CharField(widget=Textarea(attrs={"rows": 2, "cols": 10}))
    simple_comment = CharField(widget=Textarea())
    hide_field = CharField(widget=HiddenInput(), initial='hide_data')
    bool_field = BooleanField(required=False)  # single checkbox
    single_select = ChoiceField(choices=single_choices)  # default widget select
    multi_select = MultipleChoiceField(choices=multi_choices)  # SelectMultiple
    radio_select = ChoiceField(choices=single_choices, widget=RadioSelect)
    single_check = ChoiceField(choices=single_choices, widget=CheckboxInput)
    multi_check = MultipleChoiceField(choices=multi_choices, widget=CheckboxSelectMultiple)
    email_test = EmailField()  # like CharField, can have: max_length, min_length, and empty_value
    last = CharField(initial='last_value')

    test_condition_response = False

    def condition_alt_test_feature(self):
        """Methods with condition_<label> return Boolean for when to apply alt_field_info[label] attrs.  """
        # logic for determining if the alternative attrs should be applied.
        return self.test_condition_response


class FormFieldsetForm(FormFieldsetMixIn, Form):
    generic_field = CharField()


# # Extended MixIns # #


class ComputedUsernameForm(ComputedUsernameMixIn, UserCreationForm):
    # email = ''
    # username = ''
    # first_name = CharField(_('first name'), max_length=150, blank=True)
    # last_name = CharField(_('last name'), max_length=150, blank=True)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ['first_name', 'last_name', 'username']


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
    expected_form = None
    viewClass = RegisterModelSimpleFlowView(form_class=expected_form)
    user_type = 'anonymous'  # 'superuser' | 'admin' | 'user' | 'inactive' | 'anonymous'


class ModelActivateFlowTests(BaseRegisterTests, TestCase):
    expected_form = None
    viewClass = RegisterModelActivateFlowView(form_class=expected_form)
    user_type = 'anonymous'  # 'superuser' | 'admin' | 'user' | 'inactive' | 'anonymous'


class SimpleFlowTests(BaseRegisterTests, TestCase):
    expected_form = None
    viewClass = RegisterSimpleFlowView(form_class=expected_form)
    user_type = 'anonymous'  # 'superuser' | 'admin' | 'user' | 'inactive' | 'anonymous'


class ModifyUserTests(BaseRegisterTests, TestCase):
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
    expected_form = None
    viewClass = RegisterActivateFlowView(form_class=expected_form)
    user_type = 'anonymous'  # 'superuser' | 'admin' | 'user' | 'inactive' | 'anonymous'
