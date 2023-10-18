# RHACS-CAR

RHACS (Stackrox) CAR Connector
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
The Red Hat Advanced Cluster Security (RHACS) for Kubernetes, powered by StackRox technology, is the pioneering Kubernetes-native security platform, equipping organizations to more securely build, deploy, and run cloud-native applications anywhere.

Site:   ```https://www.redhat.com/en/technologies/cloud-computing/openshift/advanced-cluster-security-kubernetes```

II. PREREQUISITES:
-----------------------------------------------------------------
Python == 3.9.7 (greater than 3.9.x may work, less than probably will not; neither is tested)

APIs used from data source:
|  API  |   Endpoint   |  Description  |
| :---: |:------------:| :------------:|
| ClusterService | https://\<server\>/v1/clusters | List of clusters and details |
| NodeService | https://\<server\>/v1/nodes/{clusterId} | List and details of Nodes in Cluster |
|PodService | https://\<server\>/v1/pods | List of Pods. |
| ImageService | https://\<server\>/v1/images | List of Images |
| DeploymentService | https://\<server\>/v1/deployments | List of deployments. |
| RoleService | https://\<server\>/v1/roles | List of roles |
| GroupService | https://\<server\>/v1/groups | List of groups |
| UserService | https://\<server\>/v1/users | List of Users |

Authorization Parameters:
|  Variable  |   Type   |  Description  |
| :--------: |:--------:| :------------:|
| server | String | The base URL for your server. |
| token | String | Token - generate token with read only access (Analyst role) |

The following table shows the mapping for node as an asset.

|  CAR vertex/edge  |   CAR field   |  Data source field  |
|  :------------:   |:-------------:| :--------------:|
| asset | name | node -> name |
|       | external ID | node -> id |
|       | risk | node -> riskScore |
|       | clustername | node -> clusterName |
| ipaddress | _key | node -> internalIpAddress OR node -> externalIpAddress |
| vulnerability | name | node -> scan -> components -> vulns -> cve |
|               | external_id | node -> scan -> components -> vulns -> cve |
|               | description | node -> scan -> components -> vulns -> summary |
|               | base_score | node -> scan -> components -> vulns -> cvss |
|               | published_on | node -> scan -> components -> vulns -> publishedOn |
|               | updated_on | node -> scan -> components -> vulns -> lastModified |
| asset_vulnerability | _from_external_id | node -> id |
|               | _to_external_id | node -> scan -> components -> vulns -> cve |
| asset_ipaddress | _from_external_id | node -> id |
|               | _to | node -> internalIpAddress OR node -> externalIpAddress |

The following table shows the mapping for container as an asset.

|  CAR vertex/edge  |   CAR field   |  Data source field  |
|  :------------:   |:-------------:| :--------------:|
| asset | name | pods -> liveInstances -> containerName |
|       | external ID | pods -> liveInstances -> id |
|       | image | pods -> liveInstances -> imageDigest |
| ipaddress | _key | pods -> liveInstances -> instanceId -> containerIps |
| vulnerability | name | image -> scan -> components -> vulns -> cve |
|               | external_id | image -> scan -> components -> vulns -> cve |
|               | description | image -> scan -> components -> vulns -> summary |
|               | base_score | image -> scan -> components -> vulns -> cvss |
|               | published_on | image -> scan -> components -> vulns -> publishedOn |
|               | updated_on | image -> scan -> components -> vulns -> lastModified |
| application | external_id | deployments -> id OR node ->scan -> components -> name OR image -> scan -> components -> name |
|             | name | deployments -> name OR node ->scan -> components -> name OR image -> scan -> components -> name |
| asset_vulnerability | _from_external_id | pods -> liveInstances -> id |
|               | _to_external_id | image -> scan -> components -> vulns -> cve |
| asset_application | _from_external_id | pods -> liveInstances -> id |
|               | _to_external_id | deployments -> id OR node ->scan -> components -> name OR image -> scan -> components -> name |
| application_vulnerability | _from_external_id | node ->scan -> components -> name OR image -> scan -> components -> name |
|               | _to_external_id | nodes -> scan -> components -> vulns -> cve OR image -> scan -> components -> vulns -> cve |

The following table shows the mapping for cluster as an asset.

