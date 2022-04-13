# Cybereason ISC-CAR

Cybereason CAR Connector
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
The Cybereason platform provides military-grade cyber security with real-time awareness and detection. Cybereason takes isolated suspicious activities and links them together to present a story of an attack, providing a truly end-to-end view of malicious activities.

Using advanced detection techniques, ranging from behavioral analysis to machine learning, Cybereason recognizes relationships among multiple events and determines if they are part of a single attack.

Site:   ```https://www.cybereason.com/```

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
-host                       :Cybereason API server name or IP
-port                       :Cybereason server port number
-username                   :Cybereason API authentication user name
-password                   :Cybereason API authentication secret
-url                        :CAR DB url
-api_key                    :api_key
-password                   :password

optional arguments:
-incremental_update         :boolean value initial import/incremental update
-d                          :run code in debug mode
-malop_retention_period     :number of days of vulnerabilities to process, default is 30 days

suppressed arguments:
-working_dir                :working directory
-source                     :data source
```
Update Cybereason configuration details in 'cybereason_config.json`
### Setup Details
Please follow the mentioned steps,

I.	Cloning repository from GitHub

Link: `````https://github.com/IBM/cp4s-car-connectors.git`````

    - Use the PAT token as authentication password for cloning the same to the Linux filesystem using the “git clone” command or download the source code as a zip file.

II.	Setting PYTHONPATH permanently.

    For Linux,
    -  Open the file ~/.bashrc in your text editor – e.g. vi ~/.bashrc;
    -  Add the following line to the end: (change according to your working dorectory)
    export PYTHONPATH= /home/testadmin/cp4s-car-connectors/connectors/cybereason
    Save the file.
    -  Close your terminal application;
    -  Start your terminal application again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/cp4s-car-connectors/connectors/cybereason/.
    
    For Mac,
    - Open Terminal.app;
    Open the file ~/.bash_profile in your text editor – e.g. atom ~/.bash_profile;
    - Add the following line to the end:
    export PYTHONPATH="/home/testadmin/cp4s-car-connectors/connectors/cybereason/"
    Save the file.
    -	Close Terminal.app;
    -	Start Terminal.app again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/cp4s-car-connectors/connectors/cybereason/.


### Command To Run the script

1. goto the connector folder ` <cp4s-car-connectors/connectors/cybereason>`

2. To run the initial import which is the full dump of the data source assets, run this command:
   ` python app.py -host <Cybereason hostname or IP> -port <Cybereason server port> -username <'username'> -password <'secret'> -url <"BASE_URL"> -api_key <"api_key"> -password <"password"> -source "<Cybereason>"`

3. To run the incremental update, create a cronjob that runs every 4hours, the command to run is:
   ` python app.py -host <Cybereason hostname or IP> -port <Cybereason server port> -username <'username'> -password <'secret'> -url <"BASE_URL"> -api_key <"api_key"> -password <"password"> -source "<Cybereason>"`

V. INITIAL IMPORT
-----------------------------------------------------------------
When we run the connector First time. It loads all the asset and their entities available from the source into CAR database.​
#####SENSORS_API: (Asset information)
    "https://<your server>/rest/sensors/query"
#####HUNT_INVESTIGATE_API_URL: (network information)
    "https://<your server>/rest/visualsearch/query/simple"

#####MALOP_API_URL: (Vulnerability information)
    "https://<your server>/rest/detection/inbox"
VI. INCREMENTAL IMPORT
-----------------------------------------------------------------

- Incremental Imports are expected to be based on a time-range and hence we query the data source with time interval after initial import was run.
- Sensor status in Stale or Archive denotes the asset deletion in Incremental import
####REMARKS
1.  Vulnerabilities are fetched based on time frame provided by user, default time duration is 30 days
