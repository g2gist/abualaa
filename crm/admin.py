from django.contrib import admin
from .models import Customer, Debt, Payment, Invoice, CompanySettings


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'phone', 'email', 'page_number', 'total_debt', 'remaining_debt', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'phone', 'email', 'page_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Debt)
class DebtAdmin(admin.ModelAdmin):
    list_display = ['customer', 'amount', 'remaining_amount', 'due_date', 'status', 'created_date']
    list_filter = ['status', 'due_date', 'created_date']
    search_fields = ['customer__name', 'description']
    readonly_fields = ['created_date']

    def save_model(self, request, obj, form, change):
        if not change:  # إذا كان إنشاء جديد
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['debt', 'amount', 'payment_method', 'payment_date', 'received_by']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['debt__customer__name']
    readonly_fields = ['payment_date']

    def save_model(self, request, obj, form, change):
        if not change:  # إذا كان إنشاء جديد
            obj.received_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'debt', 'status', 'created_date']
    list_filter = ['status', 'created_date']
    search_fields = ['invoice_number', 'debt__customer__name']
    readonly_fields = ['created_date', 'invoice_number']


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'phone', 'email']

    def has_add_permission(self, request):
        # السماح بإضافة إعداد واحد فقط
        return not CompanySettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # منع حذف الإعدادات
        return False
