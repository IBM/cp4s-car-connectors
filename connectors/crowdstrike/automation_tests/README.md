# Automation Test

Automation Test For CrowdStrike Falcon CAR Connector
```
I.    SUMMARY
II.   CONFIGURATION
III.  COMMAND TO RUN THE SCRIPT
```
I. SUMMARY:
-----------------------------------------------------------------
It will test the entire CrowdStrike Falcon CAR connector process.
This automation test use mock apis values instead of CrowdStrike Falcon data source 
and push the values to CAR DB.


II. CONFIGURATION:
-----------------------------------------------------------------
- Update the config file -> automation_config.json
-   source : source name in CAR DB,
-   car_service_apikey_url : CAR DB url
-   api_key : CAR DB authentication key
-   api_password: CAR DB authentication password

III. COMMAND TO RUN THE SCRIPT:
-----------------------------------------------------------------

1. To run the automation script run this below command


   `crowdstrike> pytest .\automation_tests\automation_tests.py`
