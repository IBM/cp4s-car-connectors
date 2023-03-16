# Reference implementation of a CAR connector

## Server

The server part is a Python Django application which implements a simple Asset model.

Server setup:

```
cd server
pip3 install -r requirements.txt
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

Install python dependencies
```
pip3 install -r requirements.txt
```

Running the connector:
```
python3 app.py -host <The url of the tanium data source> -access_token <Access token of the tanium data source> -car-service-key "<car-service-key>" -car-service-password "<car-service-password>" -car-service-url "<car-service-url>" -source tanium
```