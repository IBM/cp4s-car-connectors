# Best practices when developing a new connector

### Analyzing target data source APIs 

The goal of CAR is to store data about the assets (computing machine) and the vulnerability and risks associated with those assets. Before starting development on a new connector, confirm that the data source APIs can provide information about assets and risks. Ideally the CAR connector should populate the asset, vulnerability, and user nodes along with their connective edges.

### Adhering to the import schema

Refer to the [CAR import schema](https://github.com/IBM/cp4s-car-schema/blob/master/doc/generated/importSchema_v2.json).
The connector's target data source fields should be normalized against the schema as much as possible. The schema may be extended if there is data that needs to be imported into CAR, but is not currently contained in the schema. See this [example](https://github.com/IBM/cp4s-car-connectors/blob/develop/connectors/reference_connector/app.py#L29) for extending the schema. 

### Normalizing the CAR connector configuration files with existing UDI connectors

Both UDI and CAR connectors use configuration files to control how data integrations are configured in IBM Cloud Pak for Security. When possible, configuration parameters should be normalized between connectors for the same data source. UDI connectors are all part of the open-source STIX-Shifter project. Look in the project's [modules folder](https://github.com/opencybersecurityalliance/stix-shifter/tree/develop/stix_shifter_modules) to see if your target data source has an existing UDI connector. If a UDI connector exists, use its `config.json` file ([see sample](https://github.com/opencybersecurityalliance/stix-shifter/blob/develop/stix_shifter_modules/qradar/configuration/config.json)) as a guide for naming the properties in the CAR connector's configuration file ([see sample](https://github.com/IBM/cp4s-car-connectors/tree/develop/connectors/reference_connector/configurations)). 

Make sure the test connection method is implemented for your connector ([see sample](https://github.com/IBM/cp4s-car-connectors/blob/develop/connectors/reference_connector/connector/server_access.py#L16)). This is how IBM Cloud Pak for Security determines if a connection to the data source is successful. 


