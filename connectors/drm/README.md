# Reference documentation of a DRM CAR connector

## Connector

Download DRM CAR connector either using 'git clone' or download and extract zip
```
https://github.ibm.com/IBM-Data-Risk-Manager/RiskAppCARConnector.git
```
Make sure that the car-framework git submodule is initialized, This step is needed only when drm-car-connector is loaded using 'git clone':
```
git submodule update --init --recursive --remote -f
```

Install pre-requisite modules required for running DRM CAR Connector

Ensure Latest Python or Python3 and pip or pip3 is installed on system

Once Python and pip installation is successful, Install below packages

```
pip install -r requirements.txt
```
Running DRM CAR connector:
```
python3 app.py -tenantUrl=https:/<IBM Security Verify tenant URL> -username=<username for tenant> -password=<password for tenant> -car-service-url=<car-service-url> -car-service-key=<car-service-key>  -car-service-password=<car-service-password>  -pageSize=<pagesize>  -source=<source name>

Details about arguments :

tenantUrl - This is IBM Security Verify tenant URL, It is mandatory parameter
username - username for IBM Security Verify tenant, It is mandatory parameter
password - password for IBM Security Verify tenant, It is mandatory parameter
pageSize - pageSize specify records per page
source - This is unique String which need to passed to differentiate from other sources, It is Mandatory parameter
car-service-url - This is CAR Server URL , It is mandatory parameter
car-service-key - This is API key needed to access CAR API, It is mandatory parameter
car-service-password - This is APIkey password needed to access CAR API, It is mandatory parameter
forceFullImport - This is optional parameter, pass this flag only when we want to attempt force full import eg: -forceFullImport=true

```
