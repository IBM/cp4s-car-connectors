# CrowdStrike-Falcon-CAR

CrowdStrike Falcon CAR Connector
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
CrowdStrike Falcon Platform provides comprehensive visibility and protection across critical areas of risk: endpoints, workloads, data and security.

Site:   ```https://www.crowdstrike.com/```

II. PREREQUISITES:
-----------------------------------------------------------------
Python == 3.9.7 (greater than 3.9.x may work, less than probably will not; neither is tested)

**CrowdStrike Falcon - Asset & Vulnerability**

| FalconPy module | Method Name | Usage |
|  :------------:   | :------------:| :----------:|
| Discover | get_hosts( ) | Get details on Assets |
|          | get_accounts( ) | Get details on Accounts |
|          | get_applications( ) | Get details on Applications |
| Spotlight | get_vulnerabilities( ) | Get details on Vulnerabilities |

**Authentication:**

Users with the Falcon Administrator role can create new API clients from the API Clients and Keys page of the console.

Steps to create an API client:
1. Create API clients to grant various levels of API access for different purposes.
2. On the API Clients and Keys page (Support and resources > Resources and tools > API Clients and Keys), click Create API client.
3. Enter details to define your API client:
4. Client Name (required)
5. Description (optional)
6. API Scopes (required)
7. Select the Read and/or Write boxes next to a scope to enable access to its endpoints.
8. At least one scope must be assigned.
9. Click Create to save the API client and generate the client ID and secret.

**Mappings**

The following table shows the Connected Assets and Risk connector to Falcon  Discover Asset Response data mapping.

|  CAR vertex/edge  |   CAR field   |  Data source field  |
|  :------------:   | :------------:| :----------:|
| Asset | name | Host -> hostname |
|       | external_id | Host -> id |
|       | asset_type | Host -> form_factor |
|       | description | Host -> Product_type_desc |
| hostname | host_name | Host -> hostname |
|          | _key | Host -> hostname |
| ipaddress | _key | Host -> external_ip OR Host -> network_interfaces -> local_ip |
|           | regin_id | Host -> city, country |
| macaddress | _key | Host -> network_interfaces -> mac_address |
|            | interface | Host -> network_interfaces -> interface_alias |
| geolocation | external_id | Host -> city, country |
|            | region  | Host -> city, country |
| asset_hostname | _from_external_id | Host -> id |
|            | _to | Host -> hostname |
| asset_geolocation | _from_external_id | Host -> id |
|            | _to_external_id | Host -> city, country |
| asset_ipaddress | _from_external_id | Host -> id |
|            | _to | Host -> external_ip OR Host -> local_ip_addresses |
| asset_macaddress | _from_external_id | Host -> id |
|            | _to | Host -> network_interfaces -> mac_address |
| ipaddress_macaddress | _from | Host -> external_ip OR Host -> local_ip_addresses |
|            | _to | Host -> network_interfaces -> mac_address |
| ipaddress_geolocation | _from | Host -> external_ip OR Host -> local_ip_addresses |
|            | _to_external_id | Host -> city, country |
| ipaddress_hostname | _from | Host -> external_ip OR Host -> local_ip_addresses |
|            | _to | Host -> hostname |

The following table shows the Connected Assets and Risk connector to Falcon  Discover Application Response data mapping.

|  CAR vertex/edge  |   CAR field   |  Data source field  |
|  :------------:   | :------------: | :----------:|
| application | name | App -> name OR App -> host -> os_version |
|             | external_id | App -> id OR App -> host -> os_version + kernal_version |
|             | is_os | False OR True |
|             | owner | App -> vendor |
|             | last_access_time | App -> last_updated_timestamp |
| asset_application | _from_external_id | Host -> id |
|            | _to_external_id | App -> id OR App -> host -> os_version + kernal_version |

The following table shows the Connected Assets and Risk connector to Falcon  Discover Account Response data mapping.

|  CAR vertex/edge  |   CAR field   |  Data source field  |
|  :------------:   | :------------: | :----------:|
| user | username | Account -> username |
|      | external_id | Account -> username |
| account | name | Account -> account_name |
|      | external_id | Account -> id |
| user_account | _from_external_id | Account -> username |
|            | _to_external_id | Account -> id |
| asset_account | _from_external_id | Host -> id |
|            | _to_external_id | Account -> id |

