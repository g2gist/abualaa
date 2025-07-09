#!/usr/bin/env python
"""
إنشاء مستخدم مدير تلقائياً
"""
import os
import django

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'abu_alaa_project.settings')
django.setup()

from django.contrib.auth.models import User

def create_superuser():
    """إنشاء مستخدم مدير إذا لم يكن موجوداً"""
    
    username = 'admin'
    email = 'admin@abualaa.com'
    password = 'admin123'
    
    if User.objects.filter(username=username).exists():
        print(f'✅ المستخدم {username} موجود بالفعل')
        return
    
    try:
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f'✅ تم إنشاء المستخدم المدير بنجاح!')
        print(f'📧 Username: {username}')
        print(f'🔑 Password: {password}')
        print(f'🌐 يمكنك تسجيل الدخول على: https://abualaa.onrender.com/admin/')
        
    except Exception as e:
        print(f'❌ خطأ في إنشاء المستخدم: {e}')

if __name__ == '__main__':
    create_superuser()
