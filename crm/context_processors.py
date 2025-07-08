"""
Context processors لجعل البيانات متاحة في جميع القوالب
"""
from .models import CompanySettings


def company_settings(request):
    """إضافة إعدادات الشركة إلى جميع القوالب"""
    try:
        settings = CompanySettings.objects.first()
    except CompanySettings.DoesNotExist:
        settings = None
    
    return {
        'company_settings': settings
    }


def developer_info(request):
    """إضافة معلومات المطور إلى جميع القوالب"""
    return {
        'developer_name': 'خالد شجاع',
        'developer_year': '2025',
        'app_name': 'نظام إدارة العملاء والديون',
        'app_version': '1.0.0'
    }
