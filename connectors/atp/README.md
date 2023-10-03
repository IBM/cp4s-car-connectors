# Microsoft Defender for Endpoint ISC-CAR

Microsoft Defender for Endpoint Car Connector
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
Microsoft Defender Advanced Threat Protection (Microsoft Defender for Endpoint) is a unified platform for 
preventative protection, post-breach detection, automated investigation, and response. Microsoft 
Defender for Endpoint protects endpoints from cyber threats; detects advanced attacks and data breaches, 
automates security incidents and improves security posture

Site:   ```https://securitycenter.windows.com```
      
II. PREREQUISITES:
-----------------------------------------------------------------
Python == 3.5.x (greater than 3.5.x may work, less than probably will not; neither is tested)

The following permissions are required for the Microsoft Defender for Endpoint Connected Assets and Risk connector.

**Microsoft Graph**
* User.Read
* User.Read.All

**WindowsDefenderATP**
* AdvancedQuery.Read
* AdvancedQuery.Read.All
* Alert.Read.All
* Alert.ReadWrite.All
* Machine.Read
* Machine.Read.All
* Machine.ReadWrite
* Machine.ReadWrite.All
* User. Read.All

The API access requires OAuth2.0 authentication.

Generate an ATP access token by completing the following steps.
1. Create an Azure Active Directory application.
2. Get an access token that uses this application. Use the token to access the Microsoft Defender for Endpoint API.

