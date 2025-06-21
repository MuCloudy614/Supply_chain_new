"""
URL configuration for supply_chain project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.views.generic import RedirectView
from django.contrib.auth.views import LoginView, LogoutView
from django.conf import settings

# 项目标题设置（在settings.py中定义）
if not hasattr(settings, 'SITE_TITLE'):
    settings.SITE_TITLE = '供应链管理系统'

urlpatterns = [
    # Django管理后台
    path('admin/', admin.site.urls),

    # 重定向根路径到仪表盘
    path('', RedirectView.as_view(url='/inventory/dashboard/', permanent=True)),

    # 包含inventory应用的URL
    path('inventory/', include('inventory.urls')),

    # 自定义登录登出视图
    path('accounts/login/',
         LoginView.as_view(
             template_name='admin/login_custom.html',
             extra_context={'site_title': settings.SITE_TITLE}
         ),
         name='login'
         ),
    path('accounts/logout/',
         LogoutView.as_view(template_name='admin/logout_custom.html'),
         name='logout'
         ),
]