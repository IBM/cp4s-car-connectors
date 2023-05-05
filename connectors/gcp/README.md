# GCP-CAR

GCP CAR Connector
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
Google Cloud Platform(GCP) is a cloud platform service provided by Google.

Site:   ```https://cloud.google.com/```

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
-client_email               :Client email address required for data source authentication
-certificate                :Private key required for data source authentication
-url                        :CAR DB url
-api_key                    :api_key
-password                   :password

optional arguments:
-d                          :run code in debug mode

suppressed arguments:
-working_dir                :working directory
-source                     :data source
```
Update GCP configuration details in 'gcp_config.json`
### Setup Details
Please follow the mentioned steps,

I.	Cloning repository from GitHub

Link: `````https://github.com/IBM/cp4s-car-connectors.git`````

    - Use the PAT token as authentication password for cloning the same to the Linux filesystem using the “git clone” command or download the source code as a zip file.

II.	Setting PYTHONPATH permanently.

    For Linux,
    -  Open the file ~/.bashrc in your text editor – e.g. vi ~/.bashrc;
    -  Add the following line to the end: (change according to your working dorectory)
    export PYTHONPATH= /home/testadmin/cp4s-car-connectors/connectors/gcp
    Save the file.
    -  Close your terminal application;
    -  Start your terminal application again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/cp4s-car-connectors/connectors/gcp/.
    
    For Mac,
    - Open Terminal.app;
    Open the file ~/.bash_profile in your text editor – e.g. atom ~/.bash_profile;
    - Add the following line to the end:
    export PYTHONPATH="/home/testadmin/cp4s-car-connectors/connectors/gcp/"
    Save the file.
    -	Close Terminal.app;
    -	Start Terminal.app again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/cp4s-car-connectors/connectors/gcp/.


### Command To Run the script

1. goto the connector folder ` <cp4s-car-connectors/connectors/gcp>`

2. To run the initial import which is the full dump of the data source assets, run this command:
   ` python app.py -client_email <GCP Client email> -certificate <'Private key'>  -car-service-url <"BASE_URL"> -car-service-key <"api_key"> -car-service-password <"password"> -source "<GCP>"`

3. To run the incremental update, create a cronjob that runs, the command to run is:
   ` python app.py -client_email <GCP Client email> -certificate <'Private key'>  -car-service-url <"BASE_URL"> -car-service-key <"api_key"> -car-service-password <"password"> -source "<GCP>"`

V. INITIAL IMPORT
-----------------------------------------------------------------
When we run the connector First time. It loads all the asset and their entities available from the source into CAR database.
##### Service Account: (Authentication)
    "google oauth2 service_account"
##### Resource Manager: (Project information)
    "google cloud resourcemanager_v3"
##### Assets: (Asset and OS Packages vulnerability information)
    "google cloud asset_v1"
##### Databases: (Database and User information)
    "googleapiclient discovery"
##### Securitycenter: (Vulnerability information)
    "google cloud securitycenter"

VI. INCREMENTAL IMPORT
-----------------------------------------------------------------
- Incremental Imports are expected to be based on a time-range and hence we query the Audit log events in gcp to detect various resource actions.
- Incremental imports deletes asset based on the audit logs from data source.
