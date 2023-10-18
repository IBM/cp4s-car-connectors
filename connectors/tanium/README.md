## Tanium pre-req

Modules: Intereac, Asset, Deploy, Discover and Benchmark
Packages: Client Management, Core ADQuery Content, and API Gateway

API token: https://docs.tanium.com/platform_user/platform_user/console_api_tokens.html?Highlight=api+token&cloud=false
GraphQL qurery: https://developer.tanium.com/site/global/apis/graphql/spectaql/index.gsp#definition-Endpoint

## Connector

Install python dependencies
```
pip3 install -r requirements.txt
```

Running the connector:
```
python3 app.py -host <The url of the tanium data source> -access_token <Access token of the tanium data source> -car-service-key "<car-service-key>" -car-service-password "<car-service-password>" -car-service-url "<car-service-url>" -source tanium
```

## Mappings

|  CAR vertex/edge  |   CAR field   |  Data source field  |
|  :------------:    |:---------------:| :-----:|
| asset | external_id | id |
|       | name  | manufacturer + "," + name |
|       | first_seen | eidFirstSeen |
|       | last_seen | eidLastSeen |
|       | risk | risk -> totalScore / 100 |
| ipaddress | _key | ipAddress |
| asset_ipaddress | _from_external_id | id |
|                 | _to | ipaddress/ + ipAddress |
| macaddress | _key | macAddresses |
| asset_macaddress | _from_external_id | id |
|                 | _to | macaddress/ + ipAddress |
| ipaddress_macaddress | _from | ipaddress/ + ipAddress |
|                 | _to | macaddress/ + ipAddress |
| hostname | _key | domainName |
| asset_hostname | _from_external_id | id |
|                 | _to | hostname/ + domainName |
| account | external_id | primaryUser -> email |
|       | name  | primaryUser -> name |
| asset_account | _from_external_id | id |
|                 | _to_external_id | account/ + primaryUser -> email |
| user | external_id | primaryUser -> email |
|      | fullname  | primaryUser -> name |
|      | email | primaryUser -> email |
|      | department | primaryUser -> department |
| user_account | _from_external_id | primaryUser -> email |
|                 | _to_external_id | account/ + primaryUser -> email |
| application (os) | external_id | os -> name |
|             | name  | os -> name |
|             | is_os  | True |
| asset_application | _from_external_id | id |
|                 | _to_external_id | 'application/' + os -> name |
| application (deployedSoftwarePackages) | external_id | deployedSoftwarePackages -> id |
|             | name  | deployedSoftwarePackages -> vendor |
|             | description  | deployedSoftwarePackages -> vendor + deployedSoftwarePackages -> version |
|             | app_type  | "SoftwarePackages" |
| asset_application | _from_external_id | id |
|                 | _to_external_id | 'application/' + deployedSoftwarePackages -> id |
| application (installedApplications) | external_id | installedApplications -> name |
|             | name  | installedApplications -> name |
|             | description  | installedApplications -> name + installedApplications -> version |
|             | app_type  | "application" |
| asset_application | _from_external_id | id |
|                 | _to_external_id | 'application/' + installedApplications -> name |
| application (services) | external_id | services -> name |
|             | name  | services -> displayName |
|             | status  | services -> status |
|             | app_type  | "services" |
| asset_application | _from_external_id | id |
|                 | _to_external_id | 'application/' + services -> name |
| port | external_id | id |
|             | port_number  | discover -> openPorts -> port |
|             | protocol  | "N/A" |
| application_port | _from_external_id | id |
|                 | _to_external_id | id |
| ipaddress_port | _from | 'ipaddress/' + 'ipAddress' |
|                 | _to_external_id | id |