The following table shows the Connected Assets and Risk connector to Spotlight Vulnerability data mapping.

|  CAR vertex/edge  |   CAR field   |  Data source field  |
|  :------------:   | :------------: | :----------: |
| vulnerability | name | vulnerability response -> cve -> id |
|               | external_id | vulnerability response -> id |
|               | description | vulnerability response -> cve -> description |
|               | base_score | vulnerability response -> cve -> base_score |
|               | xfr_wx | vulnerability response -> cve -> exploitability_score |
|               | published_on | vulnerability response -> cve -> published_date |
| asset_vulnerability | _from_external_id | Host -> id |
|            | _to_external_id | vulnerability response -> id |
| application_vulnerability | _from_external_id | App -> id |
|            | _to_external_id | vulnerability response -> id |

III. INSTALLATION:
-----------------------------------------------------------------
- Requirements.txt file attached.


IV. EXAMPLE USAGE (command line):
-----------------------------------------------------------------

```Usage: app.py [arguments]```

required arguments in command line:

```
positional arguments:
-host                       :CrowdStrike api base url
-client_id                  :Client id required for data source authentication
-client_secret              :Client secret code of CrowdStrike API client

optional arguments:
-d                          :run code in debug mode

suppressed arguments:
-working_dir                :working directory
-source                     :data source
```
Update crowdstrike configuration details in 'crowdstrike_config.json`
### Setup Details
Please follow the mentioned steps,

I.	Cloning repository from GitHub

Link: `````https://github.com/IBM/cp4s-car-connectors.git`````

    - Use the PAT token as authentication password for cloning the same to the Linux filesystem using the “git clone” command or download the source code as a zip file.

II.	Setting PYTHONPATH permanently.

    For Linux,
    -  Open the file ~/.bashrc in your text editor – e.g. vi ~/.bashrc;
    -  Add the following line to the end: (change according to your working dorectory)
    export PYTHONPATH= /home/testadmin/cp4s-car-connectors/connectors/crowdstrike
    Save the file.
    -  Close your terminal application;
    -  Start your terminal application again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/cp4s-car-connectors/connectors/crowdstrike/.
    
    For Mac,
    - Open Terminal.app;
    Open the file ~/.bash_profile in your text editor – e.g. atom ~/.bash_profile;
    - Add the following line to the end:
    export PYTHONPATH="/home/testadmin/cp4s-car-connectors/connectors/crowdstrike/"
    Save the file.
    -	Close Terminal.app;
    -	Start Terminal.app again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/cp4s-car-connectors/connectors/crowdstrike/.


### Command To Run the script

1. goto the connector folder ` <cp4s-car-connectors/connectors/crowdstrike>`

2. To run the initial import which is the full dump of the data source assets, run this command:
   ` python app.py -host <crowdstrike api base url> -client_id <crowdstrike Client id> -client_secret <crowdstrike Secret code>  -car-service-url <"BASE_URL"> -car-service-key <"api_key"> -car-service-password <"password"> -source "<crowdstrike_falcon>"`

3. To run the incremental update, create a cronjob that runs, the command to run is:
   ` python app.py -host <crowdstrike api base url> -client_id <crowdstrike Client id> -client_secret <crowdstrike Secret code>  -car-service-url <"BASE_URL"> -car-service-key <"api_key"> -car-service-password <"password"> -source "<crowdstrike_falcon>"`

V. INITIAL IMPORT
-----------------------------------------------------------------
When we run the connector First time. It loads all the asset and their entities available from the source into CAR database.
##### CrowdStrike Falcon Discover (Host, Application, Account and User information)
    "falconpy discovery"
##### CrowdStrike Falcon Spotlight (Vulnerability information)
    "falconpy spotlightvulnerabilities"

VI. INCREMENTAL IMPORT
-----------------------------------------------------------------
- Incremental Import are expected to be based on a time-range and hence we query the data source with time interval filter after initial import was run.
- Incremental import create, update and delete asset, application, user and vulnerability information based on the last import timestamp from data source.
