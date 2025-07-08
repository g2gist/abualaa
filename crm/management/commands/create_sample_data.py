from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from crm.models import Customer, Debt, Payment, Invoice, CompanySettings
from decimal import Decimal
from datetime import date, timedelta
import random


class Command(BaseCommand):
    help = 'إنشاء بيانات تجريبية للنظام'

    def handle(self, *args, **options):
        self.stdout.write('بدء إنشاء البيانات التجريبية...')
        
        # إنشاء إعدادات الشركة
        if not CompanySettings.objects.exists():
            CompanySettings.objects.create(
                company_name='محلات أبو علاء',
                phone='+964 770 123 4567',
                email='info@abualaastores.com',
                address='بغداد، العراق',
                currency='USD',  # تغيير إلى الدولار كافتراضي
                invoice_terms='يرجى السداد خلال 30 يوم من تاريخ الفاتورة'
            )
            self.stdout.write('تم إنشاء إعدادات الشركة')
        
        # إنشاء مستخدمين
        if not User.objects.filter(username='employee').exists():
            employee = User.objects.create_user(
                username='employee',
                password='employee123',
                first_name='أحمد',
                last_name='محمد',
                email='employee@abualaastores.com'
            )
            self.stdout.write('تم إنشاء حساب الموظف')
        
        # إنشاء عملاء تجريبيين
        customers_data = [
            {'name': 'محمد أحمد السعيد', 'phone': '+9647901234567', 'email': 'mohammed@example.com', 'address': 'بغداد، الكرادة', 'page_number': 'A-001'},
            {'name': 'فاطمة علي الزهراني', 'phone': '+9647802345678', 'email': 'fatima@example.com', 'address': 'البصرة، الجمعيات', 'page_number': 'A-002'},
            {'name': 'عبدالله خالد المطيري', 'phone': '+9647703456789', 'email': 'abdullah@example.com', 'address': 'أربيل، الشرق', 'page_number': 'A-003'},
            {'name': 'نورا سعد القحطاني', 'phone': '+9647604567890', 'email': 'nora@example.com', 'address': 'النجف، المركز', 'page_number': 'A-004'},
            {'name': 'يوسف عمر البلوي', 'phone': '+9647505678901', 'email': 'youssef@example.com', 'address': 'كربلاء، الحسين', 'page_number': 'A-005'},
        ]
        
        customers = []
        for customer_data in customers_data:
            customer, created = Customer.objects.get_or_create(
                phone=customer_data['phone'],
                defaults=customer_data
            )
            if created:
                customers.append(customer)
                self.stdout.write(f'تم إنشاء العميل: {customer.name}')
        
        # إنشاء ديون تجريبية
        admin_user = User.objects.filter(is_superuser=True).first()
        
        debts_data = [
            {'amount': Decimal('5000.00'), 'description': 'شراء أجهزة كهربائية', 'days_offset': -30},
            {'amount': Decimal('2500.00'), 'description': 'أثاث منزلي', 'days_offset': -15},
            {'amount': Decimal('1200.00'), 'description': 'أدوات مطبخ', 'days_offset': -7},
            {'amount': Decimal('3500.00'), 'description': 'معدات رياضية', 'days_offset': 15},
            {'amount': Decimal('800.00'), 'description': 'ألعاب أطفال', 'days_offset': 30},
        ]
        
        for i, debt_data in enumerate(debts_data):
            if i < len(customers):
                customer = customers[i]
                due_date = date.today() + timedelta(days=debt_data['days_offset'])
                
                debt = Debt.objects.create(
                    customer=customer,
                    amount=debt_data['amount'],
                    description=debt_data['description'],
                    due_date=due_date,
                    created_by=admin_user
                )
                
                # إنشاء فاتورة
                Invoice.objects.create(debt=debt)
                
                # إنشاء دفعات عشوائية لبعض الديون
                if random.choice([True, False]):
                    payment_amount = debt.amount * Decimal(str(random.uniform(0.3, 0.8)))
                    Payment.objects.create(
                        debt=debt,
                        amount=payment_amount,
                        payment_method=random.choice(['cash', 'bank_transfer', 'check']),
                        notes='دفعة تجريبية',
                        received_by=admin_user
                    )
                    self.stdout.write(f'تم إنشاء دفعة للدين: {debt.description}')
                
                self.stdout.write(f'تم إنشاء الدين: {debt.description}')
        
        self.stdout.write(
            self.style.SUCCESS('تم إنشاء البيانات التجريبية بنجاح!')
        )
