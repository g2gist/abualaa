#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
أداة الحصول على معلومات الشبكة - محلات أبو علاء
Network Information Tool - Abu Alaa Stores

هذه الأداة تعرض عناوين IP المتاحة للوصول للنظام
"""

import socket
import subprocess
import platform
import requests
from urllib.parse import urlparse

def get_local_ip():
    """الحصول على عنوان IP المحلي"""
    try:
        # الاتصال بخادم خارجي للحصول على IP المحلي
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "غير متاح"

def get_public_ip():
    """الحصول على عنوان IP العام"""
    try:
        response = requests.get("https://api.ipify.org", timeout=5)
        return response.text.strip()
    except Exception:
        return "غير متاح"

def get_all_network_interfaces():
    """الحصول على جميع واجهات الشبكة"""
    interfaces = []
    try:
        if platform.system() == "Windows":
            # استخدام ipconfig في Windows
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='cp1256')
            lines = result.stdout.split('\n')
            
            current_adapter = ""
            for line in lines:
                line = line.strip()
                if "adapter" in line.lower() or "محول" in line:
                    current_adapter = line
                elif "IPv4" in line or "عنوان IPv4" in line:
                    ip = line.split(':')[-1].strip()
                    if ip and ip != "127.0.0.1":
                        interfaces.append({
                            'name': current_adapter,
                            'ip': ip
                        })
        else:
            # استخدام ifconfig في Linux/Mac
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            # تحليل النتيجة...
            pass
            
    except Exception as e:
        print(f"خطأ في الحصول على واجهات الشبكة: {e}")
    
    return interfaces

def check_port_open(ip, port=8000):
    """فحص ما إذا كان المنفذ مفتوح"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except Exception:
        return False

def generate_qr_code(url):
    """إنشاء QR Code للرابط"""
    try:
        import qrcode
        from io import BytesIO
        import base64
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # حفظ كملف
        img.save("server_qr.png")
        print(f"📱 تم إنشاء QR Code: server_qr.png")
        
        return True
    except ImportError:
        print("💡 لإنشاء QR Code، قم بتثبيت: pip install qrcode[pil]")
        return False
    except Exception as e:
        print(f"خطأ في إنشاء QR Code: {e}")
        return False

