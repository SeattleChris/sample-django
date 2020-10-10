from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', home_view, name='home'),

    # path("APPNAME/", include("APPNAME.urls")),
]
