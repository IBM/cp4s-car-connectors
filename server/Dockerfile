FROM python:3.7

ADD . /asset-server

WORKDIR /asset-server

RUN pip install django
RUN pip install djangorestframework

EXPOSE 8000

CMD [ "python", "./manage.py",  "runserver", "0.0.0.0:8000" ]
