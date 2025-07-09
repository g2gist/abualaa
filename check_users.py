#!/usr/bin/env python
"""
فحص المستخدمين الموجودين في النظام
"""
import os
import django

# إعداد Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'abu_alaa_project.settings')
django.setup()

from django.contrib.auth.models import User

def check_users():
    """فحص جميع المستخدمين"""
    
    print("🔍 فحص المستخدمين الموجودين...")
    print("=" * 50)
    
    users = User.objects.all()
    
    if not users.exists():
        print("❌ لا يوجد مستخدمين في النظام!")
        print("🔧 سأقوم بإنشاء مستخدم مدير...")
        
        # إنشاء مستخدم مدير
        try:
            user = User.objects.create_superuser(
                username='admin',
                email='admin@abualaa.com',
                password='admin123'
            )
            print("✅ تم إنشاء المستخدم المدير بنجاح!")
            print(f"👤 Username: admin")
            print(f"🔑 Password: admin123")
            
        except Exception as e:
            print(f"❌ خطأ في إنشاء المستخدم: {e}")
    else:
        print(f"📊 عدد المستخدمين: {users.count()}")
        print("\n👥 قائمة المستخدمين:")
        
        for user in users:
            print(f"  • Username: {user.username}")
            print(f"    Email: {user.email}")
            print(f"    Is Staff: {user.is_staff}")
            print(f"    Is Superuser: {user.is_superuser}")
            print(f"    Is Active: {user.is_active}")
            print(f"    Last Login: {user.last_login}")
            print("-" * 30)

if __name__ == '__main__':
    check_users()
