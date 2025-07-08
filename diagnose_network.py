#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
أداة تشخيص مشاكل الشبكة - محلات أبو علاء
Network Diagnostics Tool - Abu Alaa Stores

هذه الأداة تشخص وتحل مشاكل الوصول من الأجهزة الأخرى
"""

import socket
import subprocess
import platform
import time
import threading
from datetime import datetime

def check_port_binding():
    """فحص ربط المنفذ"""
    print("🔍 فحص ربط المنفذ 8000...")
    
    try:
        # فحص المنفذ على localhost
        sock_local = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result_local = sock_local.connect_ex(('127.0.0.1', 8000))
        sock_local.close()
        
        # فحص المنفذ على جميع الواجهات
        sock_all = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result_all = sock_all.connect_ex(('0.0.0.0', 8000))
        sock_all.close()
        
        print(f"   📍 localhost:8000 - {'✅ متاح' if result_local == 0 else '❌ غير متاح'}")
        print(f"   🌐 0.0.0.0:8000 - {'✅ متاح' if result_all == 0 else '❌ غير متاح'}")
        
        return result_local == 0
        
    except Exception as e:
        print(f"   ❌ خطأ في فحص المنفذ: {e}")
        return False

def check_firewall_rules():
    """فحص قواعد Firewall"""
    print("\n🔥 فحص قواعد Windows Firewall...")
    
    try:
        if platform.system() == "Windows":
            # فحص قواعد Firewall
            result = subprocess.run([
                'netsh', 'advfirewall', 'firewall', 'show', 'rule', 
                'name=all', 'dir=in', 'protocol=tcp', 'localport=8000'
            ], capture_output=True, text=True, timeout=10)
            
            if "8000" in result.stdout:
                print("   ✅ توجد قواعد Firewall للمنفذ 8000")
            else:
                print("   ❌ لا توجد قواعد Firewall للمنفذ 8000")
                print("   💡 شغل fix_firewall.bat كمدير لإضافة القواعد")
                
        else:
            print("   ⚠️ فحص Firewall متاح فقط على Windows")
            
    except Exception as e:
        print(f"   ❌ خطأ في فحص Firewall: {e}")

def get_network_interfaces():
    """الحصول على واجهات الشبكة"""
    print("\n🔌 فحص واجهات الشبكة...")
    
    interfaces = []
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['ipconfig'], capture_output=True, text=True, encoding='cp1256')
            lines = result.stdout.split('\n')
            
            current_adapter = ""
            for line in lines:
                line = line.strip()
                if "adapter" in line.lower() or "محول" in line:
                    current_adapter = line
                elif "IPv4" in line or "عنوان IPv4" in line:
                    ip = line.split(':')[-1].strip()
                    if ip and ip != "127.0.0.1" and not ip.startswith("169.254"):
                        interfaces.append({
                            'name': current_adapter,
                            'ip': ip
                        })
                        print(f"   📡 {current_adapter}: {ip}")
                        
    except Exception as e:
        print(f"   ❌ خطأ في الحصول على واجهات الشبكة: {e}")
    
    return interfaces

def test_server_binding():
    """اختبار ربط الخادم"""
    print("\n🧪 اختبار ربط الخادم...")
    
    try:
        # إنشاء خادم اختبار
        test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # اختبار الربط على جميع الواجهات
        test_socket.bind(('0.0.0.0', 8001))  # منفذ مختلف لتجنب التعارض
        test_socket.listen(1)
        
        print("   ✅ يمكن ربط الخادم على جميع الواجهات")
        test_socket.close()
        
        return True
        
    except Exception as e:
        print(f"   ❌ خطأ في ربط الخادم: {e}")
        return False

def ping_test(ip):
    """اختبار ping"""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['ping', '-n', '1', ip], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        else:
            result = subprocess.run(['ping', '-c', '1', ip], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
    except:
        return False

def check_django_settings():
    """فحص إعدادات Django"""
    print("\n⚙️ فحص إعدادات Django...")
    
    try:
        import os
        import sys
        
        # إضافة مسار المشروع
        sys.path.append(os.getcwd())
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'abu_alaa_project.settings')
        
        import django
        django.setup()
        
        from django.conf import settings
        
        print(f"   📋 ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
        print(f"   🐛 DEBUG: {settings.DEBUG}")
        
        if '*' in settings.ALLOWED_HOSTS or '0.0.0.0' in settings.ALLOWED_HOSTS:
            print("   ✅ ALLOWED_HOSTS مُعد بشكل صحيح")
        else:
            print("   ❌ ALLOWED_HOSTS يحتاج تحديث")
            print("   💡 أضف '*' أو '0.0.0.0' إلى ALLOWED_HOSTS")
            
    except Exception as e:
        print(f"   ❌ خطأ في فحص إعدادات Django: {e}")

def start_test_server():
    """بدء خادم اختبار"""
    print("\n🚀 بدء خادم اختبار...")
    
    try:
        import http.server
        import socketserver
        
        class TestHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                
                html = """
                <!DOCTYPE html>
                <html dir="rtl">
                <head>
                    <meta charset="UTF-8">
                    <title>اختبار الاتصال - محلات أبو علاء</title>
                    <style>
                        body { font-family: Arial; text-align: center; padding: 50px; }
                        .success { color: green; font-size: 24px; }
                    </style>
                </head>
                <body>
                    <h1 class="success">✅ الاتصال يعمل بنجاح!</h1>
                    <p>نظام محلات أبو علاء - اختبار الشبكة</p>
                    <p>الوقت: {}</p>
                </body>
                </html>
                """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                
                self.wfile.write(html.encode('utf-8'))
        
        # بدء الخادم على منفذ 8001
        with socketserver.TCPServer(("0.0.0.0", 8001), TestHandler) as httpd:
            print("   🌐 خادم الاختبار يعمل على: http://0.0.0.0:8001")
            print("   📱 جرب الوصول من جهاز آخر: http://[IP]:8001")
            print("   ⏹️ اضغط Ctrl+C للإيقاف")
            
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n   ⏹️ تم إيقاف خادم الاختبار")
                
    except Exception as e:
        print(f"   ❌ خطأ في بدء خادم الاختبار: {e}")

def comprehensive_diagnosis():
    """تشخيص شامل"""
    print("="*60)
    print("🔍 تشخيص شامل لمشاكل الوصول الشبكي")
    print("Comprehensive Network Access Diagnosis")
    print("="*60)
    
    # 1. فحص ربط المنفذ
    port_ok = check_port_binding()
    
    # 2. فحص واجهات الشبكة
    interfaces = get_network_interfaces()
    
    # 3. فحص قواعد Firewall
    check_firewall_rules()
    
    # 4. فحص إعدادات Django
    check_django_settings()
    
    # 5. اختبار ربط الخادم
    binding_ok = test_server_binding()
    
    print("\n" + "="*60)
    print("📋 ملخص التشخيص:")
    print("="*60)
    
    print(f"🔌 ربط المنفذ: {'✅ يعمل' if port_ok else '❌ لا يعمل'}")
    print(f"🌐 ربط الخادم: {'✅ يعمل' if binding_ok else '❌ لا يعمل'}")
    print(f"📡 واجهات الشبكة: {'✅ متاحة' if interfaces else '❌ غير متاحة'}")
    
    print("\n🔧 الحلول المقترحة:")
    print("-" * 30)
    
    if not port_ok:
        print("❌ الخادم لا يعمل:")
        print("   💡 شغل: python server_manager.py")
        print("   💡 أو: start_server_network.bat")
    
    print("🔥 إعدادات Firewall:")
    print("   💡 شغل fix_firewall.bat كمدير")
    print("   💡 أو أضف المنفذ 8000 يدوياً في Windows Firewall")
    
    if interfaces:
        print(f"\n📱 للاختبار من الهاتف:")
        for interface in interfaces:
            print(f"   🔗 http://{interface['ip']}:8000")
    
    print("\n🧪 لاختبار الاتصال:")
    print("   💡 شغل: python diagnose_network.py test")

def main():
    """الدالة الرئيسية"""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "test":
            start_test_server()
        elif command == "ping":
            ip = input("أدخل IP للاختبار: ")
            result = ping_test(ip)
            print(f"Ping {ip}: {'✅ نجح' if result else '❌ فشل'}")
        elif command == "help":
            print("🔧 أداة تشخيص الشبكة - محلات أبو علاء")
            print("="*50)
            print("الاستخدام:")
            print("  python diagnose_network.py       - تشخيص شامل")
            print("  python diagnose_network.py test  - بدء خادم اختبار")
            print("  python diagnose_network.py ping  - اختبار ping")
            print("  python diagnose_network.py help  - عرض المساعدة")
        else:
            print(f"❌ أمر غير معروف: {command}")
    else:
        comprehensive_diagnosis()

if __name__ == "__main__":
    main()
