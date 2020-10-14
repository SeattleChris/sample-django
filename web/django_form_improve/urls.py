from django.urls import path, include
from django.contrib.auth.views import PasswordChangeView
from .views import RegisterSimpleFlowView, RegisterActivateFlowView, ModifyUser

urlpatterns = [
    path('register/signup', RegisterSimpleFlowView.as_view(), name='signup'),  # One-step, customized.
    path('register/initial', RegisterActivateFlowView.as_view(), name='initial_signup'),  # Two-step, customized.
    path('', include('django_registration.backends.one_step.urls')),  # One-step, defaults and/or remaining views.
    # path('', include('django_registration.backends.activate.urls')),  # Two-step, defaults and/or remaining views.
    path('register/update/', ModifyUser.as_view(), name='user_update'),
    path('password/', PasswordChangeView.as_view(template_name='update.html'), name='password'),
]
