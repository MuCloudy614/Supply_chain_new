# E:\pycharm_pro_project\supply_chain\supply_chain\context_processors.py

from django.conf import settings

def site_info(request):
    """添加自定义全局上下文"""
    return {
        'SITE_TITLE': settings.SITE_TITLE,
        'VERSION': settings.VERSION,
        'YEAR': settings.YEAR if hasattr(settings, 'YEAR') else '2023',
    }