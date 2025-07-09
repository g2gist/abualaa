from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import json

from .models import Customer, Debt, Payment, Invoice, CompanySettings


def is_manager(user):
    """التحقق من كون المستخدم مدير"""
    return user.is_superuser or user.groups.filter(name='المدراء').exists()


def is_employee(user):
    """التحقق من كون المستخدم موظف"""
    return user.groups.filter(name='الموظفين').exists() or is_manager(user)


def login_view(request):
    """صفحة تسجيل الدخول"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'مرحباً بك {user.first_name or user.username}')
            return redirect('dashboard')
        else:
            messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')

    return render(request, 'auth/login.html')


def logout_view(request):
    """تسجيل الخروج"""
    logout(request)
    messages.success(request, 'تم تسجيل الخروج بنجاح')
    return redirect('login')


@login_required
@user_passes_test(is_employee)
def dashboard(request):
    """لوحة التحكم الرئيسية"""
    # الإحصائيات العامة
    total_customers = Customer.objects.count()
    total_debts = Debt.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    total_paid = Payment.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    remaining_debt = total_debts - total_paid

    # الديون المتأخرة
    overdue_debts = Debt.objects.filter(
        due_date__lt=timezone.now().date(),
        status='active'
    ).count()

    # الديون المستحقة خلال 7 أيام
    due_soon = Debt.objects.filter(
        due_date__gte=timezone.now().date(),
        due_date__lte=timezone.now().date() + timedelta(days=7),
        status='active'
    ).count()

    # آخر الديون المضافة
    recent_debts = Debt.objects.select_related('customer').order_by('-created_date')[:5]

    # آخر الدفعات
    recent_payments = Payment.objects.select_related('debt__customer').order_by('-payment_date')[:5]

    # بيانات الرسم البياني الشهري
    monthly_data = []
    for i in range(6):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        month_debts = Debt.objects.filter(
            created_date__gte=month_start,
            created_date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0

        month_payments = Payment.objects.filter(
            payment_date__gte=month_start,
            payment_date__lte=month_end
        ).aggregate(total=Sum('amount'))['total'] or 0

        monthly_data.append({
            'month': month_start.strftime('%Y-%m'),
            'debts': float(month_debts),
            'payments': float(month_payments)
        })

    monthly_data.reverse()

    context = {
        'total_customers': total_customers,
        'total_debts': total_debts,
        'total_paid': total_paid,
        'remaining_debt': remaining_debt,
        'overdue_debts': overdue_debts,
        'due_soon': due_soon,
        'recent_debts': recent_debts,
        'recent_payments': recent_payments,
        'monthly_data': json.dumps(monthly_data),
    }

    return render(request, 'dashboard.html', context)


# ==================== إدارة العملاء ====================

@login_required
@user_passes_test(is_employee)
def customer_list(request):
    """قائمة العملاء"""
    search_query = request.GET.get('search', '')
    customers = Customer.objects.all()

    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query)
        )

    # ترقيم الصفحات
    paginator = Paginator(customers, 10)
    page_number = request.GET.get('page')
    customers = paginator.get_page(page_number)

    context = {
        'customers': customers,
        'search_query': search_query,
    }
    return render(request, 'customers/list.html', context)


@login_required
@user_passes_test(is_employee)
def customer_detail(request, customer_id):
    """تفاصيل العميل"""
    customer = get_object_or_404(Customer, id=customer_id)
    debts = customer.debts.all().order_by('-created_date')

    context = {
        'customer': customer,
        'debts': debts,
    }
    return render(request, 'customers/detail.html', context)


@login_required
@user_passes_test(is_employee)
def customer_create(request):
    """إضافة عميل جديد"""
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address = request.POST.get('address')
        page_number = request.POST.get('page_number')

        # التحقق من البيانات
        if not name or not phone:
            messages.error(request, 'الاسم ورقم الهاتف مطلوبان')
            return render(request, 'customers/form.html')

        # التحقق من عدم تكرار رقم الهاتف
        if Customer.objects.filter(phone=phone).exists():
            messages.error(request, 'رقم الهاتف مستخدم من قبل')
            return render(request, 'customers/form.html')

        customer = Customer.objects.create(
            name=name,
            phone=phone,
            email=email or None,
            address=address or None,
            page_number=page_number or None
        )

        messages.success(request, f'تم إضافة العميل {customer.name} بنجاح')
        return redirect('customer_detail', customer_id=customer.id)

    return render(request, 'customers/form.html')


@login_required
@user_passes_test(is_employee)
def customer_edit(request, customer_id):
    """تعديل بيانات العميل"""
    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address = request.POST.get('address')
        page_number = request.POST.get('page_number')

        # التحقق من البيانات
        if not name or not phone:
            messages.error(request, 'الاسم ورقم الهاتف مطلوبان')
            return render(request, 'customers/form.html', {'customer': customer})

        # التحقق من عدم تكرار رقم الهاتف (باستثناء العميل الحالي)
        if Customer.objects.filter(phone=phone).exclude(id=customer.id).exists():
            messages.error(request, 'رقم الهاتف مستخدم من قبل')
            return render(request, 'customers/form.html', {'customer': customer})

        customer.name = name
        customer.phone = phone
        customer.email = email or None
        customer.address = address or None
        customer.page_number = page_number or None
        customer.save()

        messages.success(request, f'تم تحديث بيانات العميل {customer.name} بنجاح')
        return redirect('customer_detail', customer_id=customer.id)

    return render(request, 'customers/form.html', {'customer': customer})


@login_required
@user_passes_test(is_manager)
def customer_delete(request, customer_id):
    """حذف العميل (للمدراء فقط)"""
    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == 'POST':
        customer_name = customer.name
        customer.delete()
        messages.success(request, f'تم حذف العميل {customer_name} بنجاح')
        return redirect('customer_list')

    return render(request, 'customers/delete.html', {'customer': customer})


# ==================== إدارة الديون ====================

@login_required
@user_passes_test(is_employee)
def debt_list(request):
    """قائمة الديون"""
    status_filter = request.GET.get('status', '')
    customer_filter = request.GET.get('customer', '')
    search_query = request.GET.get('search', '')

    debts = Debt.objects.select_related('customer').all()

    if status_filter:
        debts = debts.filter(status=status_filter)

    if customer_filter:
        debts = debts.filter(customer_id=customer_filter)

    if search_query:
        debts = debts.filter(
            Q(customer__name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # ترقيم الصفحات
    paginator = Paginator(debts, 15)
    page_number = request.GET.get('page')
    debts = paginator.get_page(page_number)

    # قائمة العملاء للفلترة
    customers = Customer.objects.all().order_by('name')

    context = {
        'debts': debts,
        'customers': customers,
        'status_filter': status_filter,
        'customer_filter': customer_filter,
        'search_query': search_query,
        'status_choices': Debt.STATUS_CHOICES,
    }
    return render(request, 'debts/list.html', context)


@login_required
@user_passes_test(is_employee)
def debt_detail(request, debt_id):
    """تفاصيل الدين"""
    debt = get_object_or_404(Debt, id=debt_id)
    payments = debt.payments.all().order_by('-payment_date')

    context = {
        'debt': debt,
        'payments': payments,
    }
    return render(request, 'debts/detail.html', context)


@login_required
@user_passes_test(is_employee)
def debt_create(request, customer_id=None):
    """إضافة دين جديد"""
    customer = None
    if customer_id:
        customer = get_object_or_404(Customer, id=customer_id)

    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        amount = request.POST.get('amount')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')

        # التحقق من البيانات
        if not all([customer_id, amount, description, due_date]):
            messages.error(request, 'جميع الحقول مطلوبة')
            return render(request, 'debts/form.html', {
                'customers': Customer.objects.all().order_by('name'),
                'selected_customer': customer
            })

        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError("المبلغ يجب أن يكون أكبر من صفر")
        except (ValueError, TypeError):
            messages.error(request, 'المبلغ غير صحيح')
            return render(request, 'debts/form.html', {
                'customers': Customer.objects.all().order_by('name'),
                'selected_customer': customer
            })

        debt = Debt.objects.create(
            customer_id=customer_id,
            amount=amount,
            description=description,
            due_date=due_date,
            created_by=request.user
        )

        # إنشاء فاتورة تلقائياً
        Invoice.objects.create(debt=debt)

        messages.success(request, f'تم إضافة الدين بنجاح للعميل {debt.customer.name}')
        return redirect('debt_detail', debt_id=debt.id)

    customers = Customer.objects.all().order_by('name')
    context = {
        'customers': customers,
        'selected_customer': customer,
    }
    return render(request, 'debts/form.html', context)


# ==================== إدارة الدفعات ====================

@login_required
@user_passes_test(is_employee)
def payment_create(request, debt_id):
    """تسجيل دفعة جديدة"""
    debt = get_object_or_404(Debt, id=debt_id)

    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        notes = request.POST.get('notes')

        # التحقق من البيانات
        if not amount or not payment_method:
            messages.error(request, 'المبلغ وطريقة الدفع مطلوبان')
            return render(request, 'payments/form.html', {
                'debt': debt,
                'payment_methods': Payment.PAYMENT_METHODS
            })

        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError("المبلغ يجب أن يكون أكبر من صفر")
            if amount > debt.remaining_amount:
                raise ValueError("المبلغ أكبر من المبلغ المتبقي")
        except (ValueError, TypeError) as e:
            messages.error(request, f'المبلغ غير صحيح: {str(e)}')
            return render(request, 'payments/form.html', {
                'debt': debt,
                'payment_methods': Payment.PAYMENT_METHODS
            })

        payment = Payment.objects.create(
            debt=debt,
            amount=amount,
            payment_method=payment_method,
            notes=notes or None,
            received_by=request.user
        )

        messages.success(request, f'تم تسجيل الدفعة بنجاح بمبلغ {payment.amount} ريال')
        return redirect('debt_detail', debt_id=debt.id)

    context = {
        'debt': debt,
        'payment_methods': Payment.PAYMENT_METHODS,
    }
    return render(request, 'payments/form.html', context)


@login_required
@user_passes_test(is_employee)
def payment_list(request):
    """قائمة الدفعات"""
    customer_filter = request.GET.get('customer', '')
    method_filter = request.GET.get('method', '')
    search_query = request.GET.get('search', '')

    payments = Payment.objects.select_related('debt__customer', 'received_by').all()

    if customer_filter:
        payments = payments.filter(debt__customer_id=customer_filter)

    if method_filter:
        payments = payments.filter(payment_method=method_filter)

    if search_query:
        payments = payments.filter(
            Q(debt__customer__name__icontains=search_query) |
            Q(notes__icontains=search_query)
        )

    # ترقيم الصفحات
    paginator = Paginator(payments, 15)
    page_number = request.GET.get('page')
    payments = paginator.get_page(page_number)

    # قائمة العملاء للفلترة
    customers = Customer.objects.all().order_by('name')

    context = {
        'payments': payments,
        'customers': customers,
        'customer_filter': customer_filter,
        'method_filter': method_filter,
        'search_query': search_query,
        'payment_methods': Payment.PAYMENT_METHODS,
    }
    return render(request, 'payments/list.html', context)


# ==================== إدارة الفواتير ====================

@login_required
@user_passes_test(is_employee)
def invoice_list(request):
    """قائمة الفواتير"""
    status_filter = request.GET.get('status', '')
    customer_filter = request.GET.get('customer', '')
    search_query = request.GET.get('search', '')

    invoices = Invoice.objects.select_related('debt__customer').all()

    if status_filter:
        invoices = invoices.filter(status=status_filter)

    if customer_filter:
        invoices = invoices.filter(debt__customer_id=customer_filter)

    if search_query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=search_query) |
            Q(debt__customer__name__icontains=search_query)
        )

    # ترقيم الصفحات
    paginator = Paginator(invoices, 15)
    page_number = request.GET.get('page')
    invoices = paginator.get_page(page_number)

    # قائمة العملاء للفلترة
    customers = Customer.objects.all().order_by('name')

    context = {
        'invoices': invoices,
        'customers': customers,
        'status_filter': status_filter,
        'customer_filter': customer_filter,
        'search_query': search_query,
        'status_choices': Invoice.STATUS_CHOICES,
    }
    return render(request, 'invoices/list.html', context)


@login_required
@user_passes_test(is_employee)
def invoice_detail(request, invoice_id):
    """تفاصيل الفاتورة"""
    invoice = get_object_or_404(Invoice, id=invoice_id)

    context = {
        'invoice': invoice,
    }
    return render(request, 'invoices/detail.html', context)


@login_required
@user_passes_test(is_employee)
def invoice_pdf(request, invoice_id):
    """توليد PDF للفاتورة"""
    from django.http import HttpResponse
    from django.template.loader import get_template

    invoice = get_object_or_404(Invoice, id=invoice_id)

    # الحصول على إعدادات الشركة
    try:
        company_settings = CompanySettings.objects.first()
    except CompanySettings.DoesNotExist:
        company_settings = None

    # إعداد السياق
    context = {
        'invoice': invoice,
        'company_settings': company_settings,
    }

    # محاولة استخدام WeasyPrint، وإذا فشل استخدم HTML بسيط
    try:
        from weasyprint import HTML, CSS

        # تحميل القالب
        template = get_template('invoices/pdf_template.html')
        html_string = template.render(context)

        # إنشاء PDF
        html = HTML(string=html_string, base_url=request.build_absolute_uri())

        # CSS للعربية
        css = CSS(string='''
            @page {
                size: A4;
                margin: 1cm;
            }
            body {
                font-family: 'Arial', sans-serif;
                direction: rtl;
                text-align: right;
            }
            .invoice-header {
                border-bottom: 2px solid #333;
                margin-bottom: 20px;
                padding-bottom: 10px;
            }
            .invoice-details {
                margin-bottom: 20px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 8px;
                text-align: right;
            }
            th {
                background-color: #f2f2f2;
            }
            .total {
                font-weight: bold;
                font-size: 1.2em;
            }
            .paid-stamp {
                color: green;
                font-size: 2em;
                font-weight: bold;
                text-align: center;
                margin: 20px 0;
            }
        ''')

        pdf = html.write_pdf(stylesheets=[css])

        # إرجاع الاستجابة
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="invoice_{invoice.invoice_number}.pdf"'

        return response

    except Exception as e:
        # إذا فشل WeasyPrint، أرجع HTML للطباعة
        template = get_template('invoices/pdf_template.html')
        html_string = template.render(context, request)

        response = HttpResponse(html_string, content_type='text/html')
        response['Content-Disposition'] = f'inline; filename="invoice_{invoice.invoice_number}.html"'

        return response


# ==================== رفع ملفات Excel ====================

@login_required
@user_passes_test(is_manager)
def customer_import_excel(request):
    """رفع العملاء من ملف Excel"""
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')

        if not excel_file:
            messages.error(request, 'يرجى اختيار ملف Excel')
            return render(request, 'customers/import_excel.html')

        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'يرجى رفع ملف Excel صحيح (.xlsx أو .xls)')
            return render(request, 'customers/import_excel.html')

        try:
            import pandas as pd

            # قراءة ملف Excel
            df = pd.read_excel(excel_file)

            # التحقق من وجود الأعمدة المطلوبة
            required_columns = ['الاسم', 'رقم الهاتف']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                messages.error(request, f'الأعمدة المطلوبة مفقودة: {", ".join(missing_columns)}')
                return render(request, 'customers/import_excel.html')

            success_count = 0
            error_count = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    name = str(row['الاسم']).strip()
                    phone = str(row['رقم الهاتف']).strip()

                    # تنظيف رقم الهاتف
                    phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
                    if not phone.startswith('+'):
                        if phone.startswith('0'):
                            phone = '+964' + phone[1:]
                        elif len(phone) == 10:
                            phone = '+964' + phone

                    # التحقق من البيانات
                    if not name or name == 'nan':
                        errors.append(f'الصف {index + 2}: الاسم مطلوب')
                        error_count += 1
                        continue

                    if not phone or phone == 'nan':
                        errors.append(f'الصف {index + 2}: رقم الهاتف مطلوب')
                        error_count += 1
                        continue

                    # التحقق من عدم تكرار رقم الهاتف
                    if Customer.objects.filter(phone=phone).exists():
                        errors.append(f'الصف {index + 2}: رقم الهاتف {phone} موجود مسبقاً')
                        error_count += 1
                        continue

                    # إنشاء العميل
                    customer_data = {
                        'name': name,
                        'phone': phone,
                    }

                    # إضافة البيانات الاختيارية
                    if 'البريد الإلكتروني' in df.columns and pd.notna(row['البريد الإلكتروني']):
                        customer_data['email'] = str(row['البريد الإلكتروني']).strip()

                    if 'العنوان' in df.columns and pd.notna(row['العنوان']):
                        customer_data['address'] = str(row['العنوان']).strip()

                    if 'رقم الصفحة' in df.columns and pd.notna(row['رقم الصفحة']):
                        customer_data['page_number'] = str(row['رقم الصفحة']).strip()

                    Customer.objects.create(**customer_data)
                    success_count += 1

                except Exception as e:
                    errors.append(f'الصف {index + 2}: خطأ في البيانات - {str(e)}')
                    error_count += 1

            # عرض النتائج
            if success_count > 0:
                messages.success(request, f'تم إضافة {success_count} عميل بنجاح')

            if error_count > 0:
                error_message = f'فشل في إضافة {error_count} عميل:\n' + '\n'.join(errors[:10])
                if len(errors) > 10:
                    error_message += f'\n... و {len(errors) - 10} أخطاء أخرى'
                messages.error(request, error_message)

            if success_count > 0:
                return redirect('customer_list')

        except Exception as e:
            messages.error(request, f'خطأ في قراءة الملف: {str(e)}')

    # إضافة إحصائيات العملاء
    total_customers = Customer.objects.count()
    context = {
        'total_customers': total_customers,
    }
    return render(request, 'customers/import_excel.html', context)


@login_required
@user_passes_test(is_manager)
def download_excel_template(request):
    """تحميل نموذج Excel للعملاء"""
    from django.http import HttpResponse
    import pandas as pd
    from io import BytesIO

    # إنشاء DataFrame نموذجي
    data = {
        'الاسم': ['أحمد محمد', 'فاطمة علي', 'محمد حسن'],
        'رقم الهاتف': ['07901234567', '07801234567', '07701234567'],
        'البريد الإلكتروني': ['ahmed@example.com', 'fatima@example.com', ''],
        'العنوان': ['بغداد، الكرادة', 'البصرة، الجمعيات', 'أربيل، الشرق'],
        'رقم الصفحة': ['A-001', 'A-002', 'A-003']
    }

    df = pd.DataFrame(data)

    # إنشاء ملف Excel في الذاكرة
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='العملاء', index=False)

    output.seek(0)

    # إرجاع الملف
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="نموذج_العملاء.xlsx"'

    return response


@login_required
def reports_dashboard(request):
    """لوحة التقارير والإحصائيات"""
    from django.db.models import Count, Sum
    from datetime import datetime, timedelta
    import json

    try:
        # الإحصائيات الأساسية
        total_customers = Customer.objects.count()
        total_debts = Debt.objects.aggregate(total=Sum('amount'))['total'] or 0
        total_paid = Payment.objects.aggregate(total=Sum('amount'))['total'] or 0
        remaining_debt = total_debts - total_paid

        # أكبر الديون
        top_debts = Debt.objects.select_related('customer').order_by('-amount')[:10]

        # الديون المتأخرة
        from django.utils import timezone
        overdue_debts = Debt.objects.filter(
            due_date__lt=timezone.now().date(),
            status='active'
        ).select_related('customer')[:10]

        # البيانات الشهرية للرسم البياني
        monthly_data = []
        monthly_labels = []

        for i in range(6):
            month_start = datetime.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end - timedelta(days=month_end.day)

            month_debts = Debt.objects.filter(
                created_date__gte=month_start,
                created_date__lte=month_end
            ).aggregate(total=Sum('amount'))['total'] or 0

            monthly_data.insert(0, float(month_debts))
            monthly_labels.insert(0, month_start.strftime('%Y-%m'))

        # بيانات حالة الديون للرسم الدائري
        status_counts = Debt.objects.values('status').annotate(count=Count('id'))
        status_data = [0, 0, 0]  # [active, paid, cancelled]

        for item in status_counts:
            if item['status'] == 'active':
                status_data[0] = item['count']
            elif item['status'] == 'paid':
                status_data[1] = item['count']
            elif item['status'] == 'cancelled':
                status_data[2] = item['count']

        context = {
            'total_customers': total_customers,
            'total_debts': total_debts,
            'total_paid': total_paid,
            'remaining_debt': remaining_debt,
            'top_debts': top_debts,
            'overdue_debts': overdue_debts,
            'monthly_labels': json.dumps(monthly_labels),
            'monthly_data': json.dumps(monthly_data),
            'status_data': json.dumps(status_data),
        }

        return render(request, 'reports/dashboard.html', context)

    except Exception as e:
        messages.error(request, f'خطأ في تحميل التقارير: {str(e)}')
        # إرجاع بيانات افتراضية في حالة الخطأ
        context = {
            'total_customers': 0,
            'total_debts': 0,
            'total_paid': 0,
            'remaining_debt': 0,
            'top_debts': [],
            'overdue_debts': [],
            'monthly_labels': json.dumps([]),
            'monthly_data': json.dumps([]),
            'status_data': json.dumps([0, 0, 0]),
        }
        return render(request, 'reports/dashboard.html', context)


@login_required
def reports_export(request):
    """تصدير التقارير إلى Excel"""
    try:
        from django.http import HttpResponse
        import pandas as pd
        from io import BytesIO

        # إنشاء البيانات للتصدير
        customers_data = []
        for customer in Customer.objects.all():
            customers_data.append({
                'الاسم': customer.name,
                'رقم الهاتف': customer.phone,
                'البريد الإلكتروني': customer.email or '',
                'العنوان': customer.address or '',
                'رقم الصفحة': customer.page_number or '',
                'إجمالي الديون': customer.total_debt,
                'المبلغ المتبقي': customer.remaining_debt,
                'تاريخ الإضافة': customer.created_date.strftime('%Y-%m-%d')
            })

        debts_data = []
        for debt in Debt.objects.select_related('customer').all():
            debts_data.append({
                'العميل': debt.customer.name,
                'الوصف': debt.description,
                'المبلغ': debt.amount,
                'المبلغ المدفوع': debt.total_paid,
                'المبلغ المتبقي': debt.remaining_amount,
                'تاريخ الاستحقاق': debt.due_date.strftime('%Y-%m-%d'),
                'الحالة': debt.get_status_display(),
                'تاريخ الإنشاء': debt.created_date.strftime('%Y-%m-%d')
            })

        # إنشاء ملف Excel
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame(customers_data).to_excel(writer, sheet_name='العملاء', index=False)
            pd.DataFrame(debts_data).to_excel(writer, sheet_name='الديون', index=False)

        output.seek(0)

        # إرجاع الملف
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="تقرير_شامل.xlsx"'

        return response

    except Exception as e:
        messages.error(request, f'خطأ في تصدير التقارير: {str(e)}')
        return redirect('reports_dashboard')


@login_required
@user_passes_test(is_manager)
def currency_settings(request):
    """إعدادات العملة"""
    try:
        company_settings = CompanySettings.objects.first()
    except CompanySettings.DoesNotExist:
        company_settings = None

    if request.method == 'POST':
        currency = request.POST.get('currency')

        if currency in ['IQD', 'USD']:
            if company_settings:
                company_settings.currency = currency
                company_settings.save()
            else:
                CompanySettings.objects.create(
                    company_name='محلات أبو علاء',
                    phone='+964 770 123 4567',
                    email='info@abualaastores.com',
                    address='بغداد، العراق',
                    currency=currency,
                    invoice_terms='يرجى السداد خلال 30 يوم من تاريخ الفاتورة'
                )

            messages.success(request, 'تم تحديث إعدادات العملة بنجاح!')
            return redirect('currency_settings')
        else:
            messages.error(request, 'عملة غير صحيحة!')

    # تحديد العملة الحالية
    current_currency_code = company_settings.currency if company_settings else 'IQD'
    current_currency = 'دينار عراقي' if current_currency_code == 'IQD' else 'دولار أمريكي'

    context = {
        'current_currency': current_currency,
        'current_currency_code': current_currency_code,
        'company_settings': company_settings,
    }

    return render(request, 'settings/currency.html', context)


@login_required
@user_passes_test(is_manager)
def backup_dashboard(request):
    """لوحة النسخ الاحتياطي"""
    from django.http import HttpResponse

    # حل مؤقت - إرجاع HTML مباشر
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>النسخ الاحتياطية</title>
        <meta charset="utf-8">
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-5">
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header">
                            <h3><i class="fas fa-download"></i> النسخ الاحتياطية</h3>
                        </div>
                        <div class="card-body text-center">
                            <h5>تحميل نسخة احتياطية</h5>
                            <p class="text-muted">احصل على نسخة من جميع بياناتك (العملاء، الديون، المدفوعات، الفواتير)</p>
                            <a href="/backup/download/" class="btn btn-success btn-lg">
                                <i class="fas fa-download"></i> تحميل النسخة الاحتياطية
                            </a>
                            <br><br>
                            <a href="/" class="btn btn-secondary">العودة للرئيسية</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    return HttpResponse(html)


@login_required
@user_passes_test(is_manager)
def create_backup(request):
    """إنشاء نسخة احتياطية"""
    # تحويل مباشر للتحميل
    return redirect('download_backup')


@login_required
@user_passes_test(is_manager)
def download_backup(request):
    """تحميل نسخة احتياطية محلية"""
    from django.http import HttpResponse, JsonResponse
    from datetime import datetime
    import json

    try:
        # إنشاء نسخة احتياطية بصيغة JSON بسيطة
        from .models import Customer, Debt, Payment, Invoice, CompanySettings

        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'customers': [],
            'debts': [],
            'payments': [],
            'invoices': [],
            'company_settings': {}
        }

        # بيانات العملاء
        for customer in Customer.objects.all():
            backup_data['customers'].append({
                'id': customer.id,
                'name': customer.name,
                'phone': customer.phone,
                'email': customer.email or '',
                'address': customer.address or '',
                'page_number': customer.page_number or '',
                'total_debt': str(customer.total_debt),
                'remaining_debt': str(customer.remaining_debt),
                'created_at': customer.created_at.isoformat(),
            })

        # بيانات الديون
        for debt in Debt.objects.all():
            backup_data['debts'].append({
                'id': debt.id,
                'customer_id': debt.customer.id,
                'customer_name': debt.customer.name,
                'amount': str(debt.amount),
                'remaining_amount': str(debt.remaining_amount),
                'description': debt.description or '',
                'status': debt.status,
                'created_at': debt.created_at.isoformat(),
            })

        # بيانات المدفوعات
        for payment in Payment.objects.all():
            backup_data['payments'].append({
                'id': payment.id,
                'debt_id': payment.debt.id,
                'customer_name': payment.debt.customer.name,
                'amount': str(payment.amount),
                'payment_date': payment.payment_date.isoformat(),
                'notes': payment.notes or '',
            })

        # بيانات الفواتير
        for invoice in Invoice.objects.all():
            backup_data['invoices'].append({
                'id': invoice.id,
                'customer_id': invoice.customer.id,
                'customer_name': invoice.customer.name,
                'invoice_number': invoice.invoice_number,
                'total_amount': str(invoice.total_amount),
                'status': invoice.status,
                'created_at': invoice.created_at.isoformat(),
            })

        # إعدادات الشركة
        try:
            company = CompanySettings.objects.first()
            if company:
                backup_data['company_settings'] = {
                    'name': company.name,
                    'address': company.address or '',
                    'phone': company.phone or '',
                    'email': company.email or '',
                    'currency': company.currency,
                }
        except:
            pass

        # إنشاء ملف JSON
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_abu_alaa_{timestamp}.json'

        response = HttpResponse(
            json.dumps(backup_data, ensure_ascii=False, indent=2),
            content_type='application/json; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        return JsonResponse({'error': f'خطأ في تحميل النسخة الاحتياطية: {e}'}, status=500)


@login_required
@user_passes_test(is_manager)
def backup_settings(request):
    """إعدادات النسخ الاحتياطي التلقائي"""
    if request.method == 'POST':
        # هنا يمكن إضافة إعدادات الجدولة التلقائية
        # مثل تفعيل النسخ اليومي أو الأسبوعي
        messages.success(request, 'تم حفظ إعدادات النسخ الاحتياطي!')
        return redirect('backup_dashboard')

    context = {
        'backup_enabled': True,  # يمكن جعل هذا قابل للتخصيص
    }

    return render(request, 'backup/settings.html', context)


@login_required
@user_passes_test(is_manager)
def logo_settings(request):
    """إعدادات الشعار والعلامة المائية"""
    try:
        company_settings = CompanySettings.objects.first()
    except CompanySettings.DoesNotExist:
        company_settings = None

    if request.method == 'POST':
        if 'logo' in request.FILES:
            logo_file = request.FILES['logo']

            # التحقق من نوع الملف
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif']
            if logo_file.content_type not in allowed_types:
                messages.error(request, 'يرجى رفع ملف صورة صحيح (JPG, PNG, GIF)')
                return redirect('logo_settings')

            # التحقق من حجم الملف (أقل من 5 ميجا)
            if logo_file.size > 5 * 1024 * 1024:
                messages.error(request, 'حجم الملف كبير جداً. يرجى رفع ملف أقل من 5 ميجابايت')
                return redirect('logo_settings')

            if company_settings:
                # حذف الشعار القديم إذا وجد
                if company_settings.logo:
                    company_settings.logo.delete()
                company_settings.logo = logo_file
                company_settings.save()
            else:
                CompanySettings.objects.create(
                    company_name='محلات أبو علاء',
                    phone='+964 770 123 4567',
                    email='info@abualaastores.com',
                    address='بغداد، العراق',
                    currency='USD',
                    logo=logo_file,
                    invoice_terms='يرجى السداد خلال 30 يوم من تاريخ الفاتورة'
                )

            messages.success(request, 'تم تحديث الشعار بنجاح!')
            return redirect('logo_settings')

        elif 'remove_logo' in request.POST:
            if company_settings and company_settings.logo:
                company_settings.logo.delete()
                company_settings.logo = None
                company_settings.save()
                messages.success(request, 'تم حذف الشعار بنجاح!')
            return redirect('logo_settings')

    context = {
        'company_settings': company_settings,
    }

    return render(request, 'settings/logo.html', context)


@login_required
def change_password(request):
    """تغيير كلمة المرور"""
    from django.contrib.auth import update_session_auth_hash
    from django.contrib.auth.forms import PasswordChangeForm

    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # للحفاظ على الجلسة
            messages.success(request, 'تم تغيير كلمة المرور بنجاح!')
            return redirect('change_password')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)

    context = {
        'form': form,
    }

    return render(request, 'auth/change_password.html', context)


def custom_login(request):
    """تسجيل الدخول المخصص"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)

                # التحقق من كلمة المرور الافتراضية
                if user.check_password('admin123') or user.check_password('employee123'):
                    messages.warning(
                        request,
                        'يرجى تغيير كلمة المرور الافتراضية لأمان أفضل!'
                    )
                    return redirect('change_password')

                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'اسم المستخدم أو كلمة المرور غير صحيحة')
        else:
            messages.error(request, 'يرجى إدخال اسم المستخدم وكلمة المرور')

    return render(request, 'auth/login.html')
