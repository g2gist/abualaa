#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
أداة إعادة تعيين كلمة المرور - محلات أبو علاء
Password Reset Tool - Abu Alaa Stores

هذه الأداة تسمح بإعادة تعيين كلمات المرور للمستخدمين
"""

import os
import sys
import django
from pathlib import Path

# إعداد Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'abu_alaa_project.settings')
django.setup()

from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

def show_users():
    """عرض جميع المستخدمين"""
    print("\n" + "="*50)
    print("📋 قائمة المستخدمين الحاليين:")
    print("="*50)
    
    users = User.objects.all()
    if not users:
        print("❌ لا يوجد مستخدمين في النظام")
        return
    
    for i, user in enumerate(users, 1):
        status = "🔴 غير نشط" if not user.is_active else "🟢 نشط"
        admin_status = "👑 مدير" if user.is_superuser else "👤 مستخدم عادي"
        last_login = user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else "لم يسجل دخول"
        
        print(f"{i}. اسم المستخدم: {user.username}")
        print(f"   البريد الإلكتروني: {user.email or 'غير محدد'}")
        print(f"   الحالة: {status}")
        print(f"   النوع: {admin_status}")
        print(f"   آخر تسجيل دخول: {last_login}")
        print(f"   تاريخ الإنشاء: {user.date_joined.strftime('%Y-%m-%d')}")
        print("-" * 30)

def reset_user_password(username, new_password):
    """إعادة تعيين كلمة مرور مستخدم"""
    try:
        user = User.objects.get(username=username)
        user.set_password(new_password)
        user.save()
        
        print(f"✅ تم تغيير كلمة مرور المستخدم '{username}' بنجاح!")
        return True
        
    except ObjectDoesNotExist:
        print(f"❌ المستخدم '{username}' غير موجود")
        return False
    except Exception as e:
        print(f"❌ خطأ في تغيير كلمة المرور: {e}")
        return False

def create_new_user(username, email, password, is_superuser=True):
    """إنشاء مستخدم جديد"""
    try:
        if User.objects.filter(username=username).exists():
            print(f"❌ المستخدم '{username}' موجود بالفعل")
            return False
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        if is_superuser:
            user.is_superuser = True
            user.is_staff = True
            user.save()
        
        print(f"✅ تم إنشاء المستخدم '{username}' بنجاح!")
        return True
        
    except Exception as e:
        print(f"❌ خطأ في إنشاء المستخدم: {e}")
        return False

def delete_user(username):
    """حذف مستخدم"""
    try:
        user = User.objects.get(username=username)
        
        # تأكيد الحذف
        confirm = input(f"⚠️ هل أنت متأكد من حذف المستخدم '{username}'؟ (y/N): ")
        if confirm.lower() != 'y':
            print("❌ تم إلغاء عملية الحذف")
            return False
        
        user.delete()
        print(f"✅ تم حذف المستخدم '{username}' بنجاح!")
        return True
        
    except ObjectDoesNotExist:
        print(f"❌ المستخدم '{username}' غير موجود")
        return False
    except Exception as e:
        print(f"❌ خطأ في حذف المستخدم: {e}")
        return False

def interactive_mode():
    """الوضع التفاعلي"""
    print("\n🔧 أداة إدارة المستخدمين - محلات أبو علاء")
    print("User Management Tool - Abu Alaa Stores")
    print("="*60)
    
    while True:
        print("\n📋 الخيارات المتاحة:")
        print("1. عرض جميع المستخدمين")
        print("2. إعادة تعيين كلمة مرور")
        print("3. إنشاء مستخدم جديد")
        print("4. حذف مستخدم")
        print("5. خروج")
        
        choice = input("\n🔢 اختر رقم العملية (1-5): ").strip()
        
        if choice == "1":
            show_users()
            
        elif choice == "2":
            show_users()
            username = input("\n👤 أدخل اسم المستخدم: ").strip()
            if username:
                new_password = input("🔑 أدخل كلمة المرور الجديدة: ").strip()
                if new_password:
                    reset_user_password(username, new_password)
                else:
                    print("❌ كلمة المرور لا يمكن أن تكون فارغة")
            else:
                print("❌ اسم المستخدم لا يمكن أن يكون فارغ")
                
        elif choice == "3":
            username = input("\n👤 أدخل اسم المستخدم الجديد: ").strip()
            if username:
                email = input("📧 أدخل البريد الإلكتروني (اختياري): ").strip()
                password = input("🔑 أدخل كلمة المرور: ").strip()
                if password:
                    is_admin = input("👑 هل تريد جعله مدير؟ (y/N): ").strip().lower() == 'y'
                    create_new_user(username, email, password, is_admin)
                else:
                    print("❌ كلمة المرور لا يمكن أن تكون فارغة")
            else:
                print("❌ اسم المستخدم لا يمكن أن يكون فارغ")
                
        elif choice == "4":
            show_users()
            username = input("\n👤 أدخل اسم المستخدم المراد حذفه: ").strip()
            if username:
                delete_user(username)
            else:
                print("❌ اسم المستخدم لا يمكن أن يكون فارغ")
                
        elif choice == "5":
            print("\n👋 شكراً لاستخدام أداة إدارة المستخدمين!")
            break
            
        else:
            print("❌ خيار غير صحيح، يرجى اختيار رقم من 1 إلى 5")

def quick_reset():
    """إعادة تعيين سريعة للمستخدمين الافتراضيين"""
    print("\n🚀 إعادة تعيين سريعة للمستخدمين الافتراضيين")
    print("="*50)
    
    # إعادة تعيين أو إنشاء مستخدم admin
    admin_password = "admin123"
    if User.objects.filter(username="admin").exists():
        reset_user_password("admin", admin_password)
    else:
        create_new_user("admin", "admin@abualaastores.com", admin_password, True)
    
    # إعادة تعيين أو إنشاء مستخدم manager
    manager_password = "manager123"
    if User.objects.filter(username="manager").exists():
        reset_user_password("manager", manager_password)
    else:
        create_new_user("manager", "manager@abualaastores.com", manager_password, True)
    
    print("\n📋 بيانات تسجيل الدخول:")
    print("-" * 30)
    print("👑 المدير الرئيسي:")
    print(f"   اسم المستخدم: admin")
    print(f"   كلمة المرور: {admin_password}")
    print("\n👤 المدير:")
    print(f"   اسم المستخدم: manager")
    print(f"   كلمة المرور: {manager_password}")
    print("\n🌐 رابط تسجيل الدخول: http://localhost:8000/login/")

def main():
    """الدالة الرئيسية"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "quick":
            quick_reset()
        elif command == "list":
            show_users()
        elif command == "help":
            print("🔧 أداة إدارة المستخدمين - محلات أبو علاء")
            print("="*50)
            print("الاستخدام:")
            print("  python reset_password.py          - الوضع التفاعلي")
            print("  python reset_password.py quick    - إعادة تعيين سريعة")
            print("  python reset_password.py list     - عرض المستخدمين")
            print("  python reset_password.py help     - عرض هذه المساعدة")
        else:
            print(f"❌ أمر غير معروف: {command}")
            print("استخدم 'python reset_password.py help' لعرض المساعدة")
    else:
        interactive_mode()

if __name__ == "__main__":
    main()
