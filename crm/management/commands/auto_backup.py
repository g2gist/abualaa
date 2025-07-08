"""
أمر Django لإجراء نسخ احتياطي تلقائي
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from crm.backup_service import BackupService, GoogleDriveService
import os


class Command(BaseCommand):
    help = 'إنشاء نسخة احتياطية تلقائية'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            default='local',
            choices=['local', 'google_drive'],
            help='نوع النسخة الاحتياطية (local أو google_drive)'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='حذف النسخ الاحتياطية القديمة (أكثر من 30 يوم)'
        )

    def handle(self, *args, **options):
        backup_type = options['type']
        cleanup = options['cleanup']
        
        self.stdout.write('بدء عملية النسخ الاحتياطي...')
        
        try:
            backup_service = BackupService()
            
            if backup_type == 'google_drive':
                # رفع إلى Google Drive
                drive_service = GoogleDriveService()
                
                # إنشاء النسخة الاحتياطية
                file_stream = backup_service.create_backup_stream()
                timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
                filename = f'backup_abu_alaa_{timestamp}.xlsx'
                
                # رفع إلى Google Drive
                success, result = drive_service.upload_backup(file_stream, filename)
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'تم إنشاء النسخة الاحتياطية ورفعها إلى Google Drive بنجاح!\n'
                            f'اسم الملف: {result["filename"]}\n'
                            f'الرابط: {result.get("link", "غير متوفر")}'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'فشل في رفع النسخة الاحتياطية: {result}')
                    )
                    
            else:
                # حفظ محلي
                filepath, filename = backup_service.create_excel_backup()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'تم إنشاء النسخة الاحتياطية بنجاح!\n'
                        f'المسار: {filepath}'
                    )
                )
            
            # تنظيف النسخ القديمة إذا طُلب ذلك
            if cleanup:
                self.cleanup_old_backups(backup_service)
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'خطأ في إنشاء النسخة الاحتياطية: {e}')
            )

    def cleanup_old_backups(self, backup_service):
        """حذف النسخ الاحتياطية القديمة"""
        import glob
        from datetime import datetime, timedelta
        
        self.stdout.write('بدء تنظيف النسخ الاحتياطية القديمة...')
        
        # حذف الملفات المحلية الأقدم من 30 يوم
        backup_pattern = os.path.join(backup_service.backup_folder, 'backup_abu_alaa_*.xlsx')
        backup_files = glob.glob(backup_pattern)
        
        cutoff_date = datetime.now() - timedelta(days=30)
        deleted_count = 0
        
        for file_path in backup_files:
            try:
                file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                if file_time < cutoff_date:
                    os.remove(file_path)
                    deleted_count += 1
                    self.stdout.write(f'تم حذف: {os.path.basename(file_path)}')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'خطأ في حذف {file_path}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'تم حذف {deleted_count} ملف قديم')
        )
