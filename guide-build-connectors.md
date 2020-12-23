1. Identify asset data and the relationships between those identifiers.  CAR-connector-schema.xls file can be helpful to figure out the mapping between CAR data model and source data structure.
2. Get local instance of CAR running. [CAR-service](https://github.ibm.com/CAR/UDA-Import) repo needs to be cloned. It has all the tools required to run local instance of CAR with detailed steps use this repo in [README](https://github.ibm.com/CAR/UDA-Import/blob/develop/functional-test/readme.md) file. Note: Easier way to run CAR is in working.
3. Get the reference CAR connector running. car-reference-connector has a server (dummy data-source) can started by following steps listed in README of that repository. Once the server is running, we can execute the reference connector with command as mentioned in the README file. While running the reference connector make sure the variables car-service-url car-service-key and car-service-password is for the CAR env setup in Step 2.
5. Verify that data is successfully imported in CAR by calling any endpoints as mentioned in CAR documentation.
6. Update the reference connector to call desired data source.



# Update reference connector
1. Delete the dummy server
2. `app.py`
    - Update  the arguments  required to connect to data source in `__init__`
    - Add logic for source id in `source` function
3. `serveraccess.py`
    - Update  the `__init__` function  for api authentication  to call data-source  API.
    - Update `get_collection` to get list of asset  data.
    - Update `get_object` and `get_objects` to get a single  or list of objects based  on identifier.
    - If data source  has any save points `get_model_state_id` can be updated  to get that save point  and `get_model_state_delta` to gather information  to get data between two save points.
4. `data_handler.py`
    - Update the `endpoint_mapping` variable for mapping collection name at data source and collection identified by CAR.
    - Add, remove and update function as required by data source data structure.
    - Update `handle_*` function for collection as per data structure. `copy_fields` function can be used for properties with same name in data source and CAR.
5. `full_import.py`
    - Update `__init__` with initializing the data handler. If data handler do not require to pull any enum from source `None` can be sent as parameter.
    - If data handler initializes source, report and source_report; `create_source_report_object` function can be as it is.
    - Update `import_collection` to add logic required to import a single collection.
    - `import_vertices` can be left as it is all the collection to be imported is lister in `endpoint_mapping` in data handler
    - Update `get_new_model_state_id` to get new save point from server, if not it can just return current time.
    - `import_edges` can be be left as it is if data handler manages the add edge logic.
6. `inc_import.py`
    - `__init__`, `import_vertices`, `import_edges`, `create_source_report_object`, `get_new_model_state_id` can be same as `full_import.py` if nothing distinct is changing for incremental import.
    - Update `get_data_for_delta` to add logic to gather information to get data from last save point and new save point. 
    - Update `import_collection` to add logic required to import a single collection only for the data between two save points.
    - Update `delete_vertices` logic to delete any vertices that are deleted in data source.
7. Update `Dockerfile` and in `configurations` folder update `config.json` and `lang.json` as per required parameter. 

