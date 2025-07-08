#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
مدير خادم محلات أبو علاء
Abu Alaa Stores Server Manager

هذا الملف يدير تشغيل خادم Django بشكل دائم مع إعادة التشغيل التلقائي
"""

import os
import sys
import time
import signal
import subprocess
import logging
import threading
from datetime import datetime
from pathlib import Path

# إعداد المسارات
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "server.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class ServerManager:
    """مدير الخادم"""
    
    def __init__(self):
        self.process = None
        self.running = False
        self.restart_count = 0
        self.max_restarts = 10
        self.restart_delay = 5
        
    def start_server(self):
        """بدء تشغيل خادم Django"""
        try:
            logger.info("🚀 بدء تشغيل خادم محلات أبو علاء...")
            
            # تغيير المجلد الحالي
            os.chdir(BASE_DIR)
            
            # تشغيل الخادم على جميع الواجهات
            self.process = subprocess.Popen([
                sys.executable, "manage.py", "runserver", "0.0.0.0:8000"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            logger.info(f"✅ تم بدء تشغيل الخادم بنجاح! PID: {self.process.pid}")
            logger.info("🌐 الخادم متاح على: http://localhost:8000")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في بدء تشغيل الخادم: {e}")
            return False
    
    def stop_server(self):
        """إيقاف الخادم"""
        if self.process:
            try:
                logger.info("⏹️ إيقاف الخادم...")
                self.process.terminate()
                self.process.wait(timeout=10)
                logger.info("✅ تم إيقاف الخادم بنجاح")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ إجبار إيقاف الخادم...")
                self.process.kill()
            except Exception as e:
                logger.error(f"❌ خطأ في إيقاف الخادم: {e}")
            finally:
                self.process = None
    
    def restart_server(self):
        """إعادة تشغيل الخادم"""
        logger.info("🔄 إعادة تشغيل الخادم...")
        self.stop_server()
        time.sleep(2)
        return self.start_server()
    
    def monitor_server(self):
        """مراقبة الخادم وإعادة تشغيله عند الحاجة"""
        while self.running:
            if self.process is None:
                if self.restart_count < self.max_restarts:
                    logger.info(f"🔄 محاولة إعادة التشغيل #{self.restart_count + 1}")
                    if self.start_server():
                        self.restart_count = 0
                    else:
                        self.restart_count += 1
                        logger.warning(f"⚠️ فشل في إعادة التشغيل. المحاولة التالية خلال {self.restart_delay} ثانية...")
                        time.sleep(self.restart_delay)
                else:
                    logger.error(f"❌ تم الوصول للحد الأقصى من محاولات إعادة التشغيل ({self.max_restarts})")
                    break
            else:
                # فحص حالة العملية
                poll = self.process.poll()
                if poll is not None:
                    logger.warning(f"⚠️ الخادم توقف مع الكود: {poll}")
                    self.process = None
                    self.restart_count += 1
                else:
                    # الخادم يعمل بشكل طبيعي
                    time.sleep(5)
    
    def run(self):
        """تشغيل مدير الخادم"""
        self.running = True
        
        # إعداد معالج الإشارات
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info("🎯 بدء تشغيل مدير خادم محلات أبو علاء")
        logger.info("📍 للإيقاف: اضغط Ctrl+C")
        
        try:
            # بدء تشغيل الخادم
            if self.start_server():
                # بدء مراقبة الخادم في خيط منفصل
                monitor_thread = threading.Thread(target=self.monitor_server)
                monitor_thread.daemon = True
                monitor_thread.start()
                
                # انتظار إيقاف الخادم
                while self.running:
                    time.sleep(1)
            else:
                logger.error("❌ فشل في بدء تشغيل الخادم")
                
        except KeyboardInterrupt:
            logger.info("⌨️ تم الإيقاف بواسطة المستخدم")
        except Exception as e:
            logger.error(f"❌ خطأ غير متوقع: {e}")
        finally:
            self.cleanup()
    
    def signal_handler(self, signum, frame):
        """معالج الإشارات"""
        logger.info(f"📡 تم استلام إشارة الإيقاف: {signum}")
        self.running = False
    
    def cleanup(self):
        """تنظيف الموارد"""
        logger.info("🧹 تنظيف الموارد...")
        self.running = False
        self.stop_server()
        logger.info("👋 تم إيقاف مدير الخادم")

def show_status():
    """عرض حالة الخادم"""
    try:
        import psutil
        import requests
        
        print("📊 حالة خادم محلات أبو علاء")
        print("=" * 40)
        
        # فحص العمليات
        django_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'python' in proc.info['name'].lower() and 'manage.py' in ' '.join(proc.info['cmdline']):
                    django_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if django_processes:
            print(f"✅ الخادم يعمل ({len(django_processes)} عملية)")
            for proc in django_processes:
                print(f"   PID: {proc.info['pid']}")
        else:
            print("❌ الخادم لا يعمل")
        
        # فحص المنفذ
        try:
            response = requests.get("http://localhost:8000", timeout=5)
            print(f"🌐 الخادم متاح على المنفذ 8000 (كود الاستجابة: {response.status_code})")
        except requests.exceptions.RequestException:
            print("❌ الخادم غير متاح على المنفذ 8000")
        
        # معلومات النظام
        print(f"💾 استخدام الذاكرة: {psutil.virtual_memory().percent}%")
        print(f"🖥️ استخدام المعالج: {psutil.cpu_percent()}%")
        
    except ImportError:
        print("⚠️ لعرض معلومات مفصلة، قم بتثبيت: pip install psutil requests")
        
        # فحص بسيط للمنفذ
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 8000))
        sock.close()
        
        if result == 0:
            print("✅ الخادم يعمل على المنفذ 8000")
        else:
            print("❌ الخادم لا يعمل على المنفذ 8000")

def main():
    """الدالة الرئيسية"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "status":
            show_status()
            return
        elif command == "help":
            print("🔧 أوامر مدير خادم محلات أبو علاء:")
            print("  python server_manager.py        - تشغيل الخادم")
            print("  python server_manager.py status - عرض حالة الخادم")
            print("  python server_manager.py help   - عرض هذه المساعدة")
            return
    
    # تشغيل مدير الخادم
    manager = ServerManager()
    manager.run()

if __name__ == "__main__":
    main()
