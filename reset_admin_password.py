#!/usr/bin/env python
"""
إعادة تعيين كلمة مرور المدير
"""
import os
import django

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'abu_alaa_project.settings')
django.setup()

from django.contrib.auth.models import User

def reset_admin_password():
    """إعادة تعيين كلمة مرور admin"""
    
    try:
        user = User.objects.get(username='admin')
        user.set_password('admin123')
        user.save()
        
        print("✅ تم تغيير كلمة مرور admin بنجاح!")
        print("👤 Username: admin")
        print("🔑 Password: admin123")
        print("🌐 يمكنك تسجيل الدخول الآن!")
        
    except User.DoesNotExist:
        print("❌ المستخدم admin غير موجود!")
        
    except Exception as e:
        print(f"❌ خطأ: {e}")

if __name__ == '__main__':
    reset_admin_password()
