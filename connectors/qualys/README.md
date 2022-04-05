# Qualys ISC-CAR

Qualys CAR Connector
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
Qualys is a cloud-based solution that detects vulnerabilities on all networked assets, including servers, network 
devices, peripherals and workstations.The Qualys Cloud Platform and its powerful Cloud Agent provide organizations 
with a single IT, security and compliance solution from prevention to detection to response.

Qualys is integrated solutions that provides businesses with asset discovery, network security, web application
security, threat protection and compliance monitoring

Site:   ```https://www.qualys.com/```

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
-qualys_url                 :Qualys API url
-qualys_gateway             :Qualys Gateway url
-username                   :Qualys authentication user name
-password                   :Qualys authentication secret
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
Update Qualys configuration details in `qualys_config.json`
### Setup Details
Please follow the mentioned steps,

I.	Cloning repository from Azure-Devops.

Link: `````https://IBMSecurityConnect@dev.azure.com/IBMSecurityConnect/ISC-CAR/_git/Qualys-ISC-CAR`````

    - Use the PAT token as authentication password for cloning the same to the Linux filesystem using the “git clone” command or download the source code as a zip file.

II.	Setting PYTHONPATH permanently.

    For Linux,
    -  Open the file ~/.bashrc in your text editor – e.g. vi ~/.bashrc;
    -  Add the following line to the end: (change according to your working dorectory)
    export PYTHONPATH= /home/testadmin/Qualys-ISC-CAR
    Save the file.
    -  Close your terminal application;
    -  Start your terminal application again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/Qualys-ISC-CAR/.
    
    For Mac,
    - Open Terminal.app;
    Open the file ~/.bash_profile in your text editor – e.g. atom ~/.bash_profile;
    - Add the following line to the end:
    export PYTHONPATH="/home/testadmin/Qualys-ISC-CAR/"
    Save the file.
    -	Close Terminal.app;
    -	Start Terminal.app again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/Qualys-ISC-CAR/.


### Command To Run the script

1. To run the initial import which is the full dump of the data source assets, run this command:
   `<Qualys-ISC-CAR> python app.py -qualys_url <Qualys api url> -qualys_gateway <Qualys gateway url> -username <'username'> -password <'secret'> -url <"BASE_URL"> -api_key <"api_key"> -password <"password"> -source "<Qualys>"`

2. To run the incremental update, create a cronjob that runs every 4hours, the command to run is:
   `<Qualys-ISC-CAR> python app.py -qualys_url <Qualys api url> -qualys_gateway <Qualys gateway url> -username <'username'> -password <'secret'> -url <"BASE_URL"> -api_key <"api_key"> -password <"password"> -source "<Qualys>"`

V. INITIAL IMPORT
-----------------------------------------------------------------
When we run the connector First time. It loads all the asset and their entities available from the source into CAR database.​
#####ASSET_API_URL: (Asset information)
    "https://<Qualys Server>/qps/rest/2.0/search/am/hostasset"

#####VMDR_API_URL: (Vulnerability information)
    "https://<Qualys Server>/api/2.0/fo/asset/host/vm/detection/?action=list "
VI. INCREMENTAL IMPORT
-----------------------------------------------------------------

- Incremental Imports are expected to be based on a time-range and hence we query the data source with time interval after initial import was run.
