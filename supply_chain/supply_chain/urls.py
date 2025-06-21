# E:\pycharm_pro_project\supply_chain\supply_chain\urls.py

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