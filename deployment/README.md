# Build and deploy CAR connector images into IBM Cloud Pak for Security (CP4S)

The scripts contained here allow you to build an image of a new or existing connector, and deploy that image into your Kubernetes cluster on your CP4S environment. The are also options for deploying an existing image from a Docker registry and for building an image locally so that you may publish it to a registry of your choice. 

## Prerequisites

The following needs to be installed on your local machine: 
* Python 3
* Docker
* OpenShift CLI (`oc`)
* Kubernetes CLI (`kubectl`)
* OpenSSL (`openssl`)

## Installing a CAR connector into CP4S

1. Open a terminal
2. CD into `deployment` folder of this project: `cd ./deployment/` 
3. Log into your CP4S cluster: 

    `cloudctl login -a <ICP CLUSTER URL> -u <USERNAME> -p <PASSWORD> -n <NAMESPACE>`
4. Optionally, log in to custom registry for build scenario "B"

5. Run build and/or deployment scripts using the following arguments:

    ### Build
    ```
    ./build.sh <MODE*> <CONNECTOR_NAME*> [-t <IMAGE_TAG>] [-v <CONNECTOR_VERSION>] [-r <REMOTE_REGISTRY>] [-n <NAMESPACE>] [-d]
    ```
    
    #### Arguments: 

    | Argument | Required | Description | Example |
    |------|-----|-----|-----|
    | MODE | Required | Values: "local" - the docker image will be built but not pushed, or "remote": the image is pushed to remote registry 
    | CONNECTOR_NAME | Required | the name of the connector and the connector source folder.
    | `-t` MAGE_TAG | Optional | the container image tag, default "Test". |  | 
    | `-v` CONNECTOR_VERSION | Optional | the connector release version, default "1.0.0.0". |  | 
    | `-r` REMOTE_REGISTRY | Optional | a custom registry url (including repository path if necessary, excluding IMAGE:TAG). Used only in `MODE` being "remote".| `docker.io/cp4s-connectors`, `sec-isc-team-isc-icp-docker-local.artifactory.swg-devops.com` | 
    | `-n` NAMESPACE | Optional | the namespace of the CP4S. If not specified, the current namespace of the logged in cluster will be used. Used only in `MODE` being "remote". |  | 
    | DEPLOY FLAG `-d` | Optional | If added, the `deploy.sh` script will be executed at the end of the build, provided `MODE` being "remote". |  | 

    #### Build scenarios: 
    ##### A. Build the connector image and push to CP4S OpenShift cluster registry
    ```
    ./build.sh remote <CONNECTOR_NAME> [-t <IMAGE_TAG>] [-v <CONNECTOR_VERSION>] [-n <NAMESPACE>] [-d]
    ```
    (Ex: `./build.sh remote azure -d -n cp4s`)
    (Ex: `./build.sh remote azure -t Test -v="1.9.0.0"`)


    ##### B. Build the connector image and push to a custom remote registry <REMOTE_REGISTRY>
    ```
    ./build.sh remote <CONNECTOR_NAME> [-t <IMAGE_TAG>] [-v <CONNECTOR_VERSION>] [-r <REMOTE_REGISTRY>] [-n <NAMESPACE>] [-d]
    ```
    (Ex: `./build.sh aws remote -r docker.io/cp4s-connectors -t="Dev_0.1.2" -v "1.9.0.0" -d`)


    ##### C. Build the connector image locally without pushing to a registry and deploying to cluster
    ```
    ./build.sh local <CONNECTOR_NAME> [<IMAGE_TAG>] [<CONNECTOR_VERSION>]
    ```
    (Ex: `./build.sh local aws`)
    (Ex: `./build.sh local aws -t Test -v="1.9.0.0"`)


    ### Deploy
    ```
    ./deploy.sh <CONNECTOR_NAME*> <REGISTRY_IMAGE_PATH*> <CONNECTOR_VERSION*> [<NAMESPACE>]
    ```
    (Ex: `./deploy.sh aws "image-registry.openshift-image-registry.svc:5000/cp4s/isc-car-connector-atp:Test" 1.9.0.0 -n cp4s`)

    #### Arguments: 

    | Argument | Required | Description | Example |
    |------|-----|-----|-----|
    | CONNECTOR_NAME | Required | The name of the connector and the connector source folder. | |
    | REGISTRY_IMAGE_PATH | Required | Image full path (including registry domain, repository path and IMAGE:TAG) |  `sec-isc-team-isc-icp-docker-local.artifactory.swg-devops.com/cp4s/isc-car-connector-aws:1.8.0.0_1.2.0` |
    | CONNECTOR_VERSION | Required | The connector release version | "1.0.0.0" |
    | `-n` NAMESPACE | Optional | The namespace of the CP4S. If not specified, the current namespace of the logged in cluster will be used. | |


    