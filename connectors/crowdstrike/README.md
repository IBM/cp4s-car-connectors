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
