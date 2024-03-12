#!/bin/bash
shopt -s expand_aliases #Used to enable exapnd alias in non-interactive shells


TAG="Test"
CONNECTOR_VERSION="1.0.0.0"
REGISTRY=""
DEPLOY=""

validate_cmd () {
  if ! `command -v $1 &> /dev/null` ; then
      echo "Error: $1 could not be found"
      exit 1
  else
      echo "  found $1"
  fi
}

validate_cmd_alias () {
  if ! `command -v $1 &> /dev/null` ; then
        if ! `command -v $2 &> /dev/null` ; then
            echo "Error: $1 and $2 could not be found"
            exit 1
        else
            echo "  found $2"
            echo "creating docker as alias for podman"
            alias docker="podman"
        fi
  else
      echo "  found $1"
  fi
}

validate_arg () {
  if [[ $1 == "" ]] ; then
      echo "Error: $2 positional argument '$3' must be supplied. $4"
      exit 1
  fi
}

# Parse command arguments and options
POSITIONAL=()
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    -t) 
      TAG="$2"
      shift
      shift
      ;;
    -t=*) 
      TAG="${1#*=}"
      shift
      ;;
    -v) 
      CONNECTOR_VERSION="$2"
      shift
      shift
      ;;
    -v=*) 
      CONNECTOR_VERSION="${1#*=}"
      shift
      ;;
    -r) 
      REGISTRY="$2"
      shift
      shift
      ;;
    -r=*) 
      REGISTRY="${1#*=}"
      shift
      ;;
    -d) 
      DEPLOY=TRUE
      shift
      ;;
    -n) 
      NAMESPACE="$2"
      shift
      shift
      ;;
    -n=*) 
      NAMESPACE="${1#*=}"
      shift
      ;;
    *)    # unknown option
      ARGG=$1
      POSITIONAL+=("$ARGG") # save it in an array for later
      shift # past argument
      ;;
  esac
done

set -- "${POSITIONAL[@]}" # restore positional parameters


MODE=$1
CONNECTOR=$2
IMAGE="isc-car-connector-$CONNECTOR"

# echo "MODE                $MODE"
# echo "CONNECTOR           $CONNECTOR"
# echo "IMAGE               $IMAGE"
# echo "TAG                 $TAG"
# echo "CONNECTOR_VERSION   $CONNECTOR_VERSION"
# echo "REGISTRY            $REGISTRY"
# echo "NAMESPACE           $NAMESPACE"
# echo "DEPLOY              $DEPLOY"

validate_arg "$MODE" "first" "mode type" "'local' or 'remote'"
validate_arg "$CONNECTOR" "second" "connector name" "E.g. 'azure'"

echo "Checking Prerequisites ... "
validate_cmd openssl
validate_cmd python3
validate_cmd pip3
validate_cmd_alias docker podman

echo -n "Checking if it is possible to execute docker command... "
docker ps > /dev/null
if [ $? -eq 0 ]; then
    echo "Ok"
else
    echo "Fail"
    exit 1
fi


DEPLOYMENT_HOME=`pwd`
PROJECT_DIR="$(dirname "$DEPLOYMENT_HOME")"
BUILD_HOME="${PROJECT_DIR}/build"
CONNECTOR_BUILD_FOLDER="$BUILD_HOME/$CONNECTOR"
CONNECTOR_SOURCE_FOLDER="$PROJECT_DIR/connectors/$CONNECTOR"

pip3 install virtualenv
pip3 install venv-run

virtualenv -p python3 virtualenv

python -V
python3 -V
docker version

pip3 install 'cryptography==42.0.5'
pip3 install 'pyopenssl==24.1.0'


if [ ! -d "$BUILD_HOME" ]; then
    echo "mkdir $BUILD_HOME"
    mkdir $BUILD_HOME
fi

