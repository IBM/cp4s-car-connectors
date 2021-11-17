# Microsoft Azure ISC-CAR

Microsoft Azure Car Connector
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
Microsoft Azure is Microsoft's cloud computing platform, providing a wide variety of services.
Azure enables the rapid development of solutions and provides the resources to accomplish tasks 
that may not be feasible in an on-premises environment. Azure's compute, storage, network, and 
application services allow you to focus on building great solutions without the need to worry 
about how the physical infrastructure is assembled.

Site:   ```https://portal.azure.com```
      
II. PREREQUISITES:
-----------------------------------------------------------------
Python == 3.5.x (greater than 3.5.x may work, less than probably will not; neither is tested)

III. INSTALLATION:
-----------------------------------------------------------------
`adal`
`requests`
- Requirements.txt file attached.



IV. EXAMPLE USAGE (command line):
-----------------------------------------------------------------

```Usage: main.py [arguments]```

required arguments in command line:

```
positional arguments:
-subscriptionID             :subscription ID of tenant (azure)      
-tenantID                   :tenant ID (azure)
-clientID                   :client ID (azure)
-clientSecret               :client secret (azure)
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

## Setup Details
Please follow the mentioned steps,

I.	Cloning repository from Azure-Devops. 
 
 Link: `````https://IBMSecurityConnect@dev.azure.com/IBMSecurityConnect/ISC-CAR/_git/Microsoft-Azure-ISC-CAR`````

    - Use the PAT token as authentication password for cloning the same to the Linux filesystem using the “git clone” command or download the source code as a zip file.

II.	Setting PYTHONPATH permanently.

    For Linux,
    -  Open the file ~/.bashrc in your text editor – e.g. vi ~/.bashrc;
    -  Add the following line to the end: (change according to your working dorectory)
    export PYTHONPATH= /home/testadmin/Microsoft-Azure-ISC-CAR
    Save the file.
    -  Close your terminal application;
    -  Start your terminal application again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/Microsoft-Azure-ISC-CAR/.
    
    For Mac,
    - Open Terminal.app;
    Open the file ~/.bash_profile in your text editor – e.g. atom ~/.bash_profile;
    - Add the following line to the end:
    export PYTHONPATH="/home/testadmin/Microsoft-Azure-ISC-CAR/"
    Save the file.
    -	Close Terminal.app;
    -	Start Terminal.app again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/Microsoft-Azure-ISC-CAR/.


## Command To Run the script

1. To run the initial import which is the full dump of the data source assets, run this command:
        `Microsoft-Azure-ISC-CAR> python main.py -subscriptionID <"subscriptionID"> -tenantID <"tenantID"> -clientID <"clientID"> -clientSecret <"clientSecret"> -url <"BASE_URL"> -api_key <"api_key"> -password <"password"> -source "Microsoft-Azure"`

2. To run the incremental update, create a cronjob that runs every 5 minutes, the command to run is:
        `Microsoft-Azure-ISC-CAR> python main.py -subscriptionID <"subscriptionID"> -tenantID <"tenantID"> -clientID <"clientID"> -clientSecret <"clientSecret"> -url <"BASE_URL"> -api_key <"api_key"> -password <"password"> -source "Microsoft-Azure" -incremental_update True`

##V. Initial Import

#####ACTIVITY_LOGS_URL: (Security events)
    "https://management.azure.com/subscriptions/{subscription_id}/providers/microsoft.insights/eventtypes/management/values"

#####VM_LIST_URL:
    "https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Compute/virtualMachines/"

#####NETWORK_LIST_URL:
    "https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Network/networkInterfaces?"
    
#####APPS_LIST_URL:
    "https://management.azure.com/subscriptions/{subscription_id}/providers/Microsoft.Web/sites"

#####SQL_DATABASE_LIST:
    "https://management.azure.com/subscriptions/{subscription_id}//resourceGroups/{rg_name}/providers/Microsoft.Sql/servers/{"server_name}/databases"
    
##VI. Incremental Update
- Incremental Imports are expected to be based on a time-range and hence we utilize the activity logs in azure monitor to detect various resource action.
- Administrative logs are used to build resource- based assets while security logs are used for building vulnerability data.
- Incremental imports detects create/update and delete scenarios with the help of “operation types”. 
- Azure has action types specified in activity logs, which correspond to a resource -based operation such as creation of a VM, deletion of a VM, etc.,.
- Each of these logs contain the resource-ID, which has the API endpoint for getting further details of the underlying resources.

#####ACTIVITY_LOGS_URL:
    "https://management.azure.com/subscriptions/{subscription_id}/providers/microsoft.insights/eventtypes/management/values"