|  CAR vertex/edge  |   CAR field   |  Data source field  |
|  :------------:   |:-------------:| :--------------:|
| asset | name | clusters -> name |
|       | external_id | clusters -> id |
| account | external_id | role -> name |
|         | name | role -> name |
| user | username | users -> id |
|      | employee_id | users -> authProviderId |
|      | external_id | users -> id |
| asset_account | _from_external_id | clusters -> id |
|               | _to_external_id | role -> name |
| user_account | _from_external_id | users -> id |
|               | _to_external_id | role -> name |

III. INSTALLATION:
-----------------------------------------------------------------
- Requirements.txt file attached.


IV. EXAMPLE USAGE (command line):
-----------------------------------------------------------------

```Usage: app.py [arguments]```

required arguments in command line:

```
positional arguments:
-host                       :RHACS API server name or IP
-token                      :RHACS API authentication token
-selfSignedCert             :Self Signed Certificate (starting with "-----BEGIN CERTIFICATE-----\n"
                              and ending with "\n-----END CERTIFICATE-----")
-sni                        :Host name
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
Update RHACS configuration details in 'rhacs_config.json`
### Setup Details
Please follow the mentioned steps,

I.	Cloning repository from GitHub

Link: `````https://github.com/IBM/cp4s-car-connectors.git`````

    - Use the PAT token as authentication password for cloning the same to the Linux filesystem using the “git clone” command or download the source code as a zip file.

II.	Setting PYTHONPATH permanently.

    For Linux,
    -  Open the file ~/.bashrc in your text editor – e.g. vi ~/.bashrc;
    -  Add the following line to the end: (change according to your working dorectory)
    export PYTHONPATH= /home/testadmin/cp4s-car-connectors/connectors/rhacs
    Save the file.
    -  Close your terminal application;
    -  Start your terminal application again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/cp4s-car-connectors/connectors/rhacs/.
    
    For Mac,
    - Open Terminal.app;
    Open the file ~/.bash_profile in your text editor – e.g. atom ~/.bash_profile;
    - Add the following line to the end:
    export PYTHONPATH="/home/testadmin/cp4s-car-connectors/connectors/rhacs/"
    Save the file.
    -	Close Terminal.app;
    -	Start Terminal.app again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/cp4s-car-connectors/connectors/rhacs/.


### Command To Run the script

Note: RHACS(StackRox) supports both ca and self-signed certificates. Below given script is based on self-signed. In case of trusted ca issued server certificate, it is not required to pass sni and self-signed parameter as they are optional.

1. goto the connector folder ` <cp4s-car-connectors/connectors/rhacs>`

2. To run the initial import which is the full dump of the data source assets, run this command:
   ` python app.py -host <RHACS hostname or IP> -token <'token'> -selfSignedCert <self signed certificate> -sni <Host name>  -url <"BASE_URL"> -api_key <"api_key"> -password <"password"> -source "<RHACS>"`

3. To run the incremental update, create a cronjob that runs every 4hours, the command to run is:
   ` python app.py -host <RHACS hostname or IP> -token <'token'> -selfSignedCert <self signed certificate> -sni <Host name> -url <"BASE_URL"> -api_key <"api_key"> -password <"password"> -source "<RHACS>"`

V. INITIAL IMPORT
-----------------------------------------------------------------
When we run the connector First time. It loads all the asset and their entities available from the source into CAR database.​
#####ClusterService: (Cluster information)
    "https://<server>/v1/clusters"
#####NodeService: (node information)
    "https://<server>/v1/nodes/{clusterId}"
#####PodService: (Pods information)
    "https://<server>/v1/pods"
#####ImageService: (Image information)
    "https://<server>/v1/images"
#####DeploymentService: (Deployment information)
    "https://<server>/v1/deployments"
#####RoleService: (Roles information)
    "https://<server>/v1/roles"
#####GroupService: (Group information)
    "https://<server>/v1/groups"
#####UserService: (User information)
    "https://<server>/v1/users"
#####VulnerabilityRequestService: (Vulnerability requests information)
    "https://<server>/v1/cve/requests"

VI. INCREMENTAL IMPORT
-----------------------------------------------------------------
- Incremental Imports are expected to be based on a time-range and RHACS doesn't have time range parameters for APIs. Hence, we are identifying the same with the help of the timestamps present in the response.
- Incremental imports deletes Asset and container based on the comparison with the latest list from data source.
- Since deffered vulnerabilities are approved for some time period and are listed again once that time period is over, those vulnerabilities will be preset whoever edges corresponding to those vulnerabilities are deleted.
