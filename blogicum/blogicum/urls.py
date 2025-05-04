"""blogicum URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path, include
from users.views import SignUp, SignIn, LoggedOut
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.conf import settings

handler404 = 'pages.views.page_404'
handler403 = 'pages.views.page_403'
handler500 = 'pages.views.page_500'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('blog.urls', namespace='blog')),
    path('pages/', include('pages.urls', namespace='pages')),
    path(
        'auth/registration/',
        SignUp.as_view(),
        name='registration',
    ),
    path('auth/login/', SignIn.as_view(), name='login'),
    path('auth/logout/', LoggedOut.as_view(), name='logout'),
    path(
        'auth/logout/confirm/',
        TemplateView.as_view(template_name='registration/logged_out.html'),
        name='logout_confirm'
    ),
    path('auth/', include('django.contrib.auth.urls')),
] + static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)
