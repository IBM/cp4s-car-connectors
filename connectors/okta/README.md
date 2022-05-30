# Okta ISC-CAR

Okta CAR Connector
```
I.   SUMMARY
II.  PREREQUISITES
III. INSTALLATION
IV.  EXAMPLE USAGE (command line)
V.   INITIAL IMPORT
```
I. SUMMARY:
-----------------------------------------------------------------
Okta is an identity and access management service. Okta helps to add authentication and authorization to applications, users will access in secure way

Site:   ```https://www.okta.com/```

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

    - Use the PAT token as authentication password for cloning the same to the Linux filesystem using the “git clone” command or download the source code as a zip file.

II.	Setting PYTHONPATH permanently.

    For Linux,
    -  Open the file ~/.bashrc in your text editor – e.g. vi ~/.bashrc;
    -  Add the following line to the end: (change according to your working dorectory)
    export PYTHONPATH= /home/testadmin/cp4s-car-connectors/connectors/okta
    Save the file.
    -  Close your terminal application;
    -  Start your terminal application again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/cp4s-car-connectors/connectors/okta/.
    
    For Mac,
    - Open Terminal.app;
    Open the file ~/.bash_profile in your text editor – e.g. atom ~/.bash_profile;
    - Add the following line to the end:
    export PYTHONPATH="/home/testadmin/cp4s-car-connectors/connectors/okta/"
    Save the file.
    -	Close Terminal.app;
    -	Start Terminal.app again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/cp4s-car-connectors/connectors/okta/.


### Command To Run the script

1. goto the connector folder ` <cp4s-car-connectors/connectors/okta>`

2. To run the initial import which is the full dump of the data source assets, run this command:
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
####REMARKS
1.  Login failures are considered for vulnerability, if subsequent user log-in attempt successful, edge between asset and vulnerability edge will be disabled
