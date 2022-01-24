# CAR Connectors for IBM Cloud Pak for Security

This project allows for the development of Connected Assets and Risks (CAR) connectors for the IBM Cloud Pak for Security platform. See the [reference connector](connectors/reference_connector) for a sample. This should be used as a template for developing new connectors. 

## Developer Guide

See the [developer guide](guide-build-connectors.md) for building a new CAR connector.


## Running a CAR connector locally

1. Open a terminal
2. Optionally create/use virtual env:
    `python3.9 -m venv venv`
    `. ./venv/bin/activate`
3. CD into a connector folder you want to run: `cd ./cd connectors/<CONNECTOR_NAME>/` 
4. Install python dependancies: `pip install -r requirements.txt`
5. Run the command to start import. Each connector has a different set of options that you can find in README.md file of each connector:
    `python3 app.py -source "<source>" -car-service-key "<car-service-key>" -car-service-password "<car-service-password>" -car-service-url "<car-service-url>" -d .... OTHER_OPTIONS`