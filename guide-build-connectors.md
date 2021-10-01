# Developing a CAR connector
## Copy the reference connector
The `cp4s-car-reference-connector` project should first be copied to your local development environment. This can be done by either cloning or downloading a ZIP archive of this project. 

## Update your copy of the reference connector

The following directories and files are modified to create a new CAR connector.

### `server` directory
Delete the server folder. This is only used to provide dummy data to demo the connector locally. Since your new connector will use to a real data source, this folder is no longer needed.

### `app.py`

Update the arguments required to connect to the target data source in the `__init__` method. The example in the reference connector uses `server`, `username` and `password`.
 
### `connector/serveraccess.py`

This is where the data source APIs are implemented to fetch that data that will be pushed to the CAR service. 
- Update  the `__init__` function for api authentication to call the data source API.
- Update `get_collection` to get the list of asset data.
- Update `get_object` and `get_objects` to get a single or list of objects based on identifier.
- If data source has any save points, `get_model_state_id` can be updated  to get that save point and `get_model_state_delta` to gather information to get data between two save points.

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

## Configuration files

The configurations folder contains two files: `config.json` and `lang.json`. These files are used by the CP4S connections UI to display the fields required to configure a connector.

### `configurations/config.json`

The configuration JSON file describes the parameters used by the CAR service and any parameters required to connect to the data source (such as for authentication). Two top level JSON objects need to be present in the file: `connection` and `configuration`. The child attributes of the `connection` object defines general information about the connector and the scheduling options for importing data into the CAR service. The `configuration` object contains parameters used for data source authentication and any other parameters used by the source APIs. The type property on an attribute determines the field type that will be used to collect user input in the UI. The regex property enforces input rules on the information entered in the associated text field.

The following example contains the appropriate parameters for `config.json`:

```json
{
    "connection": {
        "type": {
            "default": "<connector_name>",
            "extentionType": "car"
        },
        "name": {
            "min": 5,
            "type": "text",
            "regex": "^[A-Za-z0-9 _-]*$",
            "default": null
        },
        "description": {
            "type": "text",
            "regex": "^[A-Za-z0-9 _-]*$",
            "default": null
        },
        "frequency": {
            "default": "15m",
            "type": "dropdown",
            "options": ["5m", "10m", "15m", "30m", "1h","2h","4h","6h","12h", "daily"]
        },
        "time": {
            "default": "09:00",
            "type": "time"
        },
        "help": {
            "default": "<Data_Source_help_link>",
            "type": "link"
        },
        "image": {
            "type": "text",
            "hidden": true,
            "default": "{image_link}"
        }
    },
    "configuration": {
        "auth": {
            "username": {
                "type": "text"
            },
            "password": {
                "type": "password"
            }
        },
        "parameter":{
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

- `type`: Defines the type of the connector. Update the value of the `default` attribute to match the name you have chosen for the connector; this should be written in snake_case (ex. `"default": "security_product"`). The `extentionType` attribute should remain as is for CAR connectors.
- `name`: Defines the name of the connector. This object should be left as is.
- `description`: Defines the description of the connector. This object should be left as is.
- `frequency`: Defines the frequency options used to determine how often CAR's data import job is run. This object should be left as is.
- `time`: Defines in UTC time when the initial import job is run. Change this to your desired time.
- `help`: Defines a help URL where a user can get more information about a connector. This would typically be an IBM Knowledge Center page outlining the connector configuration options.
- `image`: Used by the CAR config service, the `image_link` is automatically populated by the Kubernetes custom resource. This object should be left as is.

#### `configuration`

- `auth`: Defines any authentication parameters required by the data source APIs, username and password are shown in the example, but other fields may be used. Update this object as required by the data source.
- `parameter`: Defines any additional parameters needed by the data source APIs. Any parameter added to the object is required by default. For optional parameters, add the `"optional": true` attribute. Update the `parameter` object as needed. If no additional parameters are required, the object can be deleted from the config. 

### `configurations/lang.json`

The language JSON file describes how the fields for configuring the connector (as outlined in `config.json`) will be presented in the CP4S UI. These include labels, descriptions, and field placeholder text. Just like the config JSON, two top level objects need to be present in the file: `connection` and `configuration`.

The following example contains the appropriate parameters for `lang.json`:

```json
{
    "connection": {
        "name": {
            "label": "Connector name",
            "description": "Assign a name to uniquely identify the data source connection"
        },
        "description": {
            "label": "Connector Description",
            "description": "Write a description to indicate the purpose of the data source connection"
        },
        "frequency": {
            "label": {
                "5m"    : "5 minutes",
                "10m"   : "10 minutes",
                "15m"   : "15 minutes",
                "30m"   : "30 minutes",
                "1h"    : "1 hour",
                "2h"    : "2 hour",
                "5h"    : "4 hour",
                "10h"   : "6 hour",
                "12h"   : "12 hour",
                "daily" : "Daily"
            },
            "description": "Set how frequently the connectors will pull data from the data source"
        },
        "time": {
            "label": "Time",
            "description": "Set the time to run connector to pull data from data source"
        },
        "help": {
            "label": "Help",
            "description": "More details on the data source setting can be found in the specified link"
        }
    },
    "configuration": {
        "auth": {
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


### `Dockerfile`

Update  the `LABEL` in the `Dockerfile` 

```
LABEL name="<connector_name>-isc-car-connector" \
	vendor="IBM" \
	summary="<connector_summary>" \
	release="1.5" \
	version="<cp4s_version>" \
	description="<connector_description>"
```
- The `connector_name` should be in snake_case and followed by `-isc-car-connector`.
- The `cp4s_version` should be the latest version of Cloud Pak for Security (ex. `1.6.0.0`).
- The `connector_summary` and `connector_description` can be the same, or a longer description may be added.

### `README.md`

Update `README.md` to include an overview of the target data source and any setup information.  

## Testing your connector

Download the [CAR import project](https://github.ibm.com/CAR/UDA-Import) and follow the [instructions](https://github.ibm.com/CAR/UDA-Import/tree/develop/functional-test) for running the CAR service locally. After running your new connector's full import, verify that data is successfully imported in CAR by calling the endpoints listed in the [CAR documentation](https://github.ibm.com/CAR/UDA-Import/blob/develop/README.md).


