"""api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
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
from django.http.response import HttpResponse

def load_tester(request):
    content = 'loaderio-8724c88e2ab3c7a98bf27e9e97e38aa4'
    return HttpResponse(content, content_type='text/plain')

urlpatterns = [
    path('users/', include('users.urls')),
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('loaderio-8724c88e2ab3c7a98bf27e9e97e38aa4/',load_tester)
]

