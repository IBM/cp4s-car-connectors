Pre-requisite:
1. docker
2. docker-compose
3. Access to image repository; for requesting access to CAR image contact danny.elliott@ibm.com or omkar.g.gurav@ibm.com

Steps to run CAR service:
1. Login to docker registry with the given credentials
```
docker login -u="<username>" -p="<password>" quay.io
```

2. Run the CAR service and its dependencies using docker compose car-deploy.yaml file as follows:
```
docker-compose -f ./car-deploy.yaml up -d
```