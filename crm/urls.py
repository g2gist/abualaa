from django.urls import path
from . import views

urlpatterns = [
    # المصادقة
    path('login/', views.custom_login, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # لوحة التحكم
    path('', views.dashboard, name='dashboard'),

    # العملاء
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/add/', views.customer_create, name='customer_create'),
    path('customers/import-excel/', views.customer_import_excel, name='customer_import_excel'),
    path('customers/download-template/', views.download_excel_template, name='download_excel_template'),

    # التقارير
    path('reports/', views.reports_dashboard, name='reports_dashboard'),
    path('reports/export/', views.reports_export, name='reports_export'),

    # الإعدادات
    path('settings/currency/', views.currency_settings, name='currency_settings'),
    path('settings/logo/', views.logo_settings, name='logo_settings'),
    path('settings/change-password/', views.change_password, name='change_password'),

    # النسخ الاحتياطي
    path('backup/', views.backup_dashboard, name='backup_dashboard'),
    path('backup/create/', views.create_backup, name='create_backup'),
    path('backup/download/', views.download_backup, name='download_backup'),
    path('backup/settings/', views.backup_settings, name='backup_settings'),
    path('customers/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    path('customers/<int:customer_id>/edit/', views.customer_edit, name='customer_edit'),
    path('customers/<int:customer_id>/delete/', views.customer_delete, name='customer_delete'),

    # الديون
    path('debts/', views.debt_list, name='debt_list'),
    path('debts/add/', views.debt_create, name='debt_create'),
    path('debts/add/<int:customer_id>/', views.debt_create, name='debt_create_for_customer'),
    path('debts/<int:debt_id>/', views.debt_detail, name='debt_detail'),

    # الدفعات
    path('payments/', views.payment_list, name='payment_list'),
    path('debts/<int:debt_id>/pay/', views.payment_create, name='payment_create'),

    # الفواتير
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/<int:invoice_id>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:invoice_id>/pdf/', views.invoice_pdf, name='invoice_pdf'),
]
