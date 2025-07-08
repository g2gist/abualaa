# خدمة خادم محلات أبو علاء
# Abu Alaa Stores Server Service

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("install", "uninstall", "start", "stop", "restart", "status")]
    [string]$Action = "status"
)

$ServiceName = "AbuAlaaStoresServer"
$ServiceDisplayName = "Abu Alaa Stores CRM Server"
$ServiceDescription = "خادم نظام إدارة العملاء والديون - محلات أبو علاء"
$ServerPath = "Z:\crm"
$PythonPath = "python"
$ServerScript = "manage.py"

function Install-Service {
    Write-Host "تثبيت خدمة الخادم..." -ForegroundColor Green
    
    # إنشاء ملف الخدمة
    $ServiceScript = @"
import sys
import os
import subprocess
import time
import logging
from pathlib import Path

# إعداد المسارات
SERVER_PATH = r"$ServerPath"
PYTHON_PATH = "$PythonPath"
LOG_FILE = os.path.join(SERVER_PATH, "server.log")

# إعداد التسجيل
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

def run_server():
    """تشغيل خادم Django"""
    os.chdir(SERVER_PATH)
    
    while True:
        try:
            logging.info("بدء تشغيل خادم Django...")
            
            # تشغيل الخادم
            process = subprocess.Popen([
                PYTHON_PATH, "manage.py", "runserver", "0.0.0.0:8000"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # انتظار انتهاء العملية
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logging.error(f"خطأ في الخادم: {stderr}")
            else:
                logging.info("الخادم توقف بشكل طبيعي")
                
        except Exception as e:
            logging.error(f"خطأ في تشغيل الخادم: {e}")
        
        # انتظار 5 ثوان قبل إعادة التشغيل
        logging.info("إعادة تشغيل الخادم خلال 5 ثوان...")
        time.sleep(5)

if __name__ == "__main__":
    run_server()
"@

    # حفظ ملف الخدمة
    $ServiceScriptPath = Join-Path $ServerPath "server_service.py"
    $ServiceScript | Out-File -FilePath $ServiceScriptPath -Encoding UTF8
    
    # إنشاء ملف batch للخدمة
    $BatchScript = @"
@echo off
cd /d "$ServerPath"
python server_service.py
"@
    
    $BatchScriptPath = Join-Path $ServerPath "run_service.bat"
    $BatchScript | Out-File -FilePath $BatchScriptPath -Encoding ASCII
    
    # تثبيت الخدمة باستخدام sc
    $BinaryPath = "`"$BatchScriptPath`""
    
    try {
        sc.exe create $ServiceName binPath= $BinaryPath DisplayName= "$ServiceDisplayName" start= auto
        sc.exe description $ServiceName "$ServiceDescription"
        
        Write-Host "تم تثبيت الخدمة بنجاح!" -ForegroundColor Green
        Write-Host "اسم الخدمة: $ServiceName" -ForegroundColor Yellow
        Write-Host "لبدء الخدمة: .\server_service.ps1 -Action start" -ForegroundColor Yellow
    }
    catch {
        Write-Host "فشل في تثبيت الخدمة: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Uninstall-Service {
    Write-Host "إلغاء تثبيت خدمة الخادم..." -ForegroundColor Yellow
    
    try {
        Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
        sc.exe delete $ServiceName
        
        # حذف ملفات الخدمة
        $ServiceScriptPath = Join-Path $ServerPath "server_service.py"
        $BatchScriptPath = Join-Path $ServerPath "run_service.bat"
        
        if (Test-Path $ServiceScriptPath) { Remove-Item $ServiceScriptPath -Force }
        if (Test-Path $BatchScriptPath) { Remove-Item $BatchScriptPath -Force }
        
        Write-Host "تم إلغاء تثبيت الخدمة بنجاح!" -ForegroundColor Green
    }
    catch {
        Write-Host "فشل في إلغاء تثبيت الخدمة: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Start-ServerService {
    Write-Host "بدء تشغيل خدمة الخادم..." -ForegroundColor Green
    
    try {
        Start-Service -Name $ServiceName
        Write-Host "تم بدء تشغيل الخدمة بنجاح!" -ForegroundColor Green
        Get-ServiceStatus
    }
    catch {
        Write-Host "فشل في بدء تشغيل الخدمة: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Stop-ServerService {
    Write-Host "إيقاف خدمة الخادم..." -ForegroundColor Yellow
    
    try {
        Stop-Service -Name $ServiceName -Force
        Write-Host "تم إيقاف الخدمة بنجاح!" -ForegroundColor Green
        Get-ServiceStatus
    }
    catch {
        Write-Host "فشل في إيقاف الخدمة: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Restart-ServerService {
    Write-Host "إعادة تشغيل خدمة الخادم..." -ForegroundColor Blue
    
    Stop-ServerService
    Start-Sleep -Seconds 3
    Start-ServerService
}

function Get-ServiceStatus {
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
        
        if ($service) {
            Write-Host "حالة الخدمة: $($service.Status)" -ForegroundColor Cyan
            Write-Host "نوع البدء: $(sc.exe qc $ServiceName | Select-String 'START_TYPE')" -ForegroundColor Cyan
            
            # فحص المنفذ
            $port = netstat -an | Select-String ":8000"
            if ($port) {
                Write-Host "الخادم يعمل على المنفذ 8000 ✓" -ForegroundColor Green
            } else {
                Write-Host "الخادم لا يعمل على المنفذ 8000 ✗" -ForegroundColor Red
            }
        } else {
            Write-Host "الخدمة غير مثبتة" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "خطأ في فحص حالة الخدمة: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# تنفيذ الإجراء المطلوب
switch ($Action.ToLower()) {
    "install" { Install-Service }
    "uninstall" { Uninstall-Service }
    "start" { Start-ServerService }
    "stop" { Stop-ServerService }
    "restart" { Restart-ServerService }
    "status" { Get-ServiceStatus }
    default { 
        Write-Host "الإجراءات المتاحة: install, uninstall, start, stop, restart, status" -ForegroundColor Yellow
        Get-ServiceStatus
    }
}
