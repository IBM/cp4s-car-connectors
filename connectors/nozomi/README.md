# Nozomi Vantage-CAR

Nozomi Vantage CAR Connector

```
I.   SUMMARY
II.  PREREQUISITES
III. INSTALLATION
IV.  EXAMPLE USAGE (command line)
V.   INITIAL IMPORT
VI.  INCREMENTAL IMPORT
```

I. SUMMARY:
-----------------------------------------------------------------
Nozomi Networks is a cybersecurity provider specializing in industrial control systems(ICS), operational technology(OT)
and Internet of things(IoT) security. Nozomi networks services includes Focused ICS/OT Security, Comprehensive
Visibility, Threat Detection and Response. Nozomi Networks Vantage is a SaaS solution that scales security monitoring
and visibility for large multi-site enterprises, while offering the cost benefits and flexibility of a cloud-hosted
solution

Site:   ```https://www.nozominetworks.com/```

II. PREREQUISITES:
-----------------------------------------------------------------
Python == 3.9.7 (greater than 3.9.x may work, less than probably will not; neither is tested)

**Nozomi Networks - Endpoints**

Use login endpoint to login to Nozomi and get the bearer token.

| API Category |     Endpoint      |                  Usage                   |
|:------------:|:-----------------:|:----------------------------------------:|
|    login     | /api/open/sign_in | Get bearer token to make Query API calls |

Query Endpoint APIs to get the Asset, Vulnerability, Application, Sensor details.

| API Category  |                  Query                   |                                                Usage                                                |
|:-------------:|:----------------------------------------:|:---------------------------------------------------------------------------------------------------:|
|     Asset     |     /api/open/query/do?query=assets      |                                        Get details on Assets                                        |
|     Node      |      /api/open/query/do?query=nodes      |                     Get details of assets IP address and associated Mac address                     |
|  Application  | /api/open/query/do?query=asset_softwares |                                 Get details of softwares on assets                                  |
|               |  /api/open/query/do?query=software_list  | Get details of softwares cpes on the environment, cpes helps to map vulnerabilities for application |
| Vulnerability |    /api/open/query/do?query=asset_cve    |                                   Get details on Vulnerabilities                                    |
|               |  /api/open/query/do?query=vulnerability  |    Helps to filter the vulnerabilities based on status and resolved time for incremental delete     |
|    Sensors    |     /api/open/query/do?query=sensors     |   Get the geo-location of sensor, will be mapped to assets geolocation which connected to sensor    |

**Authentication:**

Nozomi Networks suggests dedicated users with minimal permissions (RBAC) necessary to access the required table.

