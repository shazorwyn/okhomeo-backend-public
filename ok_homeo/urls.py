"""
URL configuration for ok_homeo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from core.views import (
    CookieTokenObtainPairView,
    CookieTokenRefreshView,
    LogoutView,
    ContactView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path(
        "auth/login/",
        CookieTokenObtainPairView.as_view(),
        name="jwt-create",
    ),
    path(
        "auth/refresh/",
        CookieTokenRefreshView.as_view(),
        name="token_refresh",
    ),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.jwt")),
    path("contact/", ContactView.as_view(), name="contact"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
