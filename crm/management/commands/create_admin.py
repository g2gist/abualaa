from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Create admin user for Render deployment'

    def handle(self, *args, **options):
        # حذف المستخدم إذا كان موجود
        User.objects.filter(username='admin').delete()
        
        # إنشاء مستخدم جديد
        user = User.objects.create_superuser(
            username='admin',
            email='admin@abualaa.com',
            password='admin123'
        )
        
        self.stdout.write(
            self.style.SUCCESS('✅ Admin user created successfully!')
        )
        self.stdout.write(f'Username: admin')
        self.stdout.write(f'Password: admin123')
