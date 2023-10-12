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

GCP:
- GCP Client email id
- GCP Service Account key

Create a service account key:
- In the Google Cloud console, go to the Service accounts page.
- Select a project.
- Click the email address of the service account that you want to create a key for.
- Click the Keys tab.
- Click the Add key drop-down menu, then select Create new key.
- Select JSON as the Key type and click Create

**GCP App Engine**

The following table shows the Connected Assets and Risk connector to GCP App Engine mapping.

| CAR vertex/edge |   CAR field   |  Data source field  |
| :-------------: | :-----------: | :-----------: |
| asset | name | service -> resource -> data -> id |
|       | external_id | service -> name |
|       | asset_type | service -> assetType |
| application | name | version -> resource -> data -> name |
|       | external_id | version -> name |
|       | status | version -> resource -> data -> serviceStatus |
|       | app_type | version -> assetType |
|       | is_os | False |
|       | runtime | version -> resource -> data -> runtime |
|       | environment | version -> resource -> data -> env |
| hostname | host_name | service -> resource -> data -> id + app -> resource -> data -> defaultHostname |
|       | _key | service -> resource -> data -> id + app -> resource -> data -> defaultHostname |
| asset_hostname | _from_external_id | service -> name |
|                | _to | service -> resource ->data -> id + app -> reource ->data -> defaultHostname |
| asset_application | _from_external_id | service -> name |
|                | _to_external_id | version -> name |
| geolocation | external_id | app -> resource -> data -> locationId |
|       | region | app -> resource -> data -> locationId |
| asset_geolocation | _from_external_id | service -> name |
|                | _to_external_id | app -> resource -> data -> locationId |

The following table shows the Connected Assets and Risk connector to SCC findings mapping.

| CAR vertex/edge |   CAR field   |  Data source field  |
| :-------------: | :-----------: | :-----------: |
| vulnerability | name | vulnerability response -> finding -> category |
|          | external_id | vulnerability response -> finding -> canonocal_name |
|          | description | vulnerability response -> finding -> description |
|          | base_score | vulnerability response -> finding -> severity |
|          | published_on | vulnerability response -> create_time |
|          | updated_on | vulnerability response -> event_time |
| asset_vulnerability | _from_external_id | service->name |
|          | _to_external_id | vulnerability response -> finding -> canonocal_name |

**Google Kubernetes Engine**

The following table shows the Connected Assets and Risk connector to GKE cluster.

| CAR vertex/edge |   CAR field   |  Data source field  |
| :-------------: | :-----------: | :-----------: |
| asset | name | cluster response -> resource -> data -> name |
|       | external_id | cluster response -> name |
|       | asset_type | cluster response -> asset_type |
|       | status | cluster response -> resource -> data -> status |
|       | cluster_id | cluster response -> resource -> data -> id |
| ipaddress | _key | cluster response -> resource -> data -> endpoint |
| geolocation | external_id | cluster response -> resource -> location |
|       | region | cluster response -> resource -> location |
| asset_geolocation | _from_external_id | cluster response -> name |
|          | _to_external_id | cluster response -> resource -> location |
| asset_ipaddress | _from_external_id | cluster response -> name |
|          | _to | cluster response -> resource -> data -> endpoint |
| ipaddress_geolocation | _from | cluster response -> resource -> data -> endpoint |
|          | _to_external_id | cluster response -> resource -> location |

The following table shows the Connected Assets and Risk connector to GKE node.

| CAR vertex/edge |   CAR field   |  Data source field  |
| :-------------: | :-----------: | :-----------: |
| asset | name | node response -> resource -> data -> metadata -> name |
|       | external_id | node response -> name |
|       | asset_type | node response -> asset_type |
|       | cluster_name | node response -> name |
| geolocation | external_id | node response -> resource -> location |
|       | region | node response -> resource -> location |
| asset_geolocation | _from_external_id | node response -> name |
|          | _to_external_id | node response -> resource -> location |
| ipaddress | _key | Node response - > resource -> data -> status -> addresses -> address |
|           | access_type | Node response - > resource -> data -> status ->addresses-> type: InternalIP OR Node response - > resource -> data -> status ->addresses-> type: ExternalIP |
| asset_ipaddress | _from_external_id | node response -> name |
|          | _to | Node response - > resource -> data -> status -> addresses -> address |
| hostname | host_name | Node response - > resource -> data -> statusaddresses-> address |
|          | _key | Node response - > resource -> data -> statusaddresses-> address |
| asset_hostname | _from_external_id | node response -> name |
|          | _to | Node response - > resource -> data -> statusaddresses-> address |

The following table shows the Connected Assets and Risk connector to GKE container.

