"""
خدمة Google Drive للنسخ الاحتياطية
"""
import os
import json
from io import BytesIO
from django.conf import settings
from django.core.files.storage import default_storage


class GoogleDriveService:
    """خدمة Google Drive للنسخ الاحتياطية"""
    
    def __init__(self):
        self.service = None
        self.credentials_file = getattr(settings, 'GOOGLE_DRIVE_CREDENTIALS', None)
        self.folder_id = getattr(settings, 'GOOGLE_DRIVE_FOLDER_ID', None)
        
    def authenticate(self):
        """المصادقة مع Google Drive"""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.service_account import Credentials
            
            if not self.credentials_file:
                return False, "ملف المصادقة غير محدد في الإعدادات"
            
            # البحث عن ملف المصادقة
            credentials_path = None
            possible_paths = [
                self.credentials_file,
                os.path.join(settings.BASE_DIR, self.credentials_file),
                os.path.join(settings.BASE_DIR, 'credentials.json'),
                '/opt/render/project/src/credentials.json',  # مسار Render
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    credentials_path = path
                    break
            
            if not credentials_path:
                return False, f"ملف المصادقة غير موجود في المسارات: {possible_paths}"
            
            # تحميل المصادقة
            credentials = Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            
            self.service = build('drive', 'v3', credentials=credentials)
            return True, "تم الاتصال بنجاح"
            
        except Exception as e:
            return False, f"خطأ في المصادقة: {str(e)}"
    
    def upload_backup(self, file_content, filename):
        """رفع النسخة الاحتياطية إلى Google Drive"""
        success, message = self.authenticate()
        if not success:
            return False, message
        
        try:
            from googleapiclient.http import MediaIoBaseUpload
            
            # تحضير الملف للرفع
            if isinstance(file_content, str):
                file_stream = BytesIO(file_content.encode('utf-8'))
                mimetype = 'application/json'
            else:
                file_stream = file_content
                mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            
            media = MediaIoBaseUpload(file_stream, mimetype=mimetype)
            
            # إعداد معلومات الملف
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id] if self.folder_id else []
            }
            
            # رفع الملف
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink,size'
            ).execute()
            
            return True, {
                'file_id': file.get('id'),
                'filename': file.get('name'),
                'link': file.get('webViewLink'),
                'size': file.get('size', 0)
            }
            
        except Exception as e:
            return False, f"خطأ في رفع الملف: {str(e)}"
    
    def list_backups(self, limit=10):
        """عرض قائمة النسخ الاحتياطية"""
        success, message = self.authenticate()
        if not success:
            return []
        
        try:
            # البحث عن ملفات النسخ الاحتياطية
            query = "name contains 'backup_abu_alaa_'"
            if self.folder_id:
                query += f" and '{self.folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                orderBy='createdTime desc',
                pageSize=limit,
                fields="files(id,name,createdTime,size,webViewLink,mimeType)"
            ).execute()
            
            files = results.get('files', [])
            
            # تنسيق البيانات
            backups = []
            for file in files:
                backups.append({
                    'id': file.get('id'),
                    'name': file.get('name'),
                    'created_time': file.get('createdTime'),
                    'size': file.get('size', 0),
                    'link': file.get('webViewLink'),
                    'type': file.get('mimeType')
                })
            
            return backups
            
        except Exception as e:
            print(f"خطأ في عرض النسخ الاحتياطية: {str(e)}")
            return []
    
    def delete_backup(self, file_id):
        """حذف نسخة احتياطية"""
        success, message = self.authenticate()
        if not success:
            return False, message
        
        try:
            self.service.files().delete(fileId=file_id).execute()
            return True, "تم حذف الملف بنجاح"
            
        except Exception as e:
            return False, f"خطأ في حذف الملف: {str(e)}"
    
    def test_connection(self):
        """اختبار الاتصال مع Google Drive"""
        success, message = self.authenticate()
        if not success:
            return False, message
        
        try:
            # اختبار بسيط - الحصول على معلومات المستخدم
            about = self.service.about().get(fields="user").execute()
            user_email = about.get('user', {}).get('emailAddress', 'غير معروف')
            
            return True, f"متصل بنجاح كـ: {user_email}"
            
        except Exception as e:
            return False, f"فشل في الاختبار: {str(e)}"


def setup_google_drive():
    """إعداد Google Drive - دليل للمستخدم"""
    instructions = """
    خطوات إعداد Google Drive API:
    
    1. اذهب إلى Google Cloud Console:
       https://console.cloud.google.com/
    
    2. أنشئ مشروع جديد أو اختر مشروع موجود
    
    3. فعل Google Drive API:
       - اذهب إلى "APIs & Services" > "Library"
       - ابحث عن "Google Drive API"
       - اضغط "Enable"
    
    4. أنشئ Service Account:
       - اذهب إلى "APIs & Services" > "Credentials"
       - اضغط "Create Credentials" > "Service Account"
       - أدخل اسم الحساب
       - اضغط "Create and Continue"
    
    5. حمل ملف JSON:
       - في صفحة Service Account
       - اضغط على الحساب المُنشأ
       - اذهب إلى "Keys"
       - اضغط "Add Key" > "Create New Key"
       - اختر "JSON"
       - احفظ الملف باسم "credentials.json"
    
    6. أنشئ مجلد في Google Drive:
       - اذهب إلى Google Drive
       - أنشئ مجلد جديد للنسخ الاحتياطية
       - انسخ ID المجلد من الرابط
    
    7. شارك المجلد مع Service Account:
       - اضغط بالزر الأيمن على المجلد
       - اختر "Share"
       - أضف email الـ Service Account
       - أعطه صلاحية "Editor"
    
    8. أضف الإعدادات في settings.py:
       GOOGLE_DRIVE_CREDENTIALS = 'path/to/credentials.json'
       GOOGLE_DRIVE_FOLDER_ID = 'your_folder_id'
    """
    
    return instructions
