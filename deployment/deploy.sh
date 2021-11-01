#!/bin/bash

validate_cmd () {
  if ! `command -v $1 &> /dev/null` ; then
      echo "Error: $1 could not be found"
      exit 1
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


CONNECTOR=$1
REGISTRY_IMAGE_PATH=$2
CP4S_VER_PREFIX=$3
NAMESPACE=$4

TIMESTAMP=`date '+%Y%m%d%H%M%S'`

# echo "CONNECTOR               $CONNECTOR"
# echo "REGISTRY_IMAGE_PATH     $REGISTRY_IMAGE_PATH"
# echo "NAMESPACE               $NAMESPACE"
# echo "TIMESTAMP               $TIMESTAMP"

validate_arg "$CONNECTOR" "first" "connector name" "E.g. 'azure'"
validate_arg "$REGISTRY_IMAGE_PATH" "second" "image url" "e.g.: docker.io/cp4s-connectors/isc-car-connector-azure:Dev_1.0.0.0 with format: <REGISTRY_DOMAIN>/<IMAGE_PATH>/isc-car-connector-<CONNECTOR_NAME>:<TAG>"
validate_arg "$CP4S_VER_PREFIX" "third" "connector version" "e.g.: 1.0.0.0"

echo "Checking Prerequisites ... "
validate_cmd kubectl
validate_cmd oc


echo "Deploying connector CR"

CR_FILENAME=car-${CONNECTOR}-NEW.yaml
BACKUP_FOLDER=backup/${TIMESTAMP}
mkdir -p $BACKUP_FOLDER
cd $BACKUP_FOLDER
kubectl get connector "car-${CONNECTOR}" -o yaml > "car-${CONNECTOR}.yaml"

cat > $CR_FILENAME << EOL
apiVersion: connector.isc.ibm.com/v1
kind: Connector
metadata:
  name: car-${CONNECTOR}
spec:
  type: "CAR"
  version: "${CP4S_VER_PREFIX}"
  creator: "IBM"
  image: "${REGISTRY_IMAGE_PATH}"
EOL

echo "CR is written to '${BACKUP_FOLDER}/${CR_FILENAME}', applying it"


cat > _restore.sh << EOL
cd "\$(dirname "\$0")"
kubectl delete connector car-${CONNECTOR}
kubectl apply -f car-${CONNECTOR}.yaml
EOL
chmod u+x ./_restore.sh

kubectl apply -f ${CR_FILENAME} --force

echo "Done!"
echo "No worries you can rollback it with: ./${BACKUP_FOLDER}/_restore.sh"