| CAR vertex/edge |   CAR field   |  Data source field  |
| :-------------: | :-----------: | :-----------: |
| asset | name | pod response -> resource -> data -> status -> ContainerStatuses -> name |
|       | external_id | pod response -> resource -> data -> status -> ContainerStatuses -> containerID |
|       | asset_type | "container" |
|       | cluster_name | pod response -> name |
|       | node_name | pod response -> resource -> data -> spec -> nodeName |
|       | image | pod response -> resource -> data -> status -> ContainerStatuses -> imageID |
| geolocation | external_id | pod response -> resource -> location |
|       | region | pod response -> resource -> location |
| asset_geolocation | _from_external_id | pod response -> resource -> data -> status -> ContainerStatuses -> containerID |
|          | _to_external_id | pod response -> resource -> location |
| ipaddress | _key | Pod response- - > resource -> data -> status -> podIP |
| asset_ipaddress | _from_external_id | Pod response- > resource -> data -> status -> ContainerStatuses -> containerID |
|          | _to | Pod response- - > resource -> data -> status -> podIP |
| asset_application | _from_external_id | Pod response- > resource -> data -> status -> ContainerStatuses -> containerID |
|          | _to_external_id | Pod response- - > resource -> data -> fields -> metadata -> labels ->app |
| container | name | pod response -> resource -> data -> status -> ContainerStatuses -> name |
|       | external_id | pod response -> resource -> data -> status -> ContainerStatuses -> containerID |
|       | cluster_name | pod response -> name |
|       | node_name | pod response -> resource -> data -> spec -> nodeName |
|       | image | pod response -> resource -> data -> status -> ContainerStatuses -> imageID |
| ipaddress_container | _from | pod response -> resource -> data -> status -> ContainerStatuses -> podID |
|          | _to_external_id | pod response -> resource -> data -> status -> ContainerStatuses -> containerID |
| asset_container | _from | node response -> name |
|          | _to_external_id | pod response -> resource -> data -> status -> ContainerStatuses -> containerID |

The following table shows the Connected Assets and Risk connector to deployments.

| CAR vertex/edge |   CAR field   |  Data source field  |
| :-------------: | :-----------: | :-----------: |
| aplication | external_id  | Deployment response -> name |
|            | name  | Deployment response -> resource -> data -> metadata -> name |
|            | app_type  | Deployment response -> assetType |
| asset_application | _from_external_id | Deployment response -> name |
|          | _to_external_id | Deployment response -> name |

The following table shows the Connected Assets and Risk connector to Aduit log with vuln details.

| CAR vertex/edge |   CAR field   |  Data source field  |
| :-------------: | :-----------: | :-----------: |
| vulnerability | name | response- > jsonPyload -> vulnerability -> fixedPackage +‘:’ + response- > jsonPyload -> vulnerability -> cveId |
|          | descrption | response- > jsonPyload -> vulnerability -> description |
|          | external_id | response- > jsonPyload -> vulnerability -> cveId |
|          | base_score | response- > jsonPyload -> vulnerability -> cvssScore |
| asset_vulnerability | _from_external_id | Pod response- > resource -> data -> status -> ContainerStatuses -> containerID |
|          | _to_external_id | response- > jsonPyload -> vulnerability -> cveId |

The following table shows the Connected Assets and Risk connector to SCC findings.

| CAR vertex/edge |   CAR field   |  Data source field  |
| :-------------: | :-----------: | :-----------: |
| vulnerability | name | vulnerability response- >category |
|          | descrption | vulnerability response- > description |
|          | external_id | vulnerability response -> canonical_name |
|          | base_score | vulnerability response -> severity |
|          | published_on | vulnerability response -> createTime |
|          | updated_on | vulnerability response -> event_time |
| asset_vulnerability | _from_external_id | vulnerability response -> resource_name |
|          | _to_external_id | vulnerability response -> canonical_name |

**VM Instances**

The following table shows the Connected Assets and Risk connector to VM Instance details.

