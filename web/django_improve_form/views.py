from django.urls import reverse_lazy
from django.views import generic
from django.views.decorators.csrf import csrf_protect
from django.utils.decorators import method_decorator
from django.utils.translation import gettext as _
# from django.contrib.auth import get_user_model
from django_registration.backends.one_step.views import RegistrationView as RegistrationViewOneStep
from django_registration.backends.activation.views import RegistrationView as RegistrationViewTwoStep
from .forms import RegisterUserForm, RegisterModelForm, RegisterChangeForm
from pprint import pprint  # TODO: Remove after debug

# Create your views here.


@method_decorator(csrf_protect, name='dispatch')
class RegisterSimpleFlowView(RegistrationViewOneStep):
    form_class = RegisterUserForm
    form_as_type = None
    success_url = reverse_lazy('profile_page')
    # template_name = 'improve_form/signup.html'
    template_name = 'django_registration/registration_form.html'
    default_context = {
        'improve_form_title': _('New User Sign Up'),
        'improve_form_container_class': 'registration-form-container',
        'form_heading': _('Sign Up Now!'),
        'form_preamble': '',
        'form_button_text': _('Sign Up'),
        }

    def get_context_data(self, **kwargs):
        kwargs['form_as_type'] = getattr(self, 'form_as_type', None)
        extra_context = getattr(self, 'default_context', {})
        extra_context.update(getattr(self, 'extra_context', {}) or {})
        self.extra_context = extra_context  # Allowing user defined context to override default_context
        context = super().get_context_data(**kwargs)
        return context

    def register(self, form):
        print("===================== RegisterSimpleFlowView.register ============================")
        pprint(form)
        print("----------------------------------------------------------------------------------")
        pprint(self)
        return super().register(form)


@method_decorator(csrf_protect, name='dispatch')
class RegisterActivateFlowView(RegistrationViewTwoStep):
    form_class = RegisterUserForm
    form_as_type = None
    success_url = reverse_lazy('profile_page')
    # template_name = 'improve_form/signup.html'
    template_name = 'django_registration/registration_form.html'
    default_context = {
        'improve_form_title': _('New User Sign Up'),
        'improve_form_container_class': 'registration-form-container',
        'form_heading': _('Sign Up Now!'),
        'form_preamble': '',
        'form_button_text': _('Sign Up'),
        }

    def get_context_data(self, **kwargs):
        kwargs['form_as_type'] = getattr(self, 'form_as_type', None)
        extra_context = getattr(self, 'default_context', {})
        extra_context.update(getattr(self, 'extra_context', {}) or {})
        self.extra_context = extra_context  # Allowing user defined context to override default_context
        context = super().get_context_data(**kwargs)
        return context

    def register(self, form):
        print("===================== RegisterActivateFlowView.register ============================")
        pprint(form)
        print("----------------------------------------------------------------------------------")
        pprint(self)
        return super().register(form)


@method_decorator(csrf_protect, name='dispatch')
class RegisterModelSimpleFlowView(RegistrationViewOneStep):
    model = None
    form_class = RegisterModelForm
    template_name = None

@method_decorator(csrf_protect, name='dispatch')
class RegisterModelActivateFlowView(RegistrationViewTwoStep):
    model = None
    form_class = RegisterModelForm
    template_name = None


@method_decorator(csrf_protect, name='dispatch')
class ModifyUser(generic.UpdateView):
    # model = get_user_model()
    form_class = RegisterChangeForm
    success_url = reverse_lazy('profile_page')
    template_name = 'update.html'

    def get_object(self, queryset=None):
        return self.request.user
