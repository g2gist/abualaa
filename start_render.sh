#!/bin/bash

# Render startup script
echo "🚀 Starting Abu Alaa CRM on Render..."

# Run migrations
echo "📊 Running database migrations..."
python manage.py migrate --noinput

# Create superuser if not exists
echo "👤 Creating superuser..."
python manage.py shell << 'EOF'
from django.contrib.auth.models import User

# إنشاء المستخدم الأساسي
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@abualaa.com', 'admin123')
    print('✅ Admin user created: admin/admin123')
else:
    # تحديث كلمة المرور إذا كان موجود
    user = User.objects.get(username='admin')
    user.set_password('admin123')
    user.save()
    print('✅ Admin password updated: admin/admin123')

# إنشاء مستخدم المدير
if not User.objects.filter(username='manager').exists():
    User.objects.create_superuser('manager', 'manager@abualaa.com', 'manager123')
    print('✅ Manager user created: manager/manager123')

print('🎉 All users ready!')
EOF

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start server
echo "🌐 Starting Django server..."
python manage.py runserver 0.0.0.0:$PORT
