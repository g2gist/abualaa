from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.utils import timezone
from decimal import Decimal


class Customer(models.Model):
    """نموذج العميل"""
    name = models.CharField(max_length=100, verbose_name="الاسم")
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="رقم الهاتف يجب أن يكون بالصيغة: '+999999999'. حتى 15 رقم مسموح."
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        verbose_name="رقم الجوال"
    )
    email = models.EmailField(blank=True, null=True, verbose_name="البريد الإلكتروني")
    address = models.TextField(blank=True, null=True, verbose_name="العنوان")
    page_number = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        verbose_name="رقم الصفحة الورقية"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="تاريخ التحديث")

    class Meta:
        verbose_name = "عميل"
        verbose_name_plural = "العملاء"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def total_debt(self):
        """إجمالي الديون"""
        return self.debts.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

    @property
    def total_paid(self):
        """إجمالي المدفوع"""
        return sum(debt.total_paid for debt in self.debts.all())

    @property
    def remaining_debt(self):
        """المبلغ المتبقي"""
        return self.total_debt - self.total_paid


class Debt(models.Model):
    """نموذج الدين"""
    STATUS_CHOICES = [
        ('active', 'نشط'),
        ('paid', 'مدفوع'),
        ('overdue', 'متأخر'),
        ('cancelled', 'ملغي'),
    ]

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='debts',
        verbose_name="العميل"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="المبلغ"
    )
    description = models.TextField(verbose_name="الوصف")
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    due_date = models.DateField(verbose_name="تاريخ الاستحقاق")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="الحالة"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="أنشئ بواسطة"
    )

    class Meta:
        verbose_name = "دين"
        verbose_name_plural = "الديون"
        ordering = ['-created_date']

    def __str__(self):
        return f"{self.customer.name} - {self.amount}"

    @property
    def total_paid(self):
        """إجمالي المدفوع لهذا الدين"""
        return self.payments.aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')

    @property
    def remaining_amount(self):
        """المبلغ المتبقي"""
        return self.amount - self.total_paid

    @property
    def is_overdue(self):
        """هل الدين متأخر؟"""
        if isinstance(self.due_date, str):
            from datetime import datetime
            self.due_date = datetime.strptime(self.due_date, '%Y-%m-%d').date()
        return self.due_date < timezone.now().date() and self.status == 'active'

    @property
    def is_due_soon(self):
        """هل الدين مستحق خلال 7 أيام؟"""
        if isinstance(self.due_date, str):
            from datetime import datetime
            self.due_date = datetime.strptime(self.due_date, '%Y-%m-%d').date()
        days_until_due = (self.due_date - timezone.now().date()).days
        return 0 <= days_until_due <= 7 and self.status == 'active'

    def save(self, *args, **kwargs):
        """تحديث الحالة تلقائياً"""
        # حفظ أولاً للحصول على primary key
        super().save(*args, **kwargs)

        # ثم تحديث الحالة
        if self.pk:
            if self.remaining_amount <= 0:
                self.status = 'paid'
            elif self.is_overdue:
                self.status = 'overdue'

            # حفظ مرة أخرى إذا تغيرت الحالة
            if self.status != self._state.fields_cache.get('status'):
                super().save(update_fields=['status'])


class Payment(models.Model):
    """نموذج الدفعة"""
    PAYMENT_METHODS = [
        ('cash', 'نقداً'),
        ('bank_transfer', 'تحويل بنكي'),
        ('check', 'شيك'),
        ('credit_card', 'بطاقة ائتمان'),
        ('other', 'أخرى'),
    ]

    debt = models.ForeignKey(
        Debt,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name="الدين"
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="المبلغ"
    )
    payment_date = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الدفع")
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default='cash',
        verbose_name="طريقة الدفع"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    received_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="استلم بواسطة"
    )

    class Meta:
        verbose_name = "دفعة"
        verbose_name_plural = "الدفعات"
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.debt.customer.name} - {self.amount} - {self.payment_date.strftime('%Y-%m-%d')}"

    def save(self, *args, **kwargs):
        """تحديث حالة الدين بعد الدفع"""
        super().save(*args, **kwargs)
        self.debt.save()  # لتحديث الحالة


class Invoice(models.Model):
    """نموذج الفاتورة"""
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('sent', 'مرسلة'),
        ('paid', 'مدفوعة'),
        ('cancelled', 'ملغية'),
    ]

    debt = models.OneToOneField(
        Debt,
        on_delete=models.CASCADE,
        related_name='invoice',
        verbose_name="الدين"
    )
    invoice_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="رقم الفاتورة"
    )
    created_date = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="الحالة"
    )
    pdf_file = models.FileField(
        upload_to='invoices/',
        blank=True,
        null=True,
        verbose_name="ملف PDF"
    )

    class Meta:
        verbose_name = "فاتورة"
        verbose_name_plural = "الفواتير"
        ordering = ['-created_date']

    def __str__(self):
        return f"فاتورة {self.invoice_number} - {self.debt.customer.name}"

    def save(self, *args, **kwargs):
        """إنشاء رقم فاتورة تلقائي"""
        if not self.invoice_number:
            try:
                # البحث عن آخر فاتورة
                last_invoice = Invoice.objects.order_by('-id').first()
                if last_invoice and last_invoice.invoice_number:
                    try:
                        # استخراج الرقم من آخر فاتورة
                        last_number = int(last_invoice.invoice_number.split('-')[-1])
                        self.invoice_number = f"INV-{last_number + 1:06d}"
                    except (ValueError, IndexError):
                        # إذا فشل في استخراج الرقم، ابدأ من جديد
                        self.invoice_number = f"INV-{Invoice.objects.count() + 1:06d}"
                else:
                    self.invoice_number = "INV-000001"
            except Exception:
                # في حالة أي خطأ، استخدم timestamp
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                self.invoice_number = f"INV-{timestamp}"

        super().save(*args, **kwargs)


class CompanySettings(models.Model):
    """إعدادات الشركة"""
    CURRENCY_CHOICES = [
        ('IQD', 'دينار عراقي'),
        ('USD', 'دولار أمريكي'),
    ]

    company_name = models.CharField(max_length=200, verbose_name="اسم الشركة")
    phone = models.CharField(max_length=20, verbose_name="الهاتف")
    email = models.EmailField(verbose_name="البريد الإلكتروني")
    address = models.TextField(verbose_name="العنوان")
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default="IQD",
        verbose_name="العملة"
    )
    logo = models.ImageField(upload_to='company/', blank=True, null=True, verbose_name="الشعار")
    invoice_terms = models.TextField(
        blank=True,
        null=True,
        verbose_name="شروط الفاتورة"
    )

    class Meta:
        verbose_name = "إعدادات الشركة"
        verbose_name_plural = "إعدادات الشركة"

    def __str__(self):
        return self.company_name

    @property
    def currency_symbol(self):
        """رمز العملة"""
        currency_symbols = {
            'IQD': 'د.ع',
            'USD': '$',
        }
        return currency_symbols.get(self.currency, self.currency)

    @property
    def currency_name(self):
        """اسم العملة"""
        return dict(self.CURRENCY_CHOICES).get(self.currency, self.currency)

    def save(self, *args, **kwargs):
        """التأكد من وجود إعداد واحد فقط"""
        # السماح بالتحديث للإعداد الموجود
        if not self.pk and CompanySettings.objects.exists():
            # تحديث الإعداد الموجود بدلاً من إنشاء جديد
            existing = CompanySettings.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)
