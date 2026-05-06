web: python manage.py migrate && python create_admin.py && gunicorn ecommerce.wsgi --bind 0.0.0.0:$PORT --workers 3 --max-requests 1000 --max-requests-jitter 50
