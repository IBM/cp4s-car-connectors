## Tanium pre-req

Modules: Intereac, Asset, Deploy, Discover and Benchmark
Packages: Client Management, Core ADQuery Content, and API Gateway

API token: https://docs.tanium.com/platform_user/platform_user/console_api_tokens.html?Highlight=api+token&cloud=false
GraphQL qurery: https://developer.tanium.com/site/global/apis/graphql/spectaql/index.gsp#definition-Endpoint

## Connector

Install python dependencies
```
pip3 install -r requirements.txt
```

Running the connector:
```
python3 app.py -host <The url of the tanium data source> -access_token <Access token of the tanium data source> -car-service-key "<car-service-key>" -car-service-password "<car-service-password>" -car-service-url "<car-service-url>" -source tanium
```