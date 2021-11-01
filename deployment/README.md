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
2. CD into `deployment` folder: `cd ./deployment/` 
3. Optional. For an IBM validated connector, copy the `cert.key` and `cert.pem` files that you received from IBM into the current `deployment` directory.
4. Log into your CP4S cluster: 

    `cloudctl login -a <ICP CLUSTER URL> -u <USERNAME> -p <PASSWORD> -n <NAMESPACE>`

5. Run the deployment script based on one of the following scenarios:

    ### A. Build the connector image and then deploy into your Kubernetes cluster
    ```
    ./deploy.sh remote <CONNECTOR_NAME> [<IMAGE_TAG>] [<CP4S_VERSION>]
    ```
    (Ex: `./deploy.sh remote azure`)
    (Ex: `./deploy.sh remote azure Test "1.9.0.0"`)


    ### B. Build the connector image locally without deployment
    ```
    ./deploy.sh local <CONNECTOR_NAME> [<IMAGE_TAG>] [<CP4S_VERSION>]
    ```
    (Ex: `./deploy.sh local aws`)
    (Ex: `./deploy.sh local aws Test "1.9.0.0"`)


    ### Arguments: 
    MODE: Required, values - "local" or "remote"
    CONNECTOR_NAME - Required, the name of the connector and the folder
    IMAGE_TAG - Optional, the container image tag, default "Test"
    CP4S_VERSION  Optional, CP4S release version, default "1.1.0.0"