"""
خدمة النسخ الاحتياطي للبيانات مع Google Drive
"""
import os
import pandas as pd
from datetime import datetime
from io import BytesIO
from django.conf import settings
from django.db.models import Q
from .models import Customer, Debt, Payment, Invoice, CompanySettings


class BackupService:
    """خدمة النسخ الاحتياطي"""
    
    def __init__(self):
        self.backup_folder = getattr(settings, 'BACKUP_FOLDER', 'backups')
        if not os.path.exists(self.backup_folder):
            os.makedirs(self.backup_folder)
    
    def create_backup_data(self):
        """إنشاء بيانات النسخة الاحتياطية"""
        backup_data = {}
        
        # بيانات العملاء
        customers_data = []
        for customer in Customer.objects.all():
            customers_data.append({
                'ID': customer.id,
                'الاسم': customer.name,
                'رقم الهاتف': customer.phone,
                'البريد الإلكتروني': customer.email or '',
                'العنوان': customer.address or '',
                'رقم الصفحة': customer.page_number or '',
                'إجمالي الديون': float(customer.total_debt),
                'المبلغ المتبقي': float(customer.remaining_debt),
                'تاريخ الإضافة': customer.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'تاريخ التحديث': customer.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        backup_data['العملاء'] = customers_data
        
        # بيانات الديون
        debts_data = []
        for debt in Debt.objects.select_related('customer').all():
            debts_data.append({
                'ID': debt.id,
                'العميل ID': debt.customer.id,
                'اسم العميل': debt.customer.name,
                'الوصف': debt.description,
                'المبلغ': float(debt.amount),
                'المبلغ المدفوع': float(debt.total_paid),
                'المبلغ المتبقي': float(debt.remaining_amount),
                'تاريخ الاستحقاق': debt.due_date.strftime('%Y-%m-%d'),
                'الحالة': debt.status,
                'وصف الحالة': debt.get_status_display(),
                'تاريخ الإنشاء': debt.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'تاريخ التحديث': debt.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        backup_data['الديون'] = debts_data
        
        # بيانات الدفعات
        payments_data = []
        for payment in Payment.objects.select_related('debt', 'debt__customer').all():
            payments_data.append({
                'ID': payment.id,
                'الدين ID': payment.debt.id,
                'العميل': payment.debt.customer.name,
                'المبلغ': float(payment.amount),
                'طريقة الدفع': payment.payment_method,
                'وصف طريقة الدفع': payment.get_payment_method_display(),
                'ملاحظات': payment.notes or '',
                'تاريخ الدفع': payment.payment_date.strftime('%Y-%m-%d'),
                'تاريخ الإنشاء': payment.created_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        backup_data['الدفعات'] = payments_data
        
        # بيانات الفواتير
        invoices_data = []
        for invoice in Invoice.objects.select_related('debt', 'debt__customer').all():
            invoices_data.append({
                'ID': invoice.id,
                'رقم الفاتورة': invoice.invoice_number,
                'الدين ID': invoice.debt.id,
                'العميل': invoice.debt.customer.name,
                'المبلغ': float(invoice.debt.amount),
                'تاريخ الإنشاء': invoice.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'تاريخ التحديث': invoice.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        backup_data['الفواتير'] = invoices_data
        
        # إعدادات الشركة
        settings_data = []
        for setting in CompanySettings.objects.all():
            settings_data.append({
                'ID': setting.id,
                'اسم الشركة': setting.company_name,
                'رقم الهاتف': setting.phone,
                'البريد الإلكتروني': setting.email,
                'العنوان': setting.address,
                'العملة': setting.currency,
                'شروط الفاتورة': setting.invoice_terms,
                'تاريخ الإنشاء': setting.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'تاريخ التحديث': setting.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            })
        backup_data['إعدادات_الشركة'] = settings_data
        
        return backup_data
    
    def create_excel_backup(self):
        """إنشاء ملف Excel للنسخة الاحتياطية"""
        backup_data = self.create_backup_data()
        
        # إنشاء اسم الملف مع التاريخ والوقت
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_abu_alaa_{timestamp}.xlsx'
        filepath = os.path.join(self.backup_folder, filename)
        
        # إنشاء ملف Excel
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for sheet_name, data in backup_data.items():
                if data:  # تأكد من وجود بيانات
                    df = pd.DataFrame(data)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return filepath, filename
    
    def create_backup_stream(self):
        """إنشاء stream للنسخة الاحتياطية للرفع المباشر"""
        backup_data = self.create_backup_data()
        
        # إنشاء ملف Excel في الذاكرة
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for sheet_name, data in backup_data.items():
                if data:  # تأكد من وجود بيانات
                    df = pd.DataFrame(data)
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        output.seek(0)
        return output


class GoogleDriveService:
    """خدمة Google Drive"""
    
    def __init__(self):
        self.credentials_file = getattr(settings, 'GOOGLE_DRIVE_CREDENTIALS', None)
        self.folder_id = getattr(settings, 'GOOGLE_DRIVE_FOLDER_ID', None)
        self.service = None
        
    def authenticate(self):
        """المصادقة مع Google Drive"""
        try:
            from googleapiclient.discovery import build
            from google.oauth2.service_account import Credentials
            
            if not self.credentials_file or not os.path.exists(self.credentials_file):
                raise Exception("ملف المصادقة غير موجود")
            
            credentials = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            
            self.service = build('drive', 'v3', credentials=credentials)
            return True
            
        except Exception as e:
            print(f"خطأ في المصادقة: {e}")
            return False
    
    def upload_backup(self, file_stream, filename):
        """رفع النسخة الاحتياطية إلى Google Drive"""
        if not self.authenticate():
            return False, "فشل في المصادقة مع Google Drive"
        
        try:
            from googleapiclient.http import MediaIoBaseUpload
            
            # إعداد البيانات للرفع
            media = MediaIoBaseUpload(
                file_stream,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            
            # إعداد معلومات الملف
            file_metadata = {
                'name': filename,
                'parents': [self.folder_id] if self.folder_id else []
            }
            
            # رفع الملف
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink'
            ).execute()
            
            return True, {
                'file_id': file.get('id'),
                'filename': file.get('name'),
                'link': file.get('webViewLink')
            }
            
        except Exception as e:
            return False, f"خطأ في رفع الملف: {e}"
    
    def list_backups(self, limit=10):
        """عرض قائمة النسخ الاحتياطية"""
        if not self.authenticate():
            return []
        
        try:
            query = "name contains 'backup_abu_alaa_'"
            if self.folder_id:
                query += f" and '{self.folder_id}' in parents"
            
            results = self.service.files().list(
                q=query,
                orderBy='createdTime desc',
                pageSize=limit,
                fields="files(id,name,createdTime,size,webViewLink)"
            ).execute()
            
            return results.get('files', [])
            
        except Exception as e:
            print(f"خطأ في عرض النسخ الاحتياطية: {e}")
            return []
