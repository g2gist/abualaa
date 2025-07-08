from django import template
from django.utils.safestring import mark_safe
from decimal import Decimal
from crm.models import CompanySettings

register = template.Library()

@register.simple_tag
def currency_symbol():
    """إرجاع رمز العملة من إعدادات الشركة"""
    try:
        settings = CompanySettings.objects.first()
        if settings:
            return settings.currency_symbol
    except CompanySettings.DoesNotExist:
        pass
    return 'د.ع'  # افتراضي

@register.simple_tag
def currency_name():
    """إرجاع اسم العملة من إعدادات الشركة"""
    try:
        settings = CompanySettings.objects.first()
        if settings:
            return settings.currency_name
    except CompanySettings.DoesNotExist:
        pass
    return 'دينار عراقي'  # افتراضي

@register.filter
def currency(value, currency_type=None):
    """فلتر لتنسيق المبلغ بالعملة المحددة"""
    if value is None:
        value = 0

    try:
        # تحويل القيمة إلى رقم
        if isinstance(value, str):
            value = Decimal(value)
        elif not isinstance(value, Decimal):
            value = Decimal(str(value))

        # الحصول على إعدادات العملة
        if currency_type is None:
            try:
                settings = CompanySettings.objects.first()
                if settings and settings.currency == 'USD':
                    currency_type = 'USD'
                else:
                    currency_type = 'IQD'
            except:
                currency_type = 'IQD'

        # تنسيق الرقم حسب نوع العملة
        if currency_type == 'USD':
            formatted_value = "{:,.2f}".format(value)
            return f"${formatted_value}"
        else:  # IQD
            formatted_value = "{:,.0f}".format(value)
            return f"{formatted_value} د.ع"

    except (ValueError, TypeError):
        if currency_type == 'USD':
            return "$0.00"
        else:
            return "0 د.ع"

@register.filter
def currency_usd(value):
    """تنسيق المبلغ بالدولار"""
    return currency(value, 'USD')

@register.filter
def currency_iqd(value):
    """تنسيق المبلغ بالدينار العراقي"""
    return currency(value, 'IQD')