def show_network_info():
    """عرض معلومات الشبكة الشاملة"""
    print("\n" + "="*60)
    print("🌐 معلومات الشبكة - نظام محلات أبو علاء")
    print("Network Information - Abu Alaa Stores System")
    print("="*60)
    
    # عنوان IP المحلي
    local_ip = get_local_ip()
    print(f"\n📍 عنوان IP المحلي: {local_ip}")
    
    # عنوان IP العام
    public_ip = get_public_ip()
    print(f"🌍 عنوان IP العام: {public_ip}")
    
    # فحص حالة الخادم
    server_running = check_port_open('localhost', 8000)
    status = "🟢 يعمل" if server_running else "🔴 متوقف"
    print(f"⚡ حالة الخادم: {status}")
    
    print("\n" + "="*60)
    print("🔗 روابط الوصول للنظام:")
    print("="*60)
    
    # الروابط المحلية
    print("\n📱 الوصول المحلي:")
    local_urls = [
        f"http://localhost:8000",
        f"http://127.0.0.1:8000"
    ]
    
    if local_ip != "غير متاح":
        local_urls.append(f"http://{local_ip}:8000")
    
    for url in local_urls:
        working = "✅" if check_port_open(urlparse(url).hostname, 8000) else "❌"
        print(f"   {working} {url}")
    
    # روابط الشبكة المحلية
    print("\n🏠 الوصول من الشبكة المحلية:")
    if local_ip != "غير متاح":
        network_url = f"http://{local_ip}:8000"
        working = "✅" if check_port_open(local_ip, 8000) else "❌"
        print(f"   {working} {network_url}")
        print(f"   📝 استخدم هذا الرابط من أي جهاز في نفس الشبكة")
        
        # إنشاء QR Code
        if server_running:
            generate_qr_code(network_url)
    else:
        print("   ❌ غير متاح")
    
    # الوصول من الإنترنت
    print("\n🌍 الوصول من الإنترنت:")
    if public_ip != "غير متاح":
        internet_url = f"http://{public_ip}:8000"
        print(f"   🔗 {internet_url}")
        print(f"   ⚠️ يتطلب إعداد Port Forwarding في الراوتر")
        print(f"   📝 توجيه المنفذ 8000 إلى {local_ip}:8000")
    else:
        print("   ❌ غير متاح")
    
    # واجهات الشبكة
    print("\n🔌 واجهات الشبكة المتاحة:")
    interfaces = get_all_network_interfaces()
    if interfaces:
        for interface in interfaces:
            print(f"   📡 {interface['name']}: {interface['ip']}")
    else:
        print("   📝 استخدم 'ipconfig' (Windows) أو 'ifconfig' (Linux/Mac) لعرض التفاصيل")
    
    print("\n" + "="*60)
    print("📋 معلومات إضافية:")
    print("="*60)
    print(f"🖥️ نظام التشغيل: {platform.system()} {platform.release()}")
    print(f"🐍 إصدار Python: {platform.python_version()}")
    print(f"💻 اسم الجهاز: {platform.node()}")
    
    print("\n" + "="*60)
    print("🔧 إرشادات الإعداد:")
    print("="*60)
    
    print("\n📱 للوصول من الهاتف المحمول:")
    print("   1. تأكد من اتصال الهاتف بنفس شبكة WiFi")
    print("   2. افتح المتصفح في الهاتف")
    if local_ip != "غير متاح":
        print(f"   3. اذهب إلى: http://{local_ip}:8000")
    print("   4. أو امسح QR Code إذا كان متاح")
    
    print("\n🌍 للوصول من الإنترنت:")
    print("   1. ادخل إعدادات الراوتر (عادة 192.168.1.1)")
    print("   2. ابحث عن Port Forwarding أو Virtual Server")
    print("   3. أضف قاعدة جديدة:")
    print("      - External Port: 8000")
    print("      - Internal Port: 8000")
    if local_ip != "غير متاح":
        print(f"      - Internal IP: {local_ip}")
    print("   4. احفظ الإعدادات وأعد تشغيل الراوتر")
    
    print("\n🔒 أمان الشبكة:")
    print("   ⚠️ تأكد من تغيير كلمات المرور الافتراضية")
    print("   ⚠️ استخدم HTTPS في البيئة الإنتاجية")
    print("   ⚠️ قم بإعداد Firewall مناسب")
    
    print("\n" + "="*60)

def test_connectivity():
    """اختبار الاتصال"""
    print("\n🔍 اختبار الاتصال...")
    print("="*40)
    
    # اختبار الاتصال المحلي
    local_test = check_port_open('localhost', 8000)
    print(f"📍 الاتصال المحلي: {'✅ يعمل' if local_test else '❌ فشل'}")
    
    # اختبار الاتصال عبر IP المحلي
    local_ip = get_local_ip()
    if local_ip != "غير متاح":
        network_test = check_port_open(local_ip, 8000)
        print(f"🏠 الاتصال عبر الشبكة: {'✅ يعمل' if network_test else '❌ فشل'}")
    
    # اختبار الإنترنت
    try:
        internet_test = requests.get("https://www.google.com", timeout=5)
        print(f"🌍 الاتصال بالإنترنت: {'✅ يعمل' if internet_test.status_code == 200 else '❌ فشل'}")
    except:
        print(f"🌍 الاتصال بالإنترنت: ❌ فشل")

def main():
    """الدالة الرئيسية"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            test_connectivity()
        elif command == "ip":
            local_ip = get_local_ip()
            public_ip = get_public_ip()
            print(f"Local IP: {local_ip}")
            print(f"Public IP: {public_ip}")
        elif command == "help":
            print("🔧 أداة معلومات الشبكة - محلات أبو علاء")
            print("="*50)
            print("الاستخدام:")
            print("  python get_network_info.py       - عرض معلومات شاملة")
            print("  python get_network_info.py test  - اختبار الاتصال")
            print("  python get_network_info.py ip    - عرض عناوين IP فقط")
            print("  python get_network_info.py help  - عرض هذه المساعدة")
        else:
            print(f"❌ أمر غير معروف: {command}")
            print("استخدم 'python get_network_info.py help' للمساعدة")
    else:
        show_network_info()

if __name__ == "__main__":
    main()
