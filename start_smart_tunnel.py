#!/usr/bin/env python3
"""
سكريبت ذكي لتشغيل Cloudflare Tunnel مع تحديث CSRF تلقائياً
"""
import os
import re
import sys
import time
import subprocess
import threading
from pathlib import Path

def update_csrf_settings(tunnel_url):
    """تحديث إعدادات CSRF في Django"""
    settings_path = Path("abu_alaa_project/settings.py")
    
    if not settings_path.exists():
        print("❌ ملف settings.py غير موجود!")
        return False
    
    # قراءة الملف
    with open(settings_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # البحث عن CSRF_TRUSTED_ORIGINS
    pattern = r"CSRF_TRUSTED_ORIGINS = \[(.*?)\]"
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        # إضافة النطاق الجديد
        origins = match.group(1)
        if tunnel_url not in origins:
            new_origins = f"""[
    'https://*.trycloudflare.com',
    '{tunnel_url}',
    'https://*.ngrok.io',
    'https://*.ngrok-free.app',
    'http://localhost:8080',
    'http://127.0.0.1:8080',
]"""
            content = content.replace(f"CSRF_TRUSTED_ORIGINS = [{origins}]", 
                                    f"CSRF_TRUSTED_ORIGINS = {new_origins}")
            
            # كتابة الملف
            with open(settings_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ تم تحديث CSRF للنطاق: {tunnel_url}")
            return True
    
    return False

def start_django():
    """تشغيل Django"""
    print("🚀 جاري تشغيل Django...")
    cmd = ["waitress-serve", "--host=127.0.0.1", "--port=8080", 
           "abu_alaa_project.wsgi:application"]
    
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                           stderr=subprocess.STDOUT, text=True)

def start_tunnel():
    """تشغيل Cloudflare Tunnel"""
    print("🌍 جاري تشغيل Cloudflare Tunnel...")
    cmd = ["./cloudflared.exe", "tunnel", "--url", "http://127.0.0.1:8080"]
    
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                           stderr=subprocess.STDOUT, text=True)

def monitor_tunnel(process):
    """مراقبة مخرجات Tunnel للحصول على الرابط"""
    tunnel_url = None
    
    for line in process.stdout:
        print(line.strip())
        
        # البحث عن رابط Tunnel
        if "Your quick Tunnel has been created!" in line:
            continue
        elif "trycloudflare.com" in line and "https://" in line:
            match = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
            if match:
                tunnel_url = match.group(0)
                print(f"\n🎉 تم إنشاء الرابط العالمي: {tunnel_url}")
                
                # تحديث إعدادات CSRF
                if update_csrf_settings(tunnel_url):
                    print("🔄 يرجى إعادة تشغيل Django لتطبيق الإعدادات الجديدة")
                
                break
    
    return tunnel_url

def main():
    """الدالة الرئيسية"""
    print("=" * 50)
    print("    تشغيل نظام CRM مع Cloudflare Tunnel")
    print("=" * 50)
    
    # التأكد من وجود cloudflared
    if not os.path.exists("cloudflared.exe"):
        print("❌ cloudflared.exe غير موجود!")
        print("يرجى تشغيل setup_cloudflare_tunnel.bat أولاً")
        return
    
    # تشغيل Django
    django_process = start_django()
    time.sleep(5)  # انتظار تشغيل Django
    
    # تشغيل Tunnel
    tunnel_process = start_tunnel()
    
    try:
        # مراقبة Tunnel
        tunnel_url = monitor_tunnel(tunnel_process)
        
        if tunnel_url:
            print(f"\n✅ النظام يعمل الآن على: {tunnel_url}")
            print("📱 يمكن الوصول إليه من أي دولة في العالم!")
            print("\n⚠️  لإيقاف النظام: اضغط Ctrl+C")
            
            # انتظار إيقاف النظام
            tunnel_process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 جاري إيقاف النظام...")
        
    finally:
        # إيقاف العمليات
        django_process.terminate()
        tunnel_process.terminate()
        print("✅ تم إيقاف النظام بنجاح")

if __name__ == "__main__":
    main()
