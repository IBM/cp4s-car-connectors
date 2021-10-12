del assets\migrations\00*.py
del db.sqlite3
%PYTHON3% manage.py makemigrations
%PYTHON3% manage.py migrate
%PYTHON3% manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin')"
%PYTHON3% manage.py populate
