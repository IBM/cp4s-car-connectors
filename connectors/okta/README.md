# Okta ISC-CAR

Okta CAR Connector
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
Okta is an identity and access management service. Okta helps to add authentication and authorization to applications, so that users will access applications in a secure way

Site:   ```https://www.okta.com/```

II. PREREQUISITES:
-----------------------------------------------------------------
Python == 3.9.7 (greater than 3.9.x may work, less than probably will not; neither is tested)

API Authentication: \
Okta uses valid token in HTTP header for authentication. The token needs to prefix with ‘SSWS’ identifier, whichspecifies the proprietary authentication scheme that Okta uses. \
Eg: Authorization: SSWS 00QCjAl4MlV-WPXM...0HmjFx-vbGua

The following table shows the mapping for server application as Asset.

|  CAR vertex/edge  |   CAR field   |  Data source field  |
|  :------------:    |:---------------:| :-----:|
| Asset      | name | label |
|            | external ID | id |
| Application  | name | label |
|            | external ID | name + '_' + id |
|            | app_type | signOnMode |
|            | is_os | False |
|            | status | status |
|            | app_link | Applink -> href |
|            | policies | Policies -> href |
| Asset_Application  | _from_external_id | asset -> external_id |
|            | _to_external_id | application->external_id |

The following table shows the mapping for user.

|  CAR vertex/edge  |   CAR field   |  Data source field  |
|  :------------:   |:-------------:| :-----:|
| Account      | name | Profile -> firstName + profile -> lastName |
|            | external ID | id |
| User      | username | Profile -> login |
|            | email | Profile -> email |
|            | user_category | Credential -> provider -> type |
|            | family_name | Profile -> lastname |
|            | given_name | Profile -> firstname |
|            | external_id | Profile -> email |
|            | active | status == "ACTIVE" |
|            | user_status | status |
|            | last_password_change | passwordChanged |
|            | last_login | lastLogin |
| Asset_Account  | _from_external_id | asset -> external_id |
|            | _to_external_id | id |
| User_account  | _from_external_id | Profile -> login |
|            | _to_external_id | id |

The following table shows the mapping for client as Application.

|  CAR vertex/edge  |   CAR field   |  Data source field  |
|  :------------:   |:-------------:| :-----:|
| Asset | name        | Client -> userAgent -> browser + ‘on’ + Client -> userAgent -> os +client -> device + ‘from’ + client -> ipaddress |
|       | external ID        | app_” + target -> Id ( if target -> type == ‘AppInstance’) +‘ip_’ + Client->ipAddress |
| Application      | Name | Client -> userAgent -> os |
|                  | external ID | Client -> userAgent -> os |
|                  | app_type | os |
|                  | is_os | True |
| Application      | Name | Client -> userAgent -> browser |
|                  | external ID | Client -> userAgent -> rawagent (broser version) |
|                  | app_type | Browser |
|                  | is_os | False |
| IPAddress	| _key | Client->ipaddress  |
| geolocation	| longitude | geolocation -> lon  |
|             | latitude | geolocation -> lat  |
|             | external_id | geolocation -> lat + geolocation -> lon |
| Asset_Application (os) | from_external_id        |   asset ->external_id |
|      | to_external_id | Client -> userAgent -> os |
| Asset_Application (browser) | from_external_id        |  asset ->external_id |
|      | to_external_id | Client -> userAgent -> rawagent (browser version) |
| Asset_IPAddress | _from_external_id | asset -> external_id |
|       | _to | Client -> ipaddress |
| Asset_geolocation | _from_external_id | asset -> external_id |
|       | _to_external_id | geolocation -> lat + geolocation -> lon |

III. INSTALLATION:
-----------------------------------------------------------------
- Requirements.txt file attached.


IV. EXAMPLE USAGE (command line):
-----------------------------------------------------------------

```Usage: app.py [arguments]```

required arguments in command line:

```
positional arguments:
-host                       :Okta API tenant name or IP
-auth_token                 :Okta API authentication token
-url                        :CAR DB url
-api_key                    :api_key
-password                   :password

optional arguments:
-incremental_update         :boolean value initial import/incremental update
-d                          :run code in debug mode

suppressed arguments:
-working_dir                :working directory
-source                     :data source
```
Update Okta configuration details in 'okta_config.json`
### Setup Details
Please follow the mentioned steps,

I.	Cloning repository from GitHub

Link: `````https://github.com/IBM/cp4s-car-connectors.git`````

    - Use the PAT token as authentication password for cloning the same to the Linux filesystem using the �git clone� command or download the source code as a zip file.

II.	Setting PYTHONPATH permanently.

    For Linux,
    -  Open the file ~/.bashrc in your text editor � e.g. vi ~/.bashrc;
    -  Add the following line to the end: (change according to your working dorectory)
    export PYTHONPATH= /home/testadmin/cp4s-car-connectors/connectors/okta
    Save the file.
    -  Close your terminal application;
    -  Start your terminal application again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/cp4s-car-connectors/connectors/okta/.
    
    For Mac,
    - Open Terminal.app;
    Open the file ~/.bash_profile in your text editor � e.g. atom ~/.bash_profile;
    - Add the following line to the end:
    export PYTHONPATH="/home/testadmin/cp4s-car-connectors/connectors/okta/"
    Save the file.
    -	Close Terminal.app;
    -	Start Terminal.app again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/cp4s-car-connectors/connectors/okta/.


### Command To Run the script

1. Goto the connector folder ` <cp4s-car-connectors/connectors/okta>`

2. To run the initial import which is the full dump of the data source assets, run this command:
   ` python app.py -host <Okta tenant hostname or IP> -auth_token <Okta API auth token> -url <"BASE_URL"> -api_key <"api_key"> -password <"password"> -source "<okta>"`

3. To run the incremental update, create a cronjob that runs every configured interval the command to run is:
   ` python app.py -host <Okta tenant hostname or IP> -auth_token <Okta API auth token> -url <"BASE_URL"> -api_key <"api_key"> -password <"password"> -source "<okta>"`

V. INITIAL IMPORT
-----------------------------------------------------------------
When we run the connector First time. It loads all the asset and their entities available from the source into CAR database.
#####USERS_API: (Asset information)
    "https://<your server>//api/v1/users"
#####APPLICATION_API: (Application information)
    "https://<your server>/api/v1/apps"
#####SYSTEMLOG_API: (event log information)
    "https://<your server>/api/v1/logs"

V1. INCREMENTAL IMPORT
-----------------------------------------------------------------
Incremental Imports are expected to be based on a time-range and hence we query the data source with time interval after initial import was run.

####REMARKS
1. Okta connector implementation does not have the vulnerability node. Hence we are not handling the risk score for asset.
