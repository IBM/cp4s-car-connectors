# ProofPoint ISC-CAR

Proofpoint Car Connector
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
Proofpoint TAP monitors email flow for malicious content, such as malicious URLs and attachments.
Generate alerts for malicious emails. Helps to detect, mitigate, and block threats that target people through email.
Proofpoint TAP detect both known and new attacks that use malicious attachments and URLs to install malware on a device
or trick users to share their passwords or other sensitive information

Site:   ```https://www.proofpoint.com/us/products/advanced-threat-protection/targeted-attack-protection```

II. PREREQUISITES:
-----------------------------------------------------------------
Python == 3.9.7 (greater than 3.9.x may work, less than probably will not; neither is tested)


The following table shows the Connected Assets and Risk connector to TAP data mapping.

| CAR vertex/edge  |   CAR field   |   EC2 Network Profile field  |
|  :------------: |:---------------:| :-----:|
| Asset | name | Events -> receipientName |
|       | external_id | Events -> receipientName |
|       | description | “Proofpoint User of domain” + Events ->receipientName |
|       | asset_type | User |
|       | source | source-> id |
| Vulnerability | external_id | Events -> threatId |
|       | name | Events -> classification + ":" + event-> threat |
|       | description | event -> classification + event ->threatType |
|       | disclosed_on | event -> messageTime |
|       | base_score | event->spamScore or event->phishScore or event->impostorScore or event->malwareScore |
|       | source | source-> id |
| Asset_Vulnerability | _from_external_id | Events -> receipientName  |
|       | _to_external_id | Events -> threatId |
|       | active | TRUE |
|       | created | report -> _key |
|       | source | source -> id |
|       | report | report -> _key |
|       | risk_score | event->spamScore or event->phishScore or event->impostorScore or event->malwareScore |
| Account | external_id | identity -> guiid |
|       | name | Events -> recipientName |
|       | cumulative_score | identity->attackIndex |
|       | source | source -> id |
|       | active | True |
| User | username | identity->name |
|      | job_title | identity->title |
|      | email | identity ->emails |
|      | user_category | identity ->vip |
|      | employee_id | identity ->customerUserId |
|      | department | identity ->department |
|      | external_id | identity ->customerUserId or identity->emails |
|      | source | source ->id |
| asset_account | _from_external_id | Event -> recipient |
|         | _to_external_id | Identity -> guiid |
|         | created | report -> _key |
|         | active | True |
|         | report | report -> _key |
|         | source | source -> id |
| user_account | _from_external_id | Identity -> customerUserId or Identity -> Emails |
|         | _to_external_id | Identity -> guiid |
|         | created | report -> _key |
|         | active | True |
|         | report | report -> _key |
|         | source | source -> id |


III. INSTALLATION:
-----------------------------------------------------------------
- Requirements.txt file attached.



IV. EXAMPLE USAGE (command line):
-----------------------------------------------------------------

```Usage: app.py [arguments]```

required arguments in command line:

```
positional arguments:
-proofpoint_url             :Proofpoint API url
-principle                  :Proofpoint authentication principle
-secret                     :Proofpoint authentication secret
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
Update Proofpoint configuration details in `proofpoint_config.json`
### Setup Details
Please follow the mentioned steps,

I.	Cloning repository from Azure-Devops.

Link: `````https://IBMSecurityConnect@dev.azure.com/IBMSecurityConnect/ISC-CAR/_git/ProofPointTAP-ISC-CAR`````

    - Use the PAT token as authentication password for cloning the same to the Linux filesystem using the “git clone” command or download the source code as a zip file.

II.	Setting PYTHONPATH permanently.

    For Linux,
    -  Open the file ~/.bashrc in your text editor – e.g. vi ~/.bashrc;
    -  Add the following line to the end: (change according to your working dorectory)
    export PYTHONPATH= /home/testadmin/ProofPoint-ISC-CAR
    Save the file.
    -  Close your terminal application;
    -  Start your terminal application again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/ProofPoint-ISC-CAR/.
    
    For Mac,
    - Open Terminal.app;
    Open the file ~/.bash_profile in your text editor – e.g. atom ~/.bash_profile;
    - Add the following line to the end:
    export PYTHONPATH="/home/testadmin/ProofPoint-ISC-CAR/"
    Save the file.
    -	Close Terminal.app;
    -	Start Terminal.app again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/ProofPoint-ISC-CAR/.


### Command To Run the script

1. To run the initial import which is the full dump of the data source assets, run this command:
   `ProofPoint-ISC-CAR> python app.py -proofpoint_url <proofpoint api url> -principle <'principle'> -secret <'secret'> -url <"BASE_URL"> -api_key <"api_key"> -password <"password"> -source "<Proofpoint>"`

2. To run the incremental update, create a cronjob that runs every 5 minutes, the command to run is:
   `ProofPoint-ISC-CAR> python app.py -proofpoint_url <proofpoint api url> -principle <'principle'> -secret <'secret'> -url <"BASE_URL"> -api_key <"api_key"> -password <"password"> -source "<Proofpoint>"`

V. Initial Import
-----------------------------------------------------------------

#####SIEM_API_URL: (Security events)
    "https://tap-api-v2.proofpoint.com/v2/siem/all"

#####PEOPLE_API_URL:
    "https://tap-api-v2.proofpoint.com/v2/people/vap"
VI. Incremental Update
-----------------------------------------------------------------

- Incremental Imports are expected to be based on a time-range and hence we query the data source with time interval after initial import was run.
- Threat status will be queried using Threat API and used to delete the threat.

#####THREAT_API_URL:
    "https://tap-api-v2.proofpoint.com/v2/threat/summary/<threatId>"