For more information, see [Create an app to access Microsoft Defender for Endpoint without a user](https://learn.microsoft.com/en-us/microsoft-365/security/defender-endpoint/api/exposed-apis-create-app-webapp?view=o365-worldwide).


The Microsoft Defender for Endpoint connector is designed to work with the api/advancedqueries/run, api/machines, and api/alerts API endpoints. For more information about these API endpoints, see [Supported Microsoft Defender for Endpoint APIs](https://docs.microsoft.com/en-us/microsoft-365/security/defender-endpoint/exposed-apis-list?view=o365-worldwide).

Microsoft Defender for Endpoint is an endpoint security platform to prevent, detect, investigate, and respond to advanced threats. For more information about Microsoft Defender for Endpoint, see [Microsoft Defender for Endpoint](https://www.microsoft.com/en-us/microsoft-365/windows/microsoft-defender-atp).

The Microsoft Defender for Endpoint schema is made up of multiple tables that provide either event information or information about devices and other entities. To effectively build queries that span multiple tables, you must understand the tables and the columns in the schema.

The following table outlines Microsoft Defender for Endpoint schema table names and descriptions.

| Table name  |   Description   |
| :----------:|:---------------:|
| [AlertEvents](https://docs.microsoft.com/en-us/windows/security/threat-protection/microsoft-defender-atp/advanced-hunting-alertevents-table) | Alerts on Microsoft Defender Security Center |
| [MachineInfo](https://docs.microsoft.com/en-us/windows/security/threat-protection/microsoft-defender-atp/advanced-hunting-machineinfo-table) | Machine information, including OS information |
| [MachineNetworkInfo](https://docs.microsoft.com/en-us/windows/security/threat-protection/microsoft-defender-atp/advanced-hunting-machinenetworkinfo-table) | Network properties of network devices, including adapters, IP addresses, MAC addresses, connected networks, and domains |
| [ProcessCreationEvents](https://docs.microsoft.com/en-us/windows/security/threat-protection/microsoft-defender-atp/advanced-hunting-processcreationevents-table) | Process creation and related events |
| [NetworkCommunicationEvents](https://docs.microsoft.com/en-us/windows/security/threat-protection/microsoft-defender-atp/advanced-hunting-networkcommunicationevents-table) | Network connection and related events |
| [FileCreationEvents](https://docs.microsoft.com/en-us/windows/security/threat-protection/microsoft-defender-atp/advanced-hunting-filecreationevents-table) | File creation, modification, and other file system events |
| [RegistryEvents](https://docs.microsoft.com/en-us/windows/security/threat-protection/microsoft-defender-atp/advanced-hunting-registryevents-table) | Creation and modification of registry entries |
| [LogonEvents](https://docs.microsoft.com/en-us/windows/security/threat-protection/microsoft-defender-atp/advanced-hunting-logonevents-table) | Sign-ins and other authentication events |
| [ImageLoadEvents](https://docs.microsoft.com/en-us/windows/security/threat-protection/microsoft-defender-atp/advanced-hunting-imageloadevents-table) | DLL loading events |
| [MiscEvents](https://docs.microsoft.com/en-us/windows/security/threat-protection/microsoft-defender-atp/advanced-hunting-miscevents-table) | Multiple event types, including events that are triggered by security controls such as Windows Defender Antivirus and Exploit Protection |

The following table shows the Connected Assets and Risk connector to Machine Network Profile data mapping.

|  CAR vertex/edge  |   CAR field   |  Azure field  |
|  :------------:|:---------------:|:-----:|
| IPAddress (Private) | _key    | Machine NetworkInfo -> IPAddresses |
| IPAddress (Public) | _key     | Machine Info -> PublicIP |
| MacAddress   | _key     | Machine NetworkInfo -> MacAddress |
| IPAddress_MacAddress  |  _from     | ipaddress/_key(ipaddress node) |
|                 | _to     | macaddress/_key(macaddress node) |
|                 | active     | TRUE |
|                 | timestamp     | report -> timestamp |
|                 | source     | source -> _key |
|                 | report     | report -> _key |
| Asset_IPAddress  |  from_external_id     | external_id of the asset |
|                 | _to     | ipaddress/_key(ipaddress node) |
|                 | active     | TRUE |
|                 | timestamp     | Activity log -> eventTimestamp |
|                 | source     | source -> _key |
|                 | report     | report -> _key |

The following table shows the Connected Assets and Risk connector to Users data mapping.

|  CAR vertex/edge  |   CAR field   |  Azure field  |
|  :------------:|:---------------:|:-----:|
| User | _key    | User -> accountName |
| Asset_User  |  from_external_id     | Machine -> id |
|                 | _to     | 'user/' + user -> accountName |
|                 | active     | TRUE |
|                 | timestamp     | Activity log -> eventTimestamp |
|                 | source     | source -> _key |
|                 | report     | report -> _key |
| User_Hostname  |  _from     | 'user/' + user -> accountName |
|                 | _to     | hostname/' + Machine -> computerDnsName |
|                 | active     | TRUE |
|                 | timestamp     | Activity log -> eventTimestamp |
|                 | source     | source -> _key |
|                 | report     | report -> _key |

The following table shows the Connected Assets and Risk connector to Vulnerabilities data mapping.

|  CAR vertex/edge  |   CAR field   |  Azure field  |
|  :------------:|:---------------:|:-----:|
| Asset | Name        | Machine -> computerDnsName |
|       | Description | Custom message with: osPlatform |
|       | external ID | Machine -> id |
|  Vulnerability | external ID | Alerts -> id |
|                | name    | Alerts -> title |
|                | Description    | Alerts -> description |
|                | disclosed_on    | Alerts -> firstEventTime |
|                | published_on    | Alerts -> alertCreationTime |
| Asset_Vulnerability | from_external_id    | external_id of the machine |
|         | to_external_id    | Alerts -> id |
|         | active    | TRUE |
|         | timestamp    | report -> timestamp |
|         | source    | source -> _key |
|         | report    | report -> _key |

III. INSTALLATION:
-----------------------------------------------------------------
`adal`
`requests`


IV. EXAMPLE USAGE (command line):
-----------------------------------------------------------------

```Usage: main.py [arguments]```

required arguments in command line:

```
positional arguments:
-subscriptionID             :subscription ID of tenant (ms-defender)
-tenantID                   :tenant ID (ms-defender)
-clientID                   :client ID (ms-defender)
-clientSecret               :client secret (ms-defender)
-url                        :CAR DB url
-api_key                    :api_key
-password                   :password
-incremental_update :boolean value initial import/incremental update

optional arguments:
-working_dir                :working directory
-source                     :data source
-alerts(False)              :to exclude logic for fetching alerts
-vuln(False)                :to exclude logic for fetching vulnerability
by default both alerts and vulnerabilities are included
```

## Setup Details
Please follow the mentioned steps,

I.	Cloning repository from Azure-Devops. 
 
 Link: `````https://IBMSecurityConnect@dev.azure.com/IBMSecurityConnect/ISC-CAR/_git/Microsoft-Defender-ATP-ISC-CAR-v1`````

    - Use the PAT token as authentication password for cloning the same to the Linux filesystem using the “git clone” command or download the source code as a zip file.

II.	Setting PYTHONPATH permanently.

    For Linux,
    -  Open the file ~/.bashrc in your text editor – e.g. vi ~/.bashrc;
    -  Add the following line to the end: (change according to your working dorectory)
    export PYTHONPATH= /home/testadmin/Microsoft-Defender-ATP-ISC-CAR-v1
    Save the file.
    -  Close your terminal application;
    -  Start your terminal application again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/Microsoft-Defender-ATP-ISC-CAR-v1/.
    
    For Mac,
    - Open Terminal.app;
    Open the file ~/.bash_profile in your text editor – e.g. atom ~/.bash_profile;
    - Add the following line to the end:
    export PYTHONPATH="/home/testadmin/Microsoft-Defender-ATP-ISC-CAR-v1/"
    Save the file.
    -	Close Terminal.app;
    -	Start Terminal.app again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/Microsoft-Defender-ATP-ISC-CAR-v1/.


## Command To Run the script

1. To run the initial import which is the full dump of the data source assets, run this command:
        `python main.py -subscriptionID <"subscriptionID"> -tenantID <"tenantID"> -clientID <"clientID"> -clientSecret <"clientSecret"> -url <"BASE_URL"> -api_key <"api_key"> -password <"password"> -source "Microsoft-Windows-Defender-ATP"`

2. To run the incremental update, create a cronjob that runs every 5 minutes, the command to run is:
        `python main.py -subscriptionID <"subscriptionID"> -tenantID <"tenantID"> -clientID <"clientID"> -clientSecret <"clientSecret"> -url <"BASE_URL"> -api_key <"api_key"> -password <"password"> -source "Microsoft-Windows-Defender-ATP" -incremental_update True`

##V. Initial Import

#####ALERTS_LIST_URL:
    "https://api.securitycenter.windows.com/api/alerts"
    
#####MACHINE_LIST_URL:
    "https://api.securitycenter.windows.com/api/machines"
    
#####ADVANCED_HUNTING_URL: (For IP and MAC Address and vulnerability)
    "https://api.securitycenter.windows.com/api/advancedqueries/run"
        
#####LOGON_USER_LIST_URL:
    "https://api.securitycenter.windows.com/api/machines/{id}/logonusers"
    
    
##VI. Incremental Update
- Incremental Imports are expected to be based on a last seen of the machine.
- If healthStatus == ‘inactive’ and last seen of machine >= 15 days, it denotes a Machine deletion in incremental update.
- only incremental run ip and mac edges of asset is tagged as active. previous run ip and mac are disabled by patch call.
- In incremental run, resolved and updated alerts are disabled and updated respectively with patch calls.

The above-mentioned actions guide us to accordingly process the data and interact with the CAR database as follows,
```
Create event  - all the asset and vulnerability nodes are built and imported to CAR import service.
Update event - only the updated assets and vulnerability nodes are built and imported to CAR import service.
Delete event - The underlying resource is disabled using CAR deletion endpoint, using its external ID (asset identifier)
```

##Remarks:
- Asset deletion is performed on car side, if the machine is inactive for 15 days or more.
- Vulnerability is taking for all machines other than Inactive machines in incremental update.
- No edge creation between mac and public ip.
- Hostname update shows up as a new entry, hence we treat it as a new machine creation(new machine id is allocated).