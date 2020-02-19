del assets\migrations\00*.py
del db.sqlite3
C:\Programs\Python37\python.exe manage.py makemigrations
C:\Programs\Python37\python.exe manage.py migrate
C:\Programs\Python37\python.exe manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin')"
C:\Programs\Python37\python.exe manage.py populate
