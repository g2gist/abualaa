#!/bin/bash

# Render startup script
echo "🚀 Starting Abu Alaa CRM on Render..."

# Run migrations
echo "📊 Running database migrations..."
python manage.py migrate --noinput

# Create superuser if not exists
echo "👤 Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@abualaa.com', 'admin123')
    print('✅ Superuser created: admin/admin123')
else:
    print('✅ Superuser already exists')
EOF

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start server
echo "🌐 Starting Django server..."
python manage.py runserver 0.0.0.0:$PORT