if [ -d "$CONNECTOR_SOURCE_FOLDER" ]; then
    echo "*****************************************"
    echo "Start building $IMAGE:$TAG image"

    if [ -d "$CONNECTOR_BUILD_FOLDER" ]; then
        rm -rf "$CONNECTOR_BUILD_FOLDER"
    fi

    echo "mkdir $CONNECTOR_BUILD_FOLDER"
    mkdir $CONNECTOR_BUILD_FOLDER
    
    # Copy connector folders and files
    cp -R "$CONNECTOR_SOURCE_FOLDER/connector" "$CONNECTOR_BUILD_FOLDER/"
    cp "$CONNECTOR_SOURCE_FOLDER/app.py" "$CONNECTOR_BUILD_FOLDER/"
    cp "$CONNECTOR_SOURCE_FOLDER/requirements.txt" "$CONNECTOR_BUILD_FOLDER/"

    mkdir "$CONNECTOR_BUILD_FOLDER/configurations"

    # Merge config files
    jq -s '{ connection:(.[0].connection + .[1].connection), configuration: (.[0].configuration + .[1].configuration)}' "$DEPLOYMENT_HOME/configurations/config.json" "$CONNECTOR_SOURCE_FOLDER/configurations/config.json" > "$CONNECTOR_BUILD_FOLDER/configurations/config.json"
    jq -s '{ connection:(.[0].connection + .[1].connection), configuration: (.[0].configuration + .[1].configuration)}' "$DEPLOYMENT_HOME/configurations/lang_en.json" "$CONNECTOR_SOURCE_FOLDER/configurations/lang_en.json" > "$CONNECTOR_BUILD_FOLDER/configurations/lang_en.json"


    # Update help link
    sed -i'.bak' "s/{CONNECTOR}/${CONNECTOR}/g" "$CONNECTOR_BUILD_FOLDER/configurations/config.json"
    rm -f "$CONNECTOR_BUILD_FOLDER/configurations/config.json.bak"

    # Build Docker file
    cp "$DEPLOYMENT_HOME/Dockerfile.part" "$CONNECTOR_BUILD_FOLDER/Dockerfile"
    sed -i'.bak' "s/{CONNECTOR}/${CONNECTOR}/g" "$CONNECTOR_BUILD_FOLDER/Dockerfile"
    sed -i'.bak' "s/{RELEASE}/${CONNECTOR_VERSION}/g" "$CONNECTOR_BUILD_FOLDER/Dockerfile"
    sed -i'.bak' "s/{TAG}/${TAG}/g" "$CONNECTOR_BUILD_FOLDER/Dockerfile"
    rm -f "$CONNECTOR_BUILD_FOLDER/Dockerfile.bak"

    if [ $MODE == "remote" ]; then
        validate_cmd kubectl
        validate_cmd oc

        # if REGISTRY is not supplied use cluster registery
        if [ "X$REGISTRY" == "X" ]; then
            echo "No remote registry supplied, pushing to cp4s cluster registry."
            echo 'Exposing internal registry... (https://docs.openshift.com/container-platform/4.4/registry/securing-exposing-registry.html)'
            oc patch configs.imageregistry.operator.openshift.io/cluster --patch '{"spec":{"defaultRoute":true}}' --type=merge
            echo -n "Looking for cluster registry url... "
            DOCKER_REGISTRY=$(oc get route default-route -n openshift-image-registry --template='{{ .spec.host }}')
            echo $DOCKER_REGISTRY
            if [ ! $DOCKER_REGISTRY ]; then
                echo "Error: You have to be logged in CP4S cluster before proceeding. See README.md"
                exit 1
            fi

            if [ "X$NAMESPACE" == "X" ]; then
                NAMESPACE=`kubectl config view --minify --output 'jsonpath={..namespace}' | awk '{print $1}'`
            fi
            echo "Using $NAMESPACE namespace"

            echo "Logging in into cluster registry..."
            docker login -u `oc whoami` -p `oc whoami -t` $DOCKER_REGISTRY

            REGISTRY_IMAGE_PATH="$DOCKER_REGISTRY/$NAMESPACE/$IMAGE:$TAG"
        else
            REGISTRY_IMAGE_PATH="$REGISTRY/$IMAGE:$TAG"
        fi

        echo "Building image: $REGISTRY_IMAGE_PATH"
        docker build -t $REGISTRY_IMAGE_PATH $CONNECTOR_BUILD_FOLDER --platform linux/amd64

        echo "Pushing image: $REGISTRY_IMAGE_PATH"
        docker push $REGISTRY_IMAGE_PATH
        
        # If in OCP cluster registery
        if [ "X$REGISTRY" == "X" ]; then
            docker logout
            REGISTRY_IMAGE_PATH="image-registry.openshift-image-registry.svc:5000/$NAMESPACE/$IMAGE:$TAG"
        fi

        if [ "X$DEPLOY" != "X" ]; then
            "Calling deploy: ./deploy.sh $CONNECTOR $REGISTRY_IMAGE_PATH $CONNECTOR_VERSION $NAMESPACE"
            ./deploy.sh $CONNECTOR $REGISTRY_IMAGE_PATH $CONNECTOR_VERSION $NAMESPACE
        fi
    else
        echo "Building local image: $IMAGE:$TAG"
        docker build -t $IMAGE:$TAG $CONNECTOR_BUILD_FOLDER --platform linux/amd64
    fi
    
    echo "*****************************************"

else
    echo "Error: No connector source folder found: $CONNECTOR_SOURCE_FOLDER"
    echo "Exitting."
    exit
fi
