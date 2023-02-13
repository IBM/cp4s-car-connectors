# Developing a CAR connector

## Before you begin

Read up on the [best practices](best-practices.md) for developing a CAR connector.
## Copy the reference connector
Create a fork of the `cp4s-car-connectors` project and create a working branch off of `develop`. 

## Update your copy of the reference connector

The [`reference_connector`](https://github.com/IBM/cp4s-car-connectors/tree/develop/connectors/reference_connector) is located in the connectors sub folder. Copy the reference connector and rename it to reflect the target data source. The following directories and files are modified to create a new CAR connector:

### `server` directory
Delete the server folder. This is only used to provide dummy data to demo the connector locally. Since your new connector will use to a real data source, this folder is no longer needed.

### `app.py`

Update the arguments required to connect to the target data source in the `__init__` method. The example in the reference connector uses `server`, `username` and `password`.

`get_schema_extension` method is `app.py` has an example how to extend [core CAR schema](https://github.com/IBM/cp4s-car-schema/blob/master/doc/generated/importSchema_v2.json). If the connector **doesn't need to extend the schema `get_schema_extension` method should be deleted**.
If connector needs to extend the schema more information can be found in [schema-extension](./schema-extension.md) doc. 
 
### `connector/server_access.py`

This is where the data source APIs are implemented to fetch that data that will be pushed to the CAR service. 
- Update  the `__init__` function for api authentication to call the data source API.
- Update `get_collection` to get the list of asset data.
- Update `test_connection` to ping datasource to check if the datasource is reachable. Make sure that the method return 0 on successful connection, or [a corresponding error code](https://github.com/IBM/cp4s-car-connector-framework/blob/99554ac2cfa0732af090c46be9e356beb015934e/car_framework/util.py#L35) on failure (Example: `return ErrorCode.TRANSMISSION_AUTH_CREDENTIALS.value`). 
- Update `get_object` and `get_objects` to get a single or list of objects based on identifier.
- If data source has any save points, `get_model_state_id` can be updated  to get that save point and `get_model_state_delta` to gather information to get data between two save points.
- For any kind of caught exception raise [DatasourceFailure](https://github.com/IBM/cp4s-car-connector-framework/blob/99554ac2cfa0732af090c46be9e356beb015934e/car_framework/util.py#L92) with [a corresponding error code](https://github.com/IBM/cp4s-car-connector-framework/blob/99554ac2cfa0732af090c46be9e356beb015934e/car_framework/util.py#L35)

### `connector/data_handler.py`

Identify the asset data and their relationships you wish to import from your target data source. The data that can be imported into the CAR service is defined in the [CAR schema](https://github.com/IBM/cp4s-car-schema). There is also a UML detailing the edges and nodes of the [Asset Model](https://github.com/IBM/cp4s-car-schema/blob/master/doc/generated/assetModel.png).

- Edit the `endpoint_mapping` object to map data source endpoints to CAR fields defined in the [schema](https://github.com/IBM/cp4s-car-schema). For each element in this object, the key is the data source endpoint and the value is the corresponding CAR field. As an example, if a data source has an `ip_addresses` endpoint that is to be mapped to the CAR `ipaddress` field, you would need to add it to the `endpoint_mapping` object:

```python
endpoint_mapping = {'ip_addresses': 'ipaddress'}
```

- The reference connector includes several sample helper functions: `extract_id`, `find_by_id`, and `filter_out`. You may edit or delete these functions, or add new ones depending on the needs of the target data source.

- Each element in the `endpoint_mapping` object must have a corresponding `handle_*` function for creating an object to be ingested by the CAR service. You can use the  `copy_fields` function to quickly create such an object if the data source endpoint has the same name as the target CAR property. Edit, delete, and add `handle_*` functions as needed.


### `connector/full_import.py`

The `FullImport` class is responsible for the initial import of data into the CAR service.

- Update the `__init__` method to initialize the data handler. If the data handler does not pull any enum from the source, `None` can be sent as the parameter.
- If the data handler initializes `source`; the `create_source_report_object` method can be left as is.
- Update the `import_collection` method to add logic required by the data source to import a single collection.
- Update `get_new_model_state_id` to get a new save point from the data source server. If the data source does not support save points, the current time should be returned.
- The `import_vertices` method should be left unchanged.
- The `import_edges` method should be left unchanged.

### `connector/inc_import.py`

The `IncrementalImport` class is responsible for the periodic import of data into the CAR service after the initial full import.

- The `__init__`, `import_vertices`, `import_edges`, `create_source_report_object`, and `get_new_model_state_id` methods can remain the same as in `full_import.py` unless a special case is required for incremental import.
<!-- Is this method importing new data since the last import? -->
- Update the `get_data_for_delta` method with logic to gather data from last save point and new save point. 
- Update the `import_collection` method with logic that imports a single collection only for the data between two save points.
- Update the `delete_vertices` method with logic to delete any vertices from the CAR database that have been deleted on the data source since the last import.

## Error handling

The errors occuring in the connector code must be well handled.
Consider raising DatasourceFailure with [a corresponding error code](https://github.com/IBM/cp4s-car-connector-framework/blob/99554ac2cfa0732af090c46be9e356beb015934e/car_framework/util.py#L35) whenever you need to have try/raise blocks. 
Example: 

```python
try:
    ...
    header = {
        "Authorization": "Bearer {}".format(self.get_access_token())
    }
    response = self.call_api(self.AUTH_URL, 'GET', header)
    ...

except Exception as e:
    raise DatasourceFailure(e, ErrorCode.DATASOURCE_FAILURE_AUTH.value)
```

If an error is not handled, the framework will raise a [GENERAL_APPLICATION_FAILURE](https://github.com/IBM/cp4s-car-connector-framework/blob/99554ac2cfa0732af090c46be9e356beb015934e/car_framework/app.py#L106) (Unknown error) and print the error stack. 

## Configuration files

The configurations folder contains two files: `config.json` and `lang.json`. These files are used by the IBM Cloud Pak for Security connections UI to display the fields required to configure a connector.

### `configurations/config.json`

The configuration JSON file describes the parameters used by the CAR service and any parameters required to connect to the data source (such as for authentication). Two top level JSON objects need to be present in the file: `connection` and `configuration`. The child attributes of the `connection` object defines general information about the connector. The `configuration` object contains parameters used for data source authentication and any other parameters used by the source APIs. The type property on an attribute determines the field type that will be used to collect user input in the UI.

The following example contains the appropriate parameters for `config.json`:

```json
{
    "connection": {
        "type": {
            "type": "connectorType",
            "displayName": "<CONNECTOR_NAME>"
        }
    },
    "configuration": {
        "auth": {
            "type": "fields",
            "url": {
                "type": "text"
            },
            "username": {
                "type": "text"
            },
            "password": {
                "type": "password"
            }
        },
        "parameter":{
            "type": "fields",
        	"<required_parameter>": {
                "type": "text"
            },
            "<optional_parameter>": {
                "type": "text",
                "optional": true
            }
        }
    }
}
```

#### `connection`

- `type`: Defines the type and display name of the connector. The type should remain as `connectorType` and the displayName should be changed to reflect the name of the connector.

#### `configuration`

- `auth`: Defines any authentication parameters required by the data source APIs, username and password are shown in the example, but other fields may be used. Update this object as required by the data source.
- `parameter`: Defines any additional parameters needed by the data source APIs. Any parameter added to the object is required by default. For optional parameters, add the `"optional": true` attribute. Update the `parameter` object as needed. If no additional parameters are required, the object can be deleted from the config. 

### `configurations/lang.json`

The `lang.json` file describes how the fields for configuring the connector (as outlined in `config.json`) will be presented in the IBM Cloud Pak for Security UI. These include labels, descriptions, and field placeholder text. Just like the config JSON, two top level objects need to be present in the file: `connection` and `configuration`.

The following example contains the appropriate parameters for `lang.json`:

```json
{
    "configuration": {
        "auth": {
            "url": {
                "label": "URL",
                "description": "Data source URL"
            },
            "username": {
                "label": "Username",
                "description": "Username required for data source authentication"
            },
            "password": {
                "label": "Password",
                "description": "Password required for data source authentication"
            }
        },
        "parameter": {
            "<required_parameter>": {
                "label": "<label_for_parameter_field>",
                "placeholder": "<placeholder_text_for_parameter_field>",
                "description": "<description_of_parameter>"
            },
            "<optional_parameter>": {
                "label": "<label_for_parameter_field>",
                "placeholder": "<placeholder_text_for_parameter_field>",
                "description": "<description_of_parameter>"
            }
        }
    }
}
```

Only the `configuration` object needs to be updated to reflect the `auth` and `parameter` objects defined in `config.json`.

### `travis.sh`
Update `travis.sh` file, including the name of the new connector in a new line in the CONNECTORS list.

### `README.md`

Update `README.md` to include an overview of the target data source and any setup information. Remove reference to the server since the server folder should have been deleted.

### `travis.sh`

Update `travis.sh` to execute unit test every time there is an update.

## Testing your connector

Testing a CAR connector requires an IBM Cloud Pak for Security instance. See [IBM Documentation](https://www.ibm.com/docs/en/cloud-paks/cp-security/1.8?topic=security-installing-cloud-pak-180) for installation instructions.

Log into your IBM Cloud Pak for Security Homepage and navigate to the API Keys page from the left menu. If you have not already done so, generate a new API key and secret. 

Open a terminal and navigate to your CAR connector project. Run the `app.py` python script from the CLI. The `-car-service-key`, `-car-service-password` and `-source` parameters are required. Below is an example using url, username, and password, but the parameters used to connect to the target data source will depend on what has been defined in the `config.json` file's `auth` object.


```
python app.py -url "<DATA_SOURCE_URL>" -username "<DATA_SOURCE_USERNAME>" -password "<DATA_SOURCE_PASSWORD>" -car-service-key "<API_KEY>" -car-service-password "<API_SECRET>" -car-service-url "https://<CP4S_CLUSTER>/api/car/v2" -source "car-<DATA_SOURCE_NAME>"
```
