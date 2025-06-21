from django.contrib import admin
from django.urls import path
from django.views.generic import RedirectView
from django.contrib.auth.views import LoginView, LogoutView
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),

    # 重定向根路径到登录页面
    path('', RedirectView.as_view(pattern_name='login', permanent=False)),

    # 自定义登录界面
    path('accounts/login/',
         LoginView.as_view(
             template_name='admin/login_custom.html',
             extra_context={'site_title': settings.SITE_TITLE}
         ),
         name='login'),

    # 登出功能
    path('accounts/logout/',
         LogoutView.as_view(
             template_name='admin/logout_custom.html'
         ),
         name='logout'),
]