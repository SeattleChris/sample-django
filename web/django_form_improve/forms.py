from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
# from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .mixins import AddressMixIn, AddressUsernameMixIn


def default_names():
    constructor_names = ['first_name', 'last_name']
    address_names = [
        'billing_address_1', 'billing_address_2',
        'billing_city', 'billing_country_area', 'billing_postcode',
        'billing_country_code',
        ]
    return constructor_names, address_names


def _get_available_names(model, initial_list):
    found, rejected = [], []
    for name in initial_list:
        if hasattr(model, name):
            found.append(name)
        else:
            rejected.append(name)
    # return [name for name in initial_list if hasattr(model, name)]
    return found, rejected


def make_names(model, constructors, early, setting, extras, address, profile=None):
    constructor_names, address_names = default_names()
    initial = constructors if isinstance(constructors, (tuple, list)) else constructor_names
    if isinstance(early, (tuple, list)):
        initial = [*initial, *early]
    initial = _get_available_names(model, initial)
    settings = [setting] if setting and isinstance((setting, str)) else setting
    settings = [] if not settings else _get_available_names(model, settings)
    settings.extend(("password1", "password2", ))
    if extras:
        extras = _get_available_names(model, extras)
        settings.extend(extras)
    address = address_names if address is None else address
    if profile:
        address = []
        profile_address = _get_available_names(profile, address)
        # TODO: Handle creating fields from profile model, and setup to be saved.
        print(f"Model: {profile} \n Address field names: {profile_address} ")
    else:
        address = _get_available_names(model, address)
    return [*initial, model.get_email_field_name(), model.USERNAME_FIELD, *settings, *address]


class RegisterModelForm(AddressUsernameMixIn, forms.ModelForm):
    """User creation form with configurable computed username. Includes foreign vs local country address feature.  """

    class Meta(forms.ModelForm.Meta):
        model = None
        constructor_names = None  # set to a list of model field names, otherwise assumes ['first_name', 'last_name']
        early_names = []  # User model fields that should have a form input BEFORE email, username, password.
        username_flag_name = 'username_not_email'  # set to None if the User model does not have this field type.
        extra_names = []  # User model fields that should have a form input AFTER email, username, password.
        address_names = None  # Assumes defaults or the provided list of model fields. Set to [] for no address.
        address_on_profile_name = None  # set to related name for a profile model if it stores the address fields.
        fields = make_names(model, constructor_names, early_names, username_flag_name,
                            extra_names, address_names, address_on_profile_name)
        help_texts = {
            'name_for_email': _("Used for confirmation and typically for login"),
            'name_for_user': _("Without a unique email, a username is needed. Use suggested or create one. "),
        }

    error_css_class = "error"
    required_css_class = "required"
    # computed_fields = []  # The computed fields needed for username and address will be added.


class RegisterUserForm(AddressUsernameMixIn, UserCreationForm):
    """User creation form with configurable computed username. Includes foreign vs local country address feature.  """

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        constructor_names = None  # set to a list of model field names, otherwise assumes ['first_name', 'last_name']
        early_names = []  # User model fields that should have a form input BEFORE email, username, password.
        username_flag_name = 'username_not_email'  # set to None if the User model does not have this field type.
        extra_names = []  # User model fields that should have a form input AFTER email, username, password.
        address_names = None  # Assumes defaults or the provided list of model fields. Set to [] for no address.
        address_on_profile_name = None  # set to related name for a profile model if it stores the address fields.
        fields = make_names(model, constructor_names, early_names, username_flag_name,
                            extra_names, address_names, address_on_profile_name)
        help_texts = {
            model.get_email_field_name(): _("Used for confirmation and typically for login"),
            model.USERNAME_FIELD: _("Without a unique email, a username is needed. Use suggested or create one. "),
        }

    error_css_class = "error"
    required_css_class = "required"
    # computed_fields = []  # The computed fields needed for username and address will be added.


class RegisterChangeForm(AddressMixIn, UserChangeForm):

    class Meta(UserChangeForm.Meta):
        model = get_user_model()
        fields = (
            'first_name', 'last_name',
            'email',
            'billing_address_1',
            'billing_address_2',
            'billing_city', 'billing_country_area', 'billing_postcode',
            'billing_country_code',
            )
