Build the docker container of the connector and push it to docker registry. The car connector should be in format `isc-car-connector-<connector name>`

### 1. Create this Secret in the CP4S cluster, naming it regcred:
```
kubectl create secret docker-registry regcred --docker-server=<your-registry-server> --docker-username=<your-name> --docker-password=<your-pword> --docker-email=<your-email>
```

where:\
`<your-registry-server>` is your Private Docker Registry domain name. (https://index.docker.io/v1/ for DockerHub)\
`<your-name>` is your Docker username.\
`<your-pword>` is your Docker password.\
`<your-email>` is your Docker email.

You have successfully set your Docker credentials in the cluster as a Secret called regcred.

### 2. Create the **isc-car-connector-test** secret
Create a secret for the authentication used to make connection between the car service, data source and the Connectors. SEC_ENV_VAR_# are an example of the environment variable for authentication for the connector.

```
kubectl create secret generic isc-car-connector-secret 
  --from-literal=SEC_ENV_VAR_1='<SEC_ENV_VAR_1>'
  --from-literal=SEC_ENV_VAR_2='<SEC_ENV_VAR_2>'
  --from-literal=SEC_ENV_VAR_3='<SEC_ENV_VAR_3>'
  --from-literal=SEC_ENV_VAR_4='<SEC_ENV_VAR_4>'
```
for example if connector needs access key(ACCESS_KEY), secret key(SECRET_KEY) to call data source and IBM apikey(IBM_ACCESS_KEY) and api password(IBM_PASSWORD_KEY) to call CAR service, the secret can be as follows:
```
kubectl create secret generic ibm-car-tenable-secret 
  --from-literal=ACCESS_KEY='<ACCESS_KEY>'
  --from-literal=SECRET_KEY='<SECRET_KEY>'
  --from-literal=IBM_ACCESS_KEY='<IBM_ACCESS_KEY>'
  --from-literal=IBM_PASSWORD_KEY='<IBM_PASSWORD_KEY>'
```

Verify the secret is created successfully:
```
    kubectl get secret isc-car-connector-secret -n <NAMESPACE>
```

### 3. Update the CronJob template

Create a cronjob yaml template called `isc-car-connector-test.yaml`.
The cronjob is configured to execute every 15 minutes by default.

```
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  name: isc-car-connector-test
  labels:
    name: testc
    type: CAR
  annotations:
    productID: 545bf62dce574f99af370899013a4a8a
    productName: Connect Asset and Risk
    productVersion: 1.4.0
    cloudpakName: IBM Cloud Pak for Security
    cloudpakId: 929bd9017afc410da9dda2dc67c33b75
    cloudpakVersion: 1.4.0
spec:
  schedule: "* * * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      template:
        metadata:
          labels:
            name: testc
        spec:
          restartPolicy: Never
          imagePullSecrets:
          - name: regcred
          initContainers:
          - name: concat-ca
            image: registry.access.redhat.com/ubi8/ubi-minimal
            command: 
            - sh
            - -c
            - 'cat /etc/pki/ca-trust/extracted/openssl/ca-bundle.trust.crt /etc/config/ca.crt > /etc/cache_ca/ca_roots.pem'
            volumeMounts:
              - mountPath: /etc/config
                name: secrets
                readOnly: true
              - mountPath: /etc/cache_ca
                name: cache-ca
          containers:
          - name: testc
            securityContext:
              privileged: false
              allowPrivilegeEscalation: false
              readOnlyRootFilesystem: false
              runAsNonRoot: true
              capabilities:
                drop:
                - ALL
            image: "sec-isc-team-isc-icp-docker-local.artifactory.swg-devops.com/isc-car-connector-test:Test_1"
            imagePullPolicy: Always
            env:
            - name: REQUESTS_CA_BUNDLE
              value: "/etc/cache_ca/ca_roots.pem"
            - name: SEC_ENV_VAR_1
              valueFrom:
                secretKeyRef:
                  name: isc-car-connector-secret
                  key: SEC_ENV_VAR_1
            - name: SEC_ENV_VAR_2
              valueFrom:
                secretKeyRef:
                  name: isc-car-connector-secret
                  key: SEC_ENV_VAR_2
            - name: IBM_CAR_API_URI
              value: "<CLUSTER_URL>/api/car/v2"
            - name: SEC_ENV_VAR_3
              valueFrom:
                secretKeyRef:
                  name: isc-car-connector-secret
                  key: SEC_ENV_VAR_3
            - name: SEC_ENV_VAR_4
              valueFrom:
                secretKeyRef:
                  name: isc-car-connector-secret
                  key: SEC_ENV_VAR_4
            volumeMounts:
              - mountPath: /etc/config
                name: secrets
                readOnly: true
              - mountPath: /etc/cache_ca
                name: cache-ca
          volumes:
          - name: secrets
            secret:
              defaultMode: 420
              secretName: cp4s-truststore
          - name: cache-ca
            emptyDir: {}
```

### 4. Deploy the CronJob <isc-car-connector-test.yaml>
```
    kubectl create -f isc-car-connector-test.yaml -n <NAMESPACE>
```
### 5. Validate CronJob and Pod created  successfully

Check CronJob
```
    kubectl get cronjob -lname=testc -n <NAMESPACE>
```
Check Pod
```
    kubectl get pod -lname=testc -n <NAMESPACE>
```
## Uninstall the CAR connector
Delete CronJob
```
kubectl delete cronjob isc-car-connector-test -n <NAMESPACE>
```
Delete secrets
```
kubectl delete secret isc-car-connector-secret
```
```
kubectl delete secret regcred
```
Delete Pod
```
kubectl delete pod -lname=testc -n <NAMESPACE> --force
```