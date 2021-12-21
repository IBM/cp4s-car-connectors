# AWS CAR connector

AWS Car Connector
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
AWS is a secure cloud services platform from Amazon. It provides different types of services such as Infrastructure
as a service(Iaas),Packaged software as a service(SaaS), Platform as a service (Paas). It provides various web services
like EC2, RDS, ECS, Beanstalk, S3, Lambda, DynamoDB, VPC etc. It has more features like compute, storage, and
databases–to emerging technologies, such as machine learning and artificial intelligence, data lakes and analytics,
and Internet of Things. This makes it faster, easier, and more cost effective to move your existing applications to
the cloud. Security Hub is a single place that aggregates, organizes, and prioritizes your security alerts, or
findings, from multiple AWS services, such as Amazon Guard Duty, Amazon Inspector, and Amazon Macie, as well as from
AWS Partner solutions. AWS Cloud Trail records the activity in  AWS account and store it as event. You can easily view
recent events in the CloudTrail console by going to Event history.

Site:   ```https://console.aws.amazon.com```
      
II. PREREQUISITES:
-----------------------------------------------------------------
Python == 3.6.x (greater than 3.6.x may work, less than probably will not; neither is tested)

III. INSTALLATION:
-----------------------------------------------------------------

`boto3`
`car-connector-framework`

- Requirements.txt file attached.


IV. EXAMPLE USAGE (command line):
-----------------------------------------------------------------

```Usage: app.py [arguments]```

required arguments in command line:

```
positional arguments:
-accountId                  :account ID of subscription(aws)
-clientID                   :client ID (aws)
-clientSecret               :client secret (aws)
-source                     :data source
-region                     :aws region(aws), e.g. us-east-1
-car-service-url            :CAR DB url
-car-service-key            :CAR api_key
-car-service-password       :CAR api_password

optional arguments:
-d                          :run code in debug mode
```

## Setup Details
Please follow the mentioned steps,

I.	Cloning repository from Azure-Devops. 
 
 Link: ````` https://IBMSecurityConnect@dev.azure.com/IBMSecurityConnect/ISC-CAR/_git/AWS-ISC-CAR`````

    - Use the PAT token as authentication password for cloning the same to the Linux filesystem using the “git clone”
      command or download the source code as a zip file.

II.	Setting PYTHONPATH permanently.

    For Linux,
    -  Open the file ~/.bashrc in your text editor – e.g. vi ~/.bashrc;
    -  Add the following line to the end: (change according to your working directory)
    export PYTHONPATH= /home/testadmin/AWS-ISC-CAR
    Save the file.
    -  Close your terminal application;
    -  Start your terminal application again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/AWS-ISC-CAR/.
    
    For Mac,
    - Open Terminal.app;
    Open the file ~/.bash_profile in your text editor – e.g. atom ~/.bash_profile;
    - Add the following line to the end:
    export PYTHONPATH="/home/testadmin/AWS-ISC-CAR/"
    Save the file.
    -	Close Terminal.app;
    -	Start Terminal.app again, to read in the new settings, and type this:
    echo $PYTHONPATH
    - It should show something like /home/testadmin/AWS-ISC-CAR/.


## Command To Run the script
To run the import which is either a full dump of the data source assets or incremental:
        `python3 app.py -accountId "<AWS-accountId>" -clientID "<AWS-clientID>" -clientSecret "<AWS-clientSecret>" -source "<source>" -car-service-key "<car-service-key>" -car-service-password "<car-service-password>" -car-service-url "<car-service-url>" -region "<region>" -d`

The framework is trying to make some intelligent choice for whether to run full vs incremental import. Normally, for performance reasons we would always prefer to run incremental import if one is possible.

##V. Initial Import

#####EC2_LIST_URL:
    "https://boto3.amazonaws.com/v1/documentation/api/1.9.185/reference/services/ec2.html#EC2.Paginator.DescribeInstances"

#####RDS_LIST_URL:
    "https://boto3.amazonaws.com/v1/documentation/api/1.9.185/reference/services/rds.html#RDS.Paginator.DescribeDBInstances"

#####ELASTIC_BEANSTALK_APPLICATION_LIST_URL:
    "https://boto3.amazonaws.com/v1/documentation/api/1.9.185/reference/services/elasticbeanstalk.html#ElasticBeanstalk.Client.describe_applications"

#####ELASTIC_BEANSTALK_APPLICATION_ENVIRONMENT_LIST_URL:
    "https://boto3.amazonaws.com/v1/documentation/api/1.9.185/reference/services/elasticbeanstalk.html#ElasticBeanstalk.Paginator.DescribeEnvironments"

#####ELASTIC_CONTAINER_SERVICES_LIST_URL:
    "https://boto3.amazonaws.com/v1/documentation/api/1.9.185/reference/services/ecs.html#ECS.Client.list_clusters"
    "https://boto3.amazonaws.com/v1/documentation/api/1.9.185/reference/services/ecs.html#ECS.Client.list_tasks"
    "https://boto3.amazonaws.com/v1/documentation/api/1.9.185/reference/services/ecs.html#ECS.Client.describe_tasks"
    "https://boto3.amazonaws.com/v1/documentation/api/1.9.185/reference/services/ecs.html#ECS.Client.describe_container_instances"

#####VULNERABILITY_FINDINGS_LIST_URL:
    "https://boto3.amazonaws.com/v1/documentation/api/1.9.185/reference/services/securityhub.html#SecurityHub.Paginator.GetFindings"

##VI. Incremental Update:

- Incremental Imports are expected to be based on a time-range and hence we utilize the Cloud trail logs in aws to detect various resource action.
- Incremental imports detects create, update and delete scenarios with the help of “Event names” in cloud trail logs.
- Vulnerability are fetched from AWS security Hub for the assets. For incremental runs, there is no event from the ‘CloudTrail’ logs which would differentiate the update scenarios. Hence, we are identifying the same with the help of the timestamps present in the response.
- Since Archived vulnerabilities can be Unarchived anytime within 90 days, if there is no update for 90 days those vulnerabilities will be removed from Security hub by AWS. So we considering this as delete scenario’s in Car side as well.
- Incremental scenarios for create, update and delete actions are identified for the AWS resources in the scope of this connector.
  (EC2 Instances, Relational Database Services - RDS, Elastic Bean Stalk - EBS, Elastic Container Services - ECS)

####CLOUDTRAIL_LOG:
    "https://boto3.amazonaws.com/v1/documentation/api/1.9.185/reference/services/cloudtrail.html#CloudTrail.Paginator.LookupEvents"
