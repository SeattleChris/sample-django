from django.urls import path, include
from django.contrib.auth.views import PasswordChangeView
from .views import CustomRegistrationView, Modify  # , SignUp,

urlpatterns = [
    path('register/', CustomRegistrationView.as_view(), name='signup'),  # One-step, customized.
    path('', include('django_registration.backends.one_step.urls')),  # One-step, defaults and/or remaining views.
    path('update/', Modify.as_view(), name='user_update'),
    path('password/', PasswordChangeView.as_view(template_name='update.html'), name='password'),
]
