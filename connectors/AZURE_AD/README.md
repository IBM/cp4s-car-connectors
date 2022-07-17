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