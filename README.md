# Reference implementation of a CAR connector

## Server

The server part is a Python Django application which implements a simple Asset model.

Server setup:

```
pip install -r requirements.txt
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin')"
python3 manage.py populate
```


Running the server:

```
python3 manage.py runserver
```

Use server UI to modify the model (create/delete/modify Asset model items): http://localhost:8000/admin/
Login credentials are admin/admin

Generate a model of a pre-defined size: http://localhost:8000/admin/assets/assetmodelsize/1/change/
Set the "size" to some number and click "Save" button.


## Connector

Install python dependances from "connector" folder
```
pip install -r requirements.txt
```

Running the connector:
```
python3 app.py -server=http://localhost:8000 -username=admin -password=admin -car-service-url=<car-service-url> -car-service-key=<car-service-key> -car-service-password=<car-service-password>

```
