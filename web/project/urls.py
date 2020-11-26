from django.contrib import admin
from django.urls import path, include
from .views import home_view, NamedView, ProfileView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', home_view, name='home'),
    path('named', NamedView.as_view(), name='named_path'),
    path('user/', ProfileView.as_view(), name='profile_page'),
    path("improved/", include("django_improve_form.urls")),
    # path("APPNAME/", include("APPNAME.urls")),
]
