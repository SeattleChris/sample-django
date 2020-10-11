from django.contrib import admin
from django.urls import path, include
from .views import home_view, NamedView

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', home_view, name='home'),
    path('named', NamedView.as_view(), name='named_path'),
    # path("APPNAME/", include("APPNAME.urls")),
]
