# Automation Test

Automation Test For ProofPoint Car Connector
```
I.    SUMMARY
II.   CONFIGURATION
III.  COMMAND TO RUN THE SCRIPT
```
I. SUMMARY:
-----------------------------------------------------------------
It will test the entire proofpoint CAR connector process.
This automation test use mock apis values instead of proofpoint data source 
and push the values to CAR db.


II. CONFIGURATION:
-----------------------------------------------------------------
- Update the config file -> automation_config.json
-   source : source name in car db,
-    car_service_apikey_url : car db url
-   api_key : car db authentication key
-   api_password: car db authentication password

III. COMMAND TO RUN THE SCRIPT:
-----------------------------------------------------------------

1. To run the automation script run this below command

   `ProofPoint-ISC-CAR> pytest .\automation_tests\automation_tests.py`