Steps to create an API key [OpenAPI Keys](https://technicaldocs.nozominetworks.com/users/open_api_keys.html):

1. Add local user with Group role as
   ‘Observer’"[(Users and Groups )](https://help.vantage.nozominetworks.io/docs/users-groups-overview)
2. Login into Vantage console as local user . From console click on ‘user Icon’ -> Profile.
3. Under profile, Click on API keys.
4. Provide the Description, Allowed Ips, and Organization details in section ‘Generate new API Key’.
5. Click on Generate button, copy the Key Name and Key Token values

**Mappings**

The following table shows the Connected Assets and Risk connector to Nozomi Query Asset Response data mapping.

|  CAR vertex/edge  |     CAR field      |  Data source field  |
|:-----------------:|:------------------:|:-------------------:|
|       Asset       |        name        |        name         |
|                   |    external_id     |         id          |
|                   |     asset_type     |        type         |
|                   |    description     |    product_name     |
|         	         |        risk        |        risk         |
|                   |      category      | technology_category |
|                   |       vendor       |       vendor        |
|                   | last_activity_time | last_activity_time  |
|     ipaddress     |        _key        |         ip          |
|    macaddress     |        _key        |     mac_address     |
|    application    |        name        |   os_or_firmware    |
|                   |    external_id     |   os_or_firmware    |
|                   |       is_os        |        true         |
|  asset_ipaddress  | _from_external_id  |         id          |
|                   |        _to         |         ip          |
| asset_macaddress  | _from_external_id  |         id          |
|                   |        _to         |     mac_address     |
| asset_application | _from_external_id  |         id          |
|                   |  _to_external_id   |   os_or_firmware    |

The following table shows the Connected Assets and Risk connector to Nozomi Query Node Response data mapping.

|   CAR vertex/edge    | CAR field | Data source field |
|:--------------------:|:---------:|:-----------------:|
| ipaddress_macaddress |   _from   |        ip         |
|                      |    _to    |    mac_address    |

The following table shows the Connected Assets and Risk connector to Nozomi Query Sensors Response data mapping.

|    CAR vertex/edge    |     CAR field     |        Data source field        |
|:---------------------:|:-----------------:|:-------------------------------:|
|      geolocation      |    external_id    | latitude:longitude (or) country |
|                       |     latitude      |            latitude             |
|                       |     longitude     |            longitude            |
|                       |      region       |             country             |
|   asset_geolocation   | _from_external_id |      asset response -> id       |
|                       |  _to_external_id  | latitude:longitude (or) country |
| ipaddress_geolocation |       _from       |      asset response -> ip       |
|                       |  _to_external_id  | latitude:longitude (or) country |

The following table shows the Connected Assets and Risk connector to Nozomi Query asset_softwares and software_list
Response data mapping.

|  CAR vertex/edge  |     CAR field     |       Data source field       |
|:-----------------:|:-----------------:|:-----------------------------:|
|    application    |       name        |            product            |
|                   |    external_id    |    product + ':' + version    |
|                   |       is_os       |             False             |
|                   |        cpe        | software_list response -> cpe |
|                   |    description    |    product + ':' + version    |
| asset_application | _from_external_id |     asset response -> id      |
|                   |  _to_external_id  |    product + ':' + version    |

The following table shows the Connected Assets and Risk connector to Nozomi Query Vulnerability Response
data mapping.

|   CAR vertex/edge   |      CAR field      | Data source field |
|:-------------------:|:-------------------:|:-----------------:|
|    vulnerability    |        name         |        cve        |
|                     |     external_id     |        id         |
|                     |     description     |     cwe_name      |
|                     |     base_score      |     cve_score     |
|                     |    disclosed_on     | cve_creation_time |
|                     |     updated_on      |  cve_update_time  |
|         		          | external_references |    references     |
| asset_vulnerability |  _from_external_id  |     asset_id      |
|                     |   _to_external_id   |        id         |

III. INSTALLATION:
-----------------------------------------------------------------

- Requirements.txt file attached.

IV. EXAMPLE USAGE (command line):
-----------------------------------------------------------------

```Usage: app.py [arguments]```

required arguments in command line:

```
positional arguments:
-host               :Nozomi Vantage API base URL
-port               :Nozomi Vantage API listening Port
-key_name           :API Key Name required for data source authentication
-key_token          :API Key Token required for data source authentication

optional arguments:
-data_retention_period   :Data retention period for data source (in days)
-d                  :run code in debug mode

suppressed arguments:
-working_dir        :working directory
-source             :data source
```

Update Nozomi configuration details in 'nozomi_config.json`

### Setup Details

Please follow the mentioned steps,

I. Cloning repository from GitHub

Link: `````https://github.com/IBM/cp4s-car-connectors.git`````

    - Use the PAT token as authentication password for cloning the same to the Linux filesystem using the “git clone” command or download the source code as a zip file.

II. Setting PYTHONPATH permanently.

    For Linux,
    -  Open the file ~/.bashrc in your text editor – e.g. vi ~/.bashrc;
    -  Add the following line to the end: (change according to your working dorectory)
    export PYTHONPATH= /home/testadmin/cp4s-car-connectors/connectors/nozomi
    Save the file.
    -  Close your terminal application;
    -  Start your terminal application again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/cp4s-car-connectors/connectors/nozomi/.
    
    For Mac,
    - Open Terminal.app;
    Open the file ~/.bash_profile in your text editor – e.g. atom ~/.bash_profile;
    - Add the following line to the end:
    export PYTHONPATH="/home/testadmin/cp4s-car-connectors/connectors/nozomi/"
    Save the file.
    -	Close Terminal.app;
    -	Start Terminal.app again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/cp4s-car-connectors/connectors/nozomi/.

### Command To Run the script

1. goto the connector folder ` <cp4s-car-connectors/connectors/nozomi>`

2. To run the initial import which is the full dump of the data source assets, run this command:
   ` python app.py -host <nozomi base url> -key_name <Nozomi user API Key Name> -key_token <Nozomi user API Key Token>  -car-service-url <"BASE_URL"> -car-service-key <"api_key"> -car-service-password <"password"> -source "<Nozomi>"`

3. To run the incremental update, create a cronjob that runs, the command to run is:
   ` python app.py -host <nozomi base url> -key_name <Nozomi user API Key Name> -key_token <Nozomi user API Key Token>  -retention_period <Data Source retention period> -car-service-url <"BASE_URL"> -car-service-key <"api_key"> -car-service-password <"password"> -source "<Nozomi>"`

V. INITIAL IMPORTS
-----------------------------------------------------------------
When we run the connector First time. It loads all the asset and their entities available from the source into CAR
database.

VI. INCREMENTAL IMPORT
-----------------------------------------------------------------

- Incremental Import are expected to be based on a time-range and hence we query the data source with time interval
  filter after initial import was run.
- Asset incremental create or update are filtered using ‘last_active_time > last import time’. Creates new nodes or
  edges if asset is new, else updates the existing nodes/edges in CAR.
- To delete the Asset nodes , get the asset and associated relation details from CAR DB which are last modified before
  the configured retention period.
- Complete list of asset_software and software_list are fetched from data source. Creates new nodes and edges if
  application is new, else updates the existing nodes in CAR.
- asset_application edge will be disabled if applications are removed from asset. To get the applications removed from
  the asset, get the asset_application edge details from CAR DB, compares with application details from data source. If
  application present in car and not available in data source marked for disable.
- Vulnerability incremental creates are filtered using ‘time > last import time’. Creates new vulnerability node and
  asset_vulnerability edge.
- To delete vulnerability nodes, filter the vulnerabilities resolved using 'closed_time> last import time’ and
  ‘status=resolved’. 