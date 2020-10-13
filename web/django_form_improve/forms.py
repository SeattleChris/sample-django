# from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
# from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .mixins import AddressMixIn, AddressUsernameMixIn


class UserRegisterForm(AddressUsernameMixIn, UserCreationForm):
    """Form for new user account creation. Requires double entry of password, validates unique username. """

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = [
            model.USERNAME_FIELD,
            model.get_email_field_name(),
            "password1",
            "password2",
        ]
        help_texts = {
            model.USERNAME_FIELD: _("Without a unique email, a username is needed. Use suggested or create one. "),
            model.get_email_field_name(): _("Used for confirmation and typically for login"),
        }

    error_css_class = "error"
    required_css_class = "required"
    # computed_fields = []  # The computed fields needed for username and address will be added.


class CustomRegistrationForm(UserRegisterForm):

    constructor_fields = ('first_name', 'last_name', )
    USERNAME_FLAG_FIELD = 'username_not_email'

    class Meta(UserRegisterForm.Meta):
        fields = UserRegisterForm.Meta.fields
        fields.extend(('first_name', 'last_name', 'username_not_email'))

    def __init__(self, *args, **kwargs):
        print("================================== CustomRegistrationForm.__init__ =====================")
        super().__init__(*args, **kwargs)
        # TODO: If using RegistrationForm init, then much, but not all, of attach_critical_validators is duplicate code.
        print("--------------------- FINISH CustomRegistrationForm.__init__ --------------------")


class CustomUserChangeForm(AddressMixIn, UserChangeForm):

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
