from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Документация, сгенерированная django.contrib.admindocs
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    path("admin/", admin.site.urls),
    path("api/", include("tours.urls")),
]