| CAR vertex/edge |   CAR field   |  Data source field  |
| :-------------: | :-----------: | :-----------: |
| asset | name | instance response -> resource -> data -> name |
|       | external_id | instance response -> name + instance response -> resource ->data -> id|
|       | asset_type | cluster response -> asset_type |
|       | description | instance response -> name + instance response -> resource ->data -> description |
|       | instance_id | instance response -> resource -> data -> id |
| ipaddress | _key | instance response- >resource -> data -> networkInterfaces->networkIP OR instance response- > resource -> data -> networkInterfaces -> accessconfig -> natIp |
|           | region_id | Instance response -> resource -> data -> networkInterfaces ->subnetwork |
|           | access_type | Instance response -> resource -> data -> networkInterfaces ->ipv6AccessType OR Instance response -> resource -> data -> networkInterfaces -> accessConfigs->type |
| geolocation | external_id | instance response -> resource -> location |
|             | region | instance response -> resource -> location |
| asset_ipaddress | _from_external_id | instance response- >name + instance response- >resource -> data ->id |
|           | _to | instance response- >data -> fields -> networkInterfaces-> natIP OR instance response- >data -> fields -> networkInterfaces->networkIP |
| asset_geolocation | _from_external_id | instance response- >name + instance response- >resource -> data -> id |
|           | _to_external_id | instance response- >location |
| ipaddress_geolocation | _from | instance response- >resource -> data -> networkInterfaces-> networkIP OR instance response- > resource -> data -> networkInterfaces -> accessconfig -> natIp |
|           | _to_external_id | instance response- >location |
| hostname | host_name | instance response- >resource -> data -> name(or)instance response -> resource ->data -> hostname |
|          | _key | instance response- >resource -> data -> name(or)instance response -> resource ->data -> hostname |
| asset_hostname | _from_external_id | instance response- >name + instance response- >resource -> data ->id |
|           | _to | instance response- >resource -> data -> name(or)instance response -> resource ->data -> hostname |
| ipregion | external_id | Instance response -> resource -> data -> networkInterfaces ->subnetwork |
|          | id | Instance response -> resource -> data -> networkInterfaces ->subnetwork |
|          | name | "ipregion" + ":" + Instance response -> resource -> data -> networkInterfaces ->subnetwork |

The following table shows the Connected Assets and Risk connector to VM Instance OS Inventory.

| CAR vertex/edge |   CAR field   |  Data source field  |
| :-------------: | :-----------: | :-----------: |
| application | name | Response -> osinventory -> items -> installedpackage-<> ->installedPacked -> aptPackage -> packageName OR Response -> osInventory -> osInfo -> longName |
|             | external_id | Response -> osinventory -> items -> installedpackage-<> -> id OR Response -> osInventory -> osInfo -> kernalVersion |
|             | is_os | False OR True |
| asset_application | _from_external_id | reponse->name & response -> osInventory -> name |
|                   | _to_external_id | Response -> osinventory -> items -> installedpackage -> id OR Response -> osInventory -> osInfo -> kernalVersion |
|                   | created | Response -> osinventory -> items -> installedpackage-<> ->createTime |

The following table shows the Connected Assets and Risk connector to Vulnerability - OS Inventory.

| CAR vertex/edge |   CAR field   |  Data source field  |
| :-------------: | :-----------: | :-----------: |
| vulnerability | name | vulnerability response- >resource -> data-> vulnerabilities -> items -> installedInventoryItemid + ‘:’ + vulnerability response- >resource ->data-> vulnerabilities -> details -> cve |
|               | external_id | vulnerability response- >resource -> data-> vulnerabilities -> details -> cve |
|               | description | vulnerability response- >resource -> data-> vulnerabilities -> details -> description |
|               | base_score | vulnerability response- >resource -> data-> vulnerabilities -> details -> cvssV3 -> baseScore |
|               | xfr_cvss2_base | vulnerability response- >resource -> data-> vulnerabilities -> details -> cvssV2Score |
|               | xfr_cvss3_base | vulnerability response- >resource -> data-> vulnerabilities -> details -> cvssV3 -> baseScore |
| asset_vulnerability | _from_external_id | instance response- >name |
|        | _to_external_id | vulnerability response- >resource -> data-> vulnerabilities -> details -> cve |
| application_vulnerability | _from_external_id | vulnerability response- >resource -> data-> vulnerabilities -> items -> installedInventoryItemId |
|         | _to_external_id | vulnerability response- >resource -> data-> vulnerabilities -> details -> cve |

The following table shows the Connected Assets and Risk connector to Vulnerability - SCC.

| CAR vertex/edge |   CAR field   |  Data source field  |
| :-------------: | :-----------: | :-----------: |
| vulnerability | name | vulnerability response- > finding -> category |
|               | external_id | vulnerability response- > finding ->canonical_name |
|               | description | vulnerability response -> findings ->description |
|               | base_score | vulnerability response- >findings -> severity |
|               | published_on | vulnerability response -> findings ->create_time |
|               | updated_on | vulnerability response -> findings ->event_time |
| asset_vulnerability | _from_external_id | Vulnerability response ->name |
|        | _to_external_id | vulnerability response- > finding ->canonical_name |

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
-private_key                :Private key required for data source authentication
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
   ` python app.py -client_email <GCP Client email> -private_key <'Private key'>  -car-service-url <"BASE_URL"> -car-service-key <"api_key"> -car-service-password <"password"> -source "<GCP>"`

3. To run the incremental update, create a cronjob that runs, the command to run is:
   ` python app.py -client_email <GCP Client email> -private_key <'Private key'>  -car-service-url <"BASE_URL"> -car-service-key <"api_key"> -car-service-password <"password"> -source "<GCP>"`

